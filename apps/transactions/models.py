from django.conf import settings
from django.db import models
from apps.accounts.models import BankAccount

class Transaction(models.Model):
    class Type(models.TextChoices):
        DEPOSIT = "DEPOSIT", "Dépôt"
        WITHDRAW = "WITHDRAW", "Retrait"
        TRANSFER = "TRANSFER", "Virement"

    class Status(models.TextChoices):
        COMPLETED = "COMPLETED", "Terminé"
        FAILED = "FAILED", "Échec"

    reference = models.CharField(max_length=40, unique=True)
    transaction_type = models.CharField(max_length=20, choices=Type.choices)
    source_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, null=True, blank=True, related_name="outgoing_transactions")
    destination_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, null=True, blank=True, related_name="incoming_transactions")
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=3, default="MGA")
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.COMPLETED)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reference} - {self.amount} {self.currency}"
