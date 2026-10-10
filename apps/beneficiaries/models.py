from django.db import models
from apps.clients.models import Client

class Beneficiary(models.Model):
    owner = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="beneficiaries")
    name = models.CharField(max_length=120)
    account_number = models.CharField(max_length=34)
    bank_name = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.account_number}"
