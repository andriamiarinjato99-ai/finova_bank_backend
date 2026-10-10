from decimal import Decimal
from django.db import models
from apps.clients.models import Client
from apps.agencies.models import Agency

class BankAccount(models.Model):
    class AccountType(models.TextChoices):
        SAVINGS = "SAVINGS", "Épargne"
        CURRENT = "CURRENT", "Courant"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Actif"
        BLOCKED = "BLOCKED", "Bloqué"
        CLOSED = "CLOSED", "Fermé"

    account_number = models.CharField(max_length=34, unique=True)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="accounts")
    agency = models.ForeignKey(Agency, on_delete=models.PROTECT, related_name="accounts")
    account_type = models.CharField(max_length=20, choices=AccountType.choices, default=AccountType.CURRENT)
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="MGA")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    opened_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.account_number
