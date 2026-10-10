from django.conf import settings
from django.db import models
from apps.agencies.models import Agency

class Employee(models.Model):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrateur"
        MANAGER = "MANAGER", "Manager"
        CASHIER = "CASHIER", "Caissier"
        AUDITOR = "AUDITOR", "Auditeur"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employee_profile")
    employee_number = models.CharField(max_length=30, unique=True)
    agency = models.ForeignKey(Agency, on_delete=models.PROTECT, related_name="employees")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CASHIER)
    phone = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.employee_number} - {self.user.get_full_name()}"
