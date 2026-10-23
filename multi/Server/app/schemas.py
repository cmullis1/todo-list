# app/schemas.py

from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=20))
    password = fields.Str(required=False, allow_none=True)
    is_admin = fields.Bool(required=False)

class TaskSchema(Schema):
    task_name = fields.Str(required=True, validate=validate.Length(min=1))
    assigned_to = fields.Str(required=True, validate=validate.Length(min=3, max=20))
    completed = fields.Bool(required=False, missing=False)
    due_date = fields.Str(required=False, allow_none=True)
    due_time = fields.Str(required=False, allow_none=True)
    priority = fields.Str(required=False, validate=validate.OneOf(["Urgent", "Normal", "Low"]), missing="Normal")
    details = fields.Str(required=False, allow_none=True)
    task_id = fields.Int(required=False)
