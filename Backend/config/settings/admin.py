from config.env import env

# Email addresses that should receive error notifications
ADMINS = [
    ("Admin", env("ADMIN_EMAIL1")),
    ("Admin 2", env("ADMIN_EMAIL2")),
]

# Email address that error messages come from
SERVER_EMAIL = env("EMAIL_HOST_USER")
