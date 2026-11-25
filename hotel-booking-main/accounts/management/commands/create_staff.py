r"""Create the hotel's staff accounts.

Usage (from the hotel-booking-main folder):
    venv314\Scripts\python.exe manage.py create_staff            # create missing accounts
    venv314\Scripts\python.exe manage.py create_staff --reset    # also give existing ones new passwords

Each new account gets a random password that is printed ONCE in the terminal.
Passwords are never written in this file: Django only stores a one-way hash,
so copy them somewhere safe (or reset later with `manage.py changepassword`).
"""
import secrets
import string

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

# The staff team: (username, first name, last name, job title, email)
STAFF = [
    ("grace.uwase", "Grace", "Uwase", "Front Desk Manager", "grace.uwase@easybooking.rw"),
    ("olivier.mugisha", "Olivier", "Mugisha", "Reservations Officer", "olivier.mugisha@easybooking.rw"),
    ("diane.ingabire", "Diane", "Ingabire", "Operations Supervisor", "diane.ingabire@easybooking.rw"),
]

GROUP_NAME = "Hotel Staff"

# What staff may do in Django Admin, as (app_label, model, [actions]).
# They manage inventory and bookings, and can look at (not edit) guests' data.
# No "delete" on bookings: cancelling (status) keeps the booking history.
GROUP_PERMISSIONS = [
    ("hotels", "hotel", ["view", "add", "change"]),
    ("hotels", "room", ["view", "add", "change"]),
    ("hotels", "amenity", ["view", "add", "change"]),
    ("bookings", "booking", ["view", "add", "change"]),
    ("auth", "user", ["view"]),
    ("recommendations", "userpreference", ["view"]),
    ("recommendations", "airecommendationquery", ["view"]),
]


def make_password(length=14):
    """Random password with upper, lower, digit and symbol characters (cryptographically secure)."""
    pools = [string.ascii_uppercase, string.ascii_lowercase, string.digits, "@#$%&*!?"]
    chars = [secrets.choice(pool) for pool in pools]                  # one of each kind
    everything = "".join(pools)
    chars += [secrets.choice(everything) for _ in range(length - len(chars))]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


class Command(BaseCommand):
    help = "Create EasyBooking staff accounts (is_staff, not superuser) in the 'Hotel Staff' group."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Give accounts that already exist a new random password.")

    @transaction.atomic                                               # all accounts or none
    def handle(self, *args, **options):
        group = self.setup_group()
        User = get_user_model()
        rows = []
        for username, first, last, title, email in STAFF:
            user, created = User.objects.get_or_create(username=username, defaults={
                "first_name": first, "last_name": last, "email": email})
            user.is_staff = True          # may sign in to /admin/ and /accounts/staff/
            user.is_superuser = False     # limited to the group's permissions
            user.is_active = True
            password = None
            if created or options["reset"]:
                password = make_password()
                user.set_password(password)                           # stored as a hash
            user.save()
            user.groups.add(group)
            rows.append((username, title, password or "(unchanged - use --reset)"))

        self.stdout.write(self.style.SUCCESS(f"\nStaff accounts (group '{GROUP_NAME}'):\n"))
        for username, title, password in rows:
            self.stdout.write(f"  {username:<18} {title:<24} {password}")
        self.stdout.write("\nSign in at /admin/ or /accounts/staff/. Save these passwords now - "
                          "they cannot be shown again.\n")

    def setup_group(self):
        group, _ = Group.objects.get_or_create(name=GROUP_NAME)
        perms = []
        for app_label, model, actions in GROUP_PERMISSIONS:
            for action in actions:
                perms.append(Permission.objects.get(
                    content_type__app_label=app_label, codename=f"{action}_{model}"))
        group.permissions.set(perms)                                  # exactly this list
        return group
