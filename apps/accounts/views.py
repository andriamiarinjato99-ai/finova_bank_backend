from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from apps.agencies.utils import get_default_agency
from .models import BankAccount
from .serializers import BankAccountSerializer
from .utils import generate_account_number

MAX_ACCOUNTS_PER_CLIENT = 5


class BankAccountViewSet(viewsets.ModelViewSet):
    """
    Le personnel gère tous les comptes. Un client voit ses propres comptes et peut en ouvrir
    (limite de 5) ; la modification et la suppression sont réservées au personnel.
    """

    serializer_class = BankAccountSerializer
    search_fields = ["account_number", "client__first_name", "client__last_name", "client__client_number"]
    filterset_fields = ["status", "account_type", "currency", "agency"]

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = BankAccount.objects.select_related("client", "agency").order_by("-opened_at", "-id")
        if not user.is_authenticated:
            return qs.none()
        return qs if user.is_staff else qs.filter(client__user=user)

    def perform_create(self, serializer):
        user = self.request.user
        data = serializer.validated_data
        if user.is_staff:
            client = data.get("client")
            if client is None:
                raise ValidationError({"client": ["Ce champ est obligatoire."]})
            agency = data.get("agency") or get_default_agency()
            account_number = data.get("account_number") or generate_account_number()
            extra = {}
        else:
            client = getattr(user, "client_profile", None)
            if client is None:
                raise ValidationError("Aucune fiche client n'est associée à cet utilisateur.")
            if client.accounts.count() >= MAX_ACCOUNTS_PER_CLIENT:
                raise ValidationError(f"Vous ne pouvez pas avoir plus de {MAX_ACCOUNTS_PER_CLIENT} comptes.")
            agency = get_default_agency()
            account_number = generate_account_number()
            extra = {"status": BankAccount.Status.ACTIVE}
        serializer.save(client=client, agency=agency, account_number=account_number, **extra)
