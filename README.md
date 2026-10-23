# To-Do List

A shared to-do list for a small team: a Flask server keeps everyone's tasks in one SQLite database,
an admin desktop app (Tkinter) hands out and tracks the work, and a user app lets each person see
and finish their own tasks. A simpler single-window version for one person is included too.

![The admin app showing tasks for three users, colored by priority](screenshots/admin-tasks.png)

## What it does

**Multi-user version** (`multi/`)

- **Server** (`multi/Server`): a REST API built with Flask and Flask-RESTx, with interactive API
  docs at the server's root address.
  - Login hands out a token that expires after 7 days. Passwords are hashed with bcrypt and must
    be at least 8 characters with upper and lower case, a digit and a symbol.
  - Rate limiting on every endpoint (Flask-Limiter).
  - Tasks and users live in SQLite through SQLAlchemy.
  - On first start it creates an `admin` account.
- **Admin app** (`multi/Admin`): a Tkinter desktop app.
  - See every task, or filter by user. Rows are colored by priority (urgent, normal, low).
  - Add tasks with a calendar date picker and a due time, edit them, mark them done, delete them,
    and view completed tasks in their own window.
  - Manage users: create them, reset passwords, make or remove admins, delete them.
  - Refreshes the task list every 60 seconds so changes from other people show up.
- **User app** (`multi/User`): a Tkinter desktop app for regular users.
  - Log in and see only the tasks assigned to you, with due date, time and priority, colored the
    same way as in the admin app.
  - Open a task to read its details, and mark it completed when it's done.

![The user app showing one person's open tasks, colored by priority](screenshots/user-tasks.png)

**Standalone version** (`standalone/`)

![The standalone app with incomplete and completed tasks side by side](screenshots/standalone.png)

- One window, no server: tasks are saved to a `tasks.json` file next to the app.
- Incomplete and completed tasks side by side, colored by priority.
- Due dates and times from a calendar picker, a details field for each task, and web links in the
  details open in the browser when clicked.

## How to run it

You need Python 3.12. It was built and tested on Windows, where the standard Python installer
includes Tkinter.

**Server**

```
cd multi\Server
pip install -r requirements.txt
copy config.example.ini config.ini
python run.py
```

Edit `config.ini` before you use it for real: set `SECRET_KEY` to a long random string. The
server listens on port 5000. The first start creates an `admin` user with the password `Admin1!`,
or with the password in the `DEFAULT_ADMIN_PASSWORD` environment variable if you set one, so set
that variable before the first start of a real install.

**Admin app** (with the server running)

```
cd multi\Admin
pip install -r requirements.txt
python main.py
```

The server address is in `multi/Admin/config.py` (`http://127.0.0.1:5000/api/v1` by default).

**User app** (with the server running, and a user the admin has created)

```
cd multi\User
pip install -r requirements.txt
python main.py
```

The server address is in `multi/User/config.py`.

**Standalone app**

```
cd standalone
pip install -r requirements.txt
python "My To-Do List.py"
```

The `Server`, `Admin` and `User` folders each have a `Start ... .bat` file that runs the app with
a double-click. The `.spec` files build a single `.exe` with PyInstaller, for example
`pyinstaller main.spec` in `multi\Admin`.

## How it was built

I built this in December 2024 with ChatGPT's help. The standalone app came first. Over the next
week it grew into the multi-user version: first a single-file server on plain SQLite, then the
Flask-RESTx server here, split into modules, with token logins and rate limiting. I left the
user app unfinished at the time and finished it in 2026 with Claude Code.

## License

MIT. See [LICENSE](LICENSE).
