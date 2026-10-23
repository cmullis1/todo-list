import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import Calendar
import json
import os
from datetime import datetime
import re
import webbrowser

class ToDoApp:
    def __init__(self, master):
        self.master = master
        master.title("My To-Do List")
        master.geometry("825x500")
        master.resizable(True, True)

        self.edit_window = None
        self.date_time_win = None

        style = ttk.Style(master)
        style.theme_use("clam")
        # Remove bold from the entire Treeview, set a normal font
        style.configure("Treeview", rowheight=30, font=("Segoe UI", 12))

        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TEntry", font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TCombobox", font=("Segoe UI", 10))

        self.tasks = []
        self.task_var = tk.StringVar()

        main_frame = ttk.Frame(master, padding=10)
        main_frame.pack(fill='both', expand=True)

        input_frame = ttk.Frame(main_frame)
        input_frame.pack(pady=5, fill='x')

        self.task_entry = ttk.Entry(input_frame, textvariable=self.task_var)
        self.task_entry.pack(side=tk.LEFT, padx=(0, 5), fill='x', expand=True)

        self.add_button = ttk.Button(input_frame, text="Add", command=self.add_task)
        self.add_button.pack(side=tk.LEFT, padx=(5,0))

        lists_frame = ttk.Frame(main_frame)
        lists_frame.pack(pady=10, fill='both', expand=True)

        # Incomplete tasks frame
        incomplete_frame = ttk.Frame(lists_frame)
        incomplete_frame.pack(side=tk.LEFT, padx=10, fill='both', expand=True)

        ttk.Label(incomplete_frame, text="Incomplete Tasks").pack(anchor='w', pady=(0,5))

        self.incomplete_tree = ttk.Treeview(incomplete_frame, columns=("task","due"), show="headings", selectmode="extended")
        self.incomplete_tree.heading("task", text="Task")
        self.incomplete_tree.heading("due", text="Due")
        self.incomplete_tree.column("task", width=275)
        self.incomplete_tree.column("due", width=200)
        self.incomplete_tree.pack(side=tk.LEFT, fill='both', expand=True)
        self.incomplete_tree.tag_configure("urgent", background="lightcoral")
        self.incomplete_tree.tag_configure("normal", background="lightgreen")
        self.incomplete_tree.tag_configure("low", background="lightblue")

        incomplete_scrollbar = ttk.Scrollbar(incomplete_frame, orient=tk.VERTICAL, command=self.incomplete_tree.yview)
        self.incomplete_tree.configure(yscrollcommand=incomplete_scrollbar.set)
        incomplete_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Completed tasks frame
        completed_frame = ttk.Frame(lists_frame)
        completed_frame.pack(side=tk.LEFT, padx=10, fill='both', expand=True)

        ttk.Label(completed_frame, text="Completed Tasks").pack(anchor='w', pady=(0,5))

        self.completed_tree = ttk.Treeview(completed_frame, columns=("task",), show="headings", selectmode="extended")
        self.completed_tree.heading("task", text="Task")
        self.completed_tree.column("task", width=250)
        self.completed_tree.pack(side=tk.LEFT, fill='both', expand=True)
        self.completed_tree.tag_configure("urgent", background="lightcoral")
        self.completed_tree.tag_configure("normal", background="lightgreen")
        self.completed_tree.tag_configure("low", background="lightblue")

        completed_scrollbar = ttk.Scrollbar(completed_frame, orient=tk.VERTICAL, command=self.completed_tree.yview)
        self.completed_tree.configure(yscrollcommand=completed_scrollbar.set)
        completed_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind events
        self.incomplete_tree.bind("<<TreeviewSelect>>", self.on_task_select)
        self.completed_tree.bind("<<TreeviewSelect>>", self.on_task_select)

        self.incomplete_tree.bind("<Double-Button-1>", self.show_task_info)
        self.completed_tree.bind("<Double-Button-1>", self.show_task_info)

        self.incomplete_tree.bind("<Button-3>", self.show_context_menu)
        self.completed_tree.bind("<Button-3>", self.show_context_menu)

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(pady=5, fill='x')

        self.edit_button = ttk.Button(control_frame, text="Edit", command=self.edit_selected_task)
        self.edit_button.pack(side=tk.LEFT, padx=5)

        self.toggle_button = ttk.Button(control_frame, text="Mark Completed", command=self.toggle_task_completion)
        self.toggle_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = ttk.Button(control_frame, text="Delete Selected", command=self.delete_selected_tasks)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        self.master.bind('<Return>', self.add_task)

        self.context_menu = tk.Menu(self.master, tearoff=0)

        self.load_tasks_from_file()

        if self.incomplete_tree.selection():
            self.toggle_button.config(text="Mark Completed")
        elif self.completed_tree.selection():
            self.toggle_button.config(text="Mark Incomplete")
        else:
            self.toggle_button.config(text="Mark Completed")

    def show_context_menu(self, event):
        widget = event.widget
        if widget not in [self.incomplete_tree, self.completed_tree]:
            return

        iid = widget.identify_row(event.y)
        if iid:
            widget.selection_set(iid)
        else:
            return

        self.context_menu.delete(0, tk.END)

        if widget == self.incomplete_tree:
            self.context_menu.add_command(label="Edit", command=lambda: self.edit_task_fake_event(widget))
            self.context_menu.add_command(label="Mark Completed", command=self.toggle_task_completion)
            self.context_menu.add_command(label="Delete", command=self.delete_selected_tasks)
        else:
            self.context_menu.add_command(label="Edit", command=lambda: self.edit_task_fake_event(widget))
            self.context_menu.add_command(label="Mark Incomplete", command=self.toggle_task_completion)
            self.context_menu.add_command(label="Delete", command=self.delete_selected_tasks)

        self.context_menu.tk_popup(event.x_root, event.y_root)

    def edit_task_fake_event(self, widget):
        class FakeEvent:
            pass
        fe = FakeEvent()
        fe.widget = widget
        self.edit_task(fe)

    def edit_selected_task(self):
        class FakeEvent:
            pass
        fe = FakeEvent()
        if self.incomplete_tree.selection():
            fe.widget = self.incomplete_tree
        elif self.completed_tree.selection():
            fe.widget = self.completed_tree
        else:
            messagebox.showinfo("Info", "No tasks selected.")
            return
        self.edit_task(fe)

    def add_task(self, event=None):
        task_text = self.task_var.get().strip()
        if task_text:
            task_data = {
                "text": task_text,
                "due_date": "",
                "time": "",
                "priority": "Normal",
                "completed": False,
                "details": ""
            }
            self.tasks.append(task_data)
            self.update_treeviews()
            self.task_var.set("")
            self.save_tasks_to_file()
        else:
            messagebox.showwarning("Warning", "Please enter a task.")

    def delete_selected_tasks(self):
        incomplete_sel = self.incomplete_tree.selection()
        completed_sel = self.completed_tree.selection()

        if not incomplete_sel and not completed_sel:
            messagebox.showinfo("Info", "No tasks selected.")
            return

        if incomplete_sel:
            for item_id in reversed(incomplete_sel):
                index = self.incomplete_indices[item_id]
                del self.tasks[index]

        if completed_sel:
            for item_id in reversed(completed_sel):
                index = self.completed_indices[item_id]
                del self.tasks[index]

        self.update_treeviews()
        self.save_tasks_to_file()

    def toggle_task_completion(self):
        incomplete_sel = self.incomplete_tree.selection()
        completed_sel = self.completed_tree.selection()

        if incomplete_sel:
            for item_id in incomplete_sel:
                index = self.incomplete_indices[item_id]
                self.tasks[index]["completed"] = True

        if completed_sel:
            for item_id in completed_sel:
                index = self.completed_indices[item_id]
                self.tasks[index]["completed"] = False

        self.update_treeviews()
        self.save_tasks_to_file()

    def on_task_select(self, event):
        # Enforce single selection type behavior
        if event.widget == self.incomplete_tree:
            self.completed_tree.selection_remove(self.completed_tree.get_children())
        else:
            self.incomplete_tree.selection_remove(self.incomplete_tree.get_children())

        if self.incomplete_tree.selection():
            self.toggle_button.config(text="Mark Completed")
        elif self.completed_tree.selection():
            self.toggle_button.config(text="Mark Incomplete")
        else:
            self.toggle_button.config(text="Mark Completed")

    def show_task_info(self, event):
        widget = event.widget
        y = event.y
        item_id = widget.identify_row(y)
        if not item_id:
            return

        if widget == self.incomplete_tree:
            actual_index = self.incomplete_indices[item_id]
        else:
            actual_index = self.completed_indices[item_id]

        task = self.tasks[actual_index]

        info_window = tk.Toplevel(self.master)
        info_window.title(task["text"])
        info_window.geometry("400x300")
        info_window.resizable(True, True)

        main_frame = ttk.Frame(info_window, padding=10)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(0, weight=1)

        due_date_str = task["due_date"] if task["due_date"] else "Not Set"
        time_str = task["time"] if task["time"] else "Not Set"

        ttk.Label(main_frame, text=f"Due Date: {due_date_str}").pack(anchor='w', pady=5)
        ttk.Label(main_frame, text=f"Time: {time_str}").pack(anchor='w', pady=5)

        ttk.Label(main_frame, text="Details:").pack(anchor='w', pady=(10,5))

        details_text = tk.Text(main_frame, wrap='word')
        details_text.pack(fill='both', expand=True)
        details_text.insert(tk.END, task["details"])
        details_text.config(state=tk.DISABLED)

        self.make_hyperlinks_clickable(details_text)

    def make_hyperlinks_clickable(self, text_widget):
        pattern = r"(http[s]?://\S+)"
        text_content = text_widget.get("1.0", tk.END)

        for match in re.finditer(pattern, text_content):
            start_index = f"1.0+{match.start()}c"
            end_index = f"1.0+{match.end()}c"
            text_widget.tag_add("hyperlink", start_index, end_index)

        text_widget.tag_configure("hyperlink", foreground="blue", underline=True)
        text_widget.tag_bind("hyperlink", "<Button-1>", self.open_link)

    def open_link(self, event):
        text_widget = event.widget
        index = text_widget.index(f"@{event.x},{event.y}")

        hyperlink_ranges = text_widget.tag_ranges("hyperlink")
        for start, end in zip(hyperlink_ranges[0::2], hyperlink_ranges[1::2]):
            if text_widget.compare(start, "<=", index) and text_widget.compare(end, ">=", index):
                url = text_widget.get(start, end)
                webbrowser.open(url)
                break

    def edit_task(self, event):
        if self.edit_window is not None and tk.Toplevel.winfo_exists(self.edit_window):
            self.edit_window.lift()
            return

        widget = event.widget
        if widget == self.incomplete_tree:
            selection = self.incomplete_tree.selection()
            if not selection:
                return
            selected_id = selection[0]
            actual_index = self.incomplete_indices[selected_id]
        else:
            selection = self.completed_tree.selection()
            if not selection:
                return
            selected_id = selection[0]
            actual_index = self.completed_indices[selected_id]

        task = self.tasks[actual_index]

        self.edit_window = tk.Toplevel(self.master)
        self.edit_window.title("Edit Task Details")
        self.edit_window.geometry("350x450")
        self.edit_window.minsize(350, 450)
        self.edit_window.resizable(True, True)

        def on_close():
            if self.edit_window is not None and tk.Toplevel.winfo_exists(self.edit_window):
                self.edit_window.destroy()
            self.edit_window = None

        self.edit_window.protocol("WM_DELETE_WINDOW", on_close)

        style = ttk.Style(self.edit_window)
        style.theme_use("clam")

        edit_main_frame = ttk.Frame(self.edit_window, padding=10)
        edit_main_frame.pack(fill='both', expand=True)
        edit_main_frame.columnconfigure(0, weight=1)

        # Edit Task Name
        selected_text = task["text"]
        ttk.Label(edit_main_frame, text="Task Name:").grid(row=0, column=0, sticky='w', pady=5)
        name_var = tk.StringVar(value=selected_text)
        name_entry = ttk.Entry(edit_main_frame, textvariable=name_var)
        name_entry.grid(row=1, column=0, sticky='ew', pady=5)

        selected_date = task["due_date"]
        selected_time = task["time"]
        selected_priority = task["priority"]
        selected_details = task["details"]

        due_time_frame = ttk.Frame(edit_main_frame)
        due_time_frame.grid(row=2, column=0, sticky='ew', pady=5)

        due_date_label = ttk.Label(due_time_frame, text=f"Due Date: {selected_date if selected_date else 'Not Set'}")
        due_date_label.pack(anchor='w')

        time_label = ttk.Label(due_time_frame, text=f"Time: {selected_time if selected_time else 'Not Set'}")
        time_label.pack(anchor='w')

        def dt_on_close():
            if self.date_time_win is not None and tk.Toplevel.winfo_exists(self.date_time_win):
                self.date_time_win.destroy()
            self.date_time_win = None

        def open_date_time_window():
            if self.date_time_win is not None and tk.Toplevel.winfo_exists(self.date_time_win):
                self.date_time_win.lift()
                return

            self.date_time_win = tk.Toplevel(self.edit_window)
            self.date_time_win.title("Set Due Date and Time")
            self.date_time_win.geometry("350x450")
            self.date_time_win.resizable(True, True)

            self.date_time_win.protocol("WM_DELETE_WINDOW", dt_on_close)

            dt_main_frame = ttk.Frame(self.date_time_win, padding=10)
            dt_main_frame.pack(fill='both', expand=True)

            ttk.Label(dt_main_frame, text="Select Due Date:").pack(pady=5, anchor='w')
            now = datetime.now()
            cal = Calendar(dt_main_frame, selectmode="day", year=now.year, month=now.month, day=now.day)
            cal.pack(pady=5, fill='x')

            if selected_date:
                try:
                    mm, dd, yyyy = selected_date.split('/')
                    cal.selection_set(f"{yyyy}-{int(mm):02d}-{int(dd):02d}")
                except:
                    pass

            hour_val, minute_val, ampm_val = "01", "00", "AM"
            if selected_time and ("AM" in selected_time or "PM" in selected_time):
                parts = selected_time.split()
                if len(parts) == 2:
                    time_part, ampm_part = parts
                    if ":" in time_part:
                        h, m = time_part.split(':')
                        hour_val, minute_val = h, m
                    ampm_val = ampm_part

            time_frame = ttk.Frame(dt_main_frame)
            time_frame.pack(pady=10, fill='x')

            ttk.Label(time_frame, text="Hour:").pack(side=tk.LEFT, padx=2)
            hour_var = tk.StringVar(value=hour_val)
            hour_options = [f"{h:02d}" for h in range(1, 13)]
            hour_dropdown = ttk.Combobox(time_frame, textvariable=hour_var, values=hour_options, state="readonly", width=3)
            hour_dropdown.pack(side=tk.LEFT, padx=2)

            ttk.Label(time_frame, text="Min:").pack(side=tk.LEFT, padx=2)
            minute_var = tk.StringVar(value=minute_val)
            minute_options = ["00", "30"]
            minute_dropdown = ttk.Combobox(time_frame, textvariable=minute_var, values=minute_options, state="readonly", width=3)
            minute_dropdown.pack(side=tk.LEFT, padx=2)

            ttk.Label(time_frame, text="AM/PM:").pack(side=tk.LEFT, padx=2)
            ampm_var = tk.StringVar(value=ampm_val)
            ampm_dropdown = ttk.Combobox(time_frame, textvariable=ampm_var, values=["AM", "PM"], state="readonly", width=3)
            ampm_dropdown.pack(side=tk.LEFT, padx=2)

            def save_date_time():
                nonlocal selected_date, selected_time
                selected_date = cal.get_date()  # MM/DD/YYYY
                chosen_hour = hour_var.get()
                chosen_minute = minute_var.get()
                chosen_ampm = ampm_var.get()
                selected_time = f"{chosen_hour}:{chosen_minute} {chosen_ampm}"
                due_date_label.config(text=f"Due Date: {selected_date}")
                time_label.config(text=f"Time: {selected_time}")
                dt_on_close()

            ttk.Button(dt_main_frame, text="Save", command=save_date_time).pack(pady=10)

        dt_button = ttk.Button(edit_main_frame, text="Set Due Date/Time", command=open_date_time_window)
        dt_button.grid(row=3, column=0, sticky='ew', pady=5)

        ttk.Label(edit_main_frame, text="Priority:").grid(row=4, column=0, sticky='w', pady=5)
        priority_var = tk.StringVar(value=selected_priority)
        priority_dropdown = ttk.Combobox(edit_main_frame, textvariable=priority_var, values=["Urgent", "Normal", "Low"], state="readonly")
        priority_dropdown.grid(row=5, column=0, sticky='ew', pady=5)

        ttk.Label(edit_main_frame, text="Details:").grid(row=6, column=0, sticky='w')
        details_frame = ttk.Frame(edit_main_frame)
        details_frame.grid(row=7, column=0, pady=5, sticky='nsew')
        edit_main_frame.rowconfigure(7, weight=1)

        details_text = tk.Text(details_frame, wrap='word')
        details_text.pack(pady=5, fill='both', expand=True)
        details_text.insert(tk.END, selected_details)

        button_frame = ttk.Frame(edit_main_frame)
        button_frame.grid(row=8, column=0, pady=10, sticky='ew')
        button_frame.columnconfigure(0, weight=1)

        def save_details():
            task["text"] = name_var.get().strip()
            task["due_date"] = selected_date
            task["time"] = selected_time
            task["priority"] = priority_var.get()
            task["details"] = details_text.get("1.0", tk.END).strip()
            self.update_treeviews()
            self.save_tasks_to_file()
            on_close()

        save_button = ttk.Button(button_frame, text="Save Changes", command=save_details)
        save_button.pack(side='right', padx=5)

    def update_treeviews(self):
        # Clear both treeviews
        for item in self.incomplete_tree.get_children():
            self.incomplete_tree.delete(item)
        for item in self.completed_tree.get_children():
            self.completed_tree.delete(item)

        self.incomplete_indices = {}
        self.completed_indices = {}

        priority_map = {"Urgent":0, "Normal":1, "Low":2}

        def parse_date_time(due_date, time_str):
            if not due_date:
                return (9999, 12, 31, 23, 59)
            try:
                mm, dd, yyyy = due_date.split('/')
                year = int(yyyy)
                month = int(mm)
                day = int(dd)
            except:
                return (9999, 12, 31, 23, 59)

            if not time_str:
                hour=23; minute=59
            else:
                parts = time_str.split()
                if len(parts) == 2:
                    hhmm, ampm = parts
                    if ":" in hhmm:
                        h, m = hhmm.split(':')
                        hour = int(h)
                        minute = int(m)
                        if ampm.upper() == "PM" and hour != 12:
                            hour += 12
                        if ampm.upper() == "AM" and hour == 12:
                            hour = 0
                    else:
                        hour=23;minute=59
                else:
                    hour=23;minute=59
            return (year, month, day, hour, minute)

        incomplete_tasks = [t for t in self.tasks if not t["completed"]]
        completed_tasks = [t for t in self.tasks if t["completed"]]

        incomplete_tasks.sort(key=lambda t: (priority_map.get(t["priority"],1),
                                             parse_date_time(t["due_date"], t["time"])))

        for task in incomplete_tasks:
            main_text = task["text"]
            parts = main_text.split(" | ", 1)
            parts[0] = parts[0].upper()
            main_text = " | ".join(parts)

            due_text = ""
            if task["due_date"]:
                due_text = f"Due: {task['due_date']}"
                if task["time"]:
                    due_text += f" {task['time']}"

            item_id = self.incomplete_tree.insert("", "end", values=(main_text, due_text))
            priority_tag = "urgent" if task["priority"] == "Urgent" else \
                           "normal" if task["priority"] == "Normal" else "low"
            self.incomplete_tree.item(item_id, tags=(priority_tag,))
            self.incomplete_indices[item_id] = self.tasks.index(task)

        for task in completed_tasks:
            main_text = task["text"]
            parts = main_text.split(" | ", 1)
            parts[0] = parts[0].upper()
            main_text = " | ".join(parts)

            item_id = self.completed_tree.insert("", "end", values=(f"[X] {main_text}",))
            priority_tag = "urgent" if task["priority"] == "Urgent" else \
                           "normal" if task["priority"] == "Normal" else "low"
            self.completed_tree.item(item_id, tags=(priority_tag,))
            self.completed_indices[item_id] = self.tasks.index(task)

    def save_tasks_to_file(self):
        with open("tasks.json", "w") as f:
            json.dump(self.tasks, f, indent=4)

    def load_tasks_from_file(self):
        if os.path.exists("tasks.json"):
            with open("tasks.json", "r") as f:
                try:
                    self.tasks = json.load(f)
                    self.update_treeviews()
                except json.JSONDecodeError:
                    self.tasks = []

if __name__ == "__main__":
    root = tk.Tk()
    app = ToDoApp(root)
    root.mainloop()
