from decimal import Decimal
from rest_framework import serializers
from .models import Transaction

MIN_AMOUNT = Decimal("0.01")


class TransactionSerializer(serializers.ModelSerializer):
    source_account_number = serializers.SerializerMethodField()
    destination_account_number = serializers.SerializerMethodField()
    # Sens de l'opération pour l'utilisateur connecté : IN (reçu), OUT (envoyé), INTERNAL (entre ses comptes).
    direction = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = "__all__"
        read_only_fields = ["reference", "status", "performed_by", "created_at"]

    def get_source_account_number(self, obj):
        return obj.source_account.account_number if obj.source_account_id else None

    def get_destination_account_number(self, obj):
        return obj.destination_account.account_number if obj.destination_account_id else None

    def get_direction(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None
        from_me = bool(obj.source_account_id and obj.source_account.client.user_id == user.id)
        to_me = bool(obj.destination_account_id and obj.destination_account.client.user_id == user.id)
        if from_me and to_me:
            return "INTERNAL"
        if to_me:
            return "IN"
        if from_me:
            return "OUT"
        return None


class DepositSerializer(serializers.Serializer):
    account_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=MIN_AMOUNT)
    description = serializers.CharField(required=False, allow_blank=True, max_length=255)


class WithdrawSerializer(serializers.Serializer):
    account_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=MIN_AMOUNT)
    description = serializers.CharField(required=False, allow_blank=True, max_length=255)


class TransferSerializer(serializers.Serializer):
    source_account_id = serializers.IntegerField()
    destination_account_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=MIN_AMOUNT)
    description = serializers.CharField(required=False, allow_blank=True, max_length=255)
