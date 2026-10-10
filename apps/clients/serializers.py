from rest_framework import serializers
from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True, allow_null=True)

    class Meta:
        model = Client
        fields = [
            "id", "user", "username", "client_number", "first_name", "last_name",
            "national_id", "email", "phone", "address", "date_of_birth",
            "is_active", "created_at",
        ]
        read_only_fields = ["created_at", "username"]

    def validate_national_id(self, value):
        # Plusieurs clients sans pièce d'identité : on stocke NULL (et non "") pour respecter l'unicité.
        return value or None


class ClientSelfSerializer(ClientSerializer):
    """Un client ne peut modifier que son e-mail, son téléphone et son adresse."""

    class Meta(ClientSerializer.Meta):
        read_only_fields = [
            "id", "user", "username", "client_number", "first_name", "last_name",
            "national_id", "date_of_birth", "is_active", "created_at",
        ]
