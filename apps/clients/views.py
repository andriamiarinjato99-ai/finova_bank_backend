from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from .models import Client
from .serializers import ClientSelfSerializer, ClientSerializer


class ClientViewSet(viewsets.ModelViewSet):
    """Le personnel gère tous les clients ; un client ne voit et ne modifie que sa propre fiche."""

    search_fields = ["client_number", "first_name", "last_name", "national_id", "email", "phone", "user__username"]
    filterset_fields = ["is_active"]

    def get_permissions(self):
        if self.action in ("create", "destroy"):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = Client.objects.select_related("user").order_by("-created_at")
        if not user.is_authenticated:
            return qs.none()
        return qs if user.is_staff else qs.filter(user=user)

    def get_serializer_class(self):
        user = getattr(self.request, "user", None)
        return ClientSerializer if (user and user.is_staff) else ClientSelfSerializer

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        client = Client.objects.select_related("user").filter(user=request.user).first()
        if not client:
            return Response({"detail": "Aucune fiche client associée à cet utilisateur."}, status=404)
        return Response(self.get_serializer(client).data)
