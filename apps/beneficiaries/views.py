from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from .models import Beneficiary
from .serializers import BeneficiarySerializer

class BeneficiaryViewSet(viewsets.ModelViewSet):
    serializer_class = BeneficiarySerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "account_number", "bank_name"]
    filterset_fields = ["owner", "is_active"]

    def get_queryset(self):
        qs = Beneficiary.objects.select_related("owner").all().order_by("-created_at")
        if self.request.user.is_staff:
            return qs
        return qs.filter(owner__user=self.request.user)

    def perform_create(self, serializer):
        owner = getattr(self.request.user, "client_profile", None)
        if owner is None:
            raise ValidationError("Cet utilisateur n'est pas associé à un client.")
        serializer.save(owner=owner)

    def perform_update(self, serializer):
        beneficiary = self.get_object()
        if not self.request.user.is_staff and beneficiary.owner.user_id != self.request.user.id:
            raise ValidationError("Vous ne pouvez pas modifier ce bénéficiaire.")
        serializer.save()
