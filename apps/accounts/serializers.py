from rest_framework import serializers
from .models import BankAccount

ALLOWED_CURRENCIES = {"MGA", "EUR", "USD"}


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = "__all__"
        read_only_fields = ["balance", "opened_at"]
        # Renseignés automatiquement à l'ouverture d'un compte (voir BankAccountViewSet.perform_create).
        extra_kwargs = {
            "account_number": {"required": False},
            "client": {"required": False},
            "agency": {"required": False},
        }

    def validate_currency(self, value):
        value = value.upper()
        if value not in ALLOWED_CURRENCIES:
            raise serializers.ValidationError("Devise non prise en charge (MGA, EUR ou USD).")
        return value

    def validate(self, attrs):
        if attrs.get("status") == BankAccount.Status.CLOSED and self.instance and self.instance.balance != 0:
            raise serializers.ValidationError("Un compte ne peut être fermé que si son solde est nul.")
        return attrs
