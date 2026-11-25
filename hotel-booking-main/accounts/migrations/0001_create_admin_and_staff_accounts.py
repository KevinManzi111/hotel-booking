"""Data migration: create EasyBooking's admin and staff accounts automatically.

Runs once on every database when `python manage.py migrate` is run (local SQLite
or the Supabase database used by Vercel), so the accounts are always there.

People sign in with their email address: the username IS the email.

Security: this repository is public, so the plain passwords are NOT written here.
Only Django's one-way PBKDF2 hashes are stored; Django checks a typed password
against them at login. To change a password later, use the admin or
`python manage.py changepassword <email>`.
"""
from django.db import migrations

# (email/username, first name, last name, role, password hash)
ACCOUNTS = [
    ("paul@gmail.com", "Paul", "", "admin",
     "pbkdf2_sha256$600000$o84R2SJ4aYzNXtmLDqA9xN$e7OlqO+a8tWGtsXR+LH86JpSHNYCQi5KfwOkfUjCvf0="),
    ("bruno@gmail.com", "Bruno", "", "admin",
     "pbkdf2_sha256$600000$18Hz4b2Oa1lZ9VSzFyQ1c7$54NneNsMTAPlAcA7Bd6PQzJOMK7F3DAKmV0atewT7UU="),
    ("boris@gmail.com", "Boris", "", "staff",
     "pbkdf2_sha256$600000$9OOyjxjFY076zxrzS7VYFZ$9Z0tRzkoD0rB2Z2oGjuRv2JVsfCmNhPXEPoqTXWcrAc="),
    ("eric@gmail.com", "Eric", "", "staff",
     "pbkdf2_sha256$600000$DMs6AmLVOm2cRZbHIjSLEm$08YAY9zn6O/ROjs91ASBCchTj9gq3r3yks4816SOhBw="),
]

STAFF_GROUP = "Hotel Staff"

# What the staff role may do in Django Admin (same list as the create_staff command).
# Admins (superusers) automatically have every permission and need no group.
STAFF_PERMISSIONS = [
    ("hotels", "hotel", ["view", "add", "change"]),
    ("hotels", "room", ["view", "add", "change"]),
    ("hotels", "amenity", ["view", "add", "change"]),
    ("bookings", "booking", ["view", "add", "change"]),
    ("auth", "user", ["view"]),
    ("recommendations", "userpreference", ["view"]),
    ("recommendations", "airecommendationquery", ["view"]),
]


def ensure_permissions_exist(apps):
    # Django normally creates permission rows AFTER all migrations finish.
    # On a brand-new database they would not exist yet, so create them now.
    from django.contrib.auth.management import create_permissions
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None


def create_accounts(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    # 1. The "Hotel Staff" group and its permissions
    ensure_permissions_exist(apps)
    group, _ = Group.objects.get_or_create(name=STAFF_GROUP)
    for app_label, model, actions in STAFF_PERMISSIONS:
        for action in actions:
            perm = Permission.objects.filter(content_type__app_label=app_label,
                                             codename=f"{action}_{model}").first()
            if perm:
                group.permissions.add(perm)

    # 2. The accounts themselves (updated if they somehow already exist)
    for email, first, last, role, password_hash in ACCOUNTS:
        user, _ = User.objects.get_or_create(username=email)
        user.email = email
        user.first_name, user.last_name = first, last
        user.password = password_hash          # already hashed - do NOT use set_password()
        user.is_active = True
        user.is_staff = True                   # both roles may open /admin/ and /accounts/staff/
        user.is_superuser = role == "admin"    # admins: full access; staff: group permissions
        user.save()
        if role == "staff":
            user.groups.add(group)


def remove_accounts(apps, schema_editor):
    # Undo (python manage.py migrate accounts zero): delete these four accounts
    User = apps.get_model("auth", "User")
    User.objects.filter(username__in=[row[0] for row in ACCOUNTS]).delete()


class Migration(migrations.Migration):
    # Run after the tables (and models whose permissions we assign) exist
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("hotels", "0005_rehome_foreign_rooms_to_rwanda"),
        ("bookings", "0003_alter_booking_guests"),
        ("recommendations", "0006_alter_userpreference_preferred_city"),
    ]

    operations = [migrations.RunPython(create_accounts, remove_accounts)]
