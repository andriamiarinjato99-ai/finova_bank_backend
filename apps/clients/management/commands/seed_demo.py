from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from apps.accounts.models import BankAccount
from apps.agencies.utils import get_default_agency
from apps.clients.models import Client
from apps.employees.models import Employee


class Command(BaseCommand):
    help = "Crée un jeu de données de démonstration (un administrateur et deux clients)."

    def handle(self, *args, **kwargs):
        agency = get_default_agency()

        # --- Administrateur (personnel) ---
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@bank.local", "first_name": "Admin", "last_name": "Bank"},
        )
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password("Admin123!")
        admin.save()
        Employee.objects.update_or_create(
            user=admin,
            defaults={"employee_number": "EMP001", "agency": agency, "role": Employee.Role.ADMIN},
        )

        # --- Deux clients de démonstration (pour tester un virement de l'un vers l'autre) ---
        demo_users = [
            ("jean@finova.mg", "Jean", "Rakoto", "CL000001", "0340000001", "MG000000000000000001", Decimal("500000.00")),
            ("hery@finova.mg", "Hery", "Rasoa", "CL000002", "0340000002", "MG000000000000000002", Decimal("250000.00")),
        ]
        for email, first, last, number, phone, account_number, balance in demo_users:
            user, _ = User.objects.get_or_create(
                username=email,
                defaults={"email": email, "first_name": first, "last_name": last},
            )
            user.set_password("Demo12345!")
            user.save()
            client, _ = Client.objects.get_or_create(
                client_number=number,
                defaults={
                    "user": user, "first_name": first, "last_name": last,
                    "email": email, "phone": phone,
                },
            )
            if client.user_id != user.id:
                client.user = user
                client.save(update_fields=["user"])
            BankAccount.objects.get_or_create(
                account_number=account_number,
                defaults={
                    "client": client, "agency": agency, "account_type": BankAccount.AccountType.CURRENT,
                    "currency": "MGA", "balance": balance,
                },
            )

        self.stdout.write(self.style.SUCCESS("Données de démonstration créées."))
        self.stdout.write("Administration : admin / Admin123!")
        self.stdout.write("Client 1 : jean@finova.mg / Demo12345!  (compte MG000000000000000001)")
        self.stdout.write("Client 2 : hery@finova.mg / Demo12345!  (compte MG000000000000000002)")
