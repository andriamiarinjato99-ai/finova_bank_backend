from rest_framework import serializers
from apps.accounts.models import BankAccount
from .models import Beneficiary


class BeneficiarySerializer(serializers.ModelSerializer):
    # Identifiant du compte Finova correspondant au numéro saisi (null si le compte n'existe pas chez nous).
    account_id = serializers.SerializerMethodField()

    class Meta:
        model = Beneficiary
        fields = "__all__"
        read_only_fields = ["owner", "created_at"]

    def get_account_id(self, obj):
        return BankAccount.objects.filter(account_number=obj.account_number).values_list("id", flat=True).first()

    def validate_account_number(self, value):
        value = "".join(value.split()).upper()
        if not value:
            raise serializers.ValidationError("Le numéro de compte est obligatoire.")
        return value
