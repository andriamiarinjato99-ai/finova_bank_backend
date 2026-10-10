from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.accounts.models import BankAccount
from apps.accounts.utils import generate_account_number
from apps.agencies.utils import get_default_agency
from apps.audit.models import AuditLog
from .models import Client
from .utils import generate_client_number

User = get_user_model()

EMAIL_TAKEN = "Un compte existe déjà avec cette adresse e-mail."


class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=80)
    last_name = serializers.CharField(max_length=80)
    email = serializers.EmailField(max_length=150)
    phone = serializers.CharField(max_length=30)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(username__iexact=email).exists() or Client.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(EMAIL_TAKEN)
        return email

    def validate(self, attrs):
        candidate = User(
            username=attrs["email"],
            email=attrs["email"],
            first_name=attrs["first_name"],
            last_name=attrs["last_name"],
        )
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs

    def create(self, validated_data):
        email = validated_data["email"]
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=validated_data["password"],
                    first_name=validated_data["first_name"],
                    last_name=validated_data["last_name"],
                )
                client = Client.objects.create(
                    user=user,
                    client_number=generate_client_number(),
                    first_name=validated_data["first_name"],
                    last_name=validated_data["last_name"],
                    email=email,
                    phone=validated_data["phone"],
                )
                # Un premier compte courant est ouvert automatiquement.
                BankAccount.objects.create(
                    account_number=generate_account_number(),
                    client=client,
                    agency=get_default_agency(),
                    account_type=BankAccount.AccountType.CURRENT,
                    currency="MGA",
                )
                AuditLog.objects.create(
                    user=user,
                    action=AuditLog.Action.CREATE,
                    entity="Client",
                    entity_id=str(client.pk),
                    description=f"Inscription du client {client.client_number}",
                )
        except IntegrityError:
            raise serializers.ValidationError({"email": [EMAIL_TAKEN]})
        return user


class RegisterView(APIView):
    """Inscription publique : crée l'utilisateur, sa fiche client et un premier compte."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    @extend_schema(request=RegisterSerializer, responses={201: None})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"detail": "Compte créé.", "username": user.username}, status=status.HTTP_201_CREATED)
