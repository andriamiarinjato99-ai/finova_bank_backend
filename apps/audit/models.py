from django.conf import settings
from django.db import models

class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "CREATE", "Création"
        UPDATE = "UPDATE", "Modification"
        DELETE = "DELETE", "Suppression"
        DEPOSIT = "DEPOSIT", "Dépôt"
        WITHDRAW = "WITHDRAW", "Retrait"
        TRANSFER = "TRANSFER", "Virement"
        LOGIN = "LOGIN", "Connexion"
        OTHER = "OTHER", "Autre"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=Action.choices)
    entity = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
