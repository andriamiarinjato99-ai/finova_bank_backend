from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Transaction
from .serializers import TransactionSerializer, DepositSerializer, WithdrawSerializer, TransferSerializer
from .filters import TransactionFilter
from .services import deposit, withdraw, transfer


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """Historique (lecture seule) + opérations de dépôt, retrait et virement."""

    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["reference", "description", "source_account__account_number", "destination_account__account_number"]
    filterset_class = TransactionFilter
    ordering_fields = ["created_at", "amount"]

    def get_queryset(self):
        user = self.request.user
        qs = Transaction.objects.select_related(
            "source_account__client", "destination_account__client", "performed_by"
        ).order_by("-created_at", "-id")
        if not user.is_authenticated:
            return qs.none()
        if user.is_staff:
            return qs
        # Un client voit les opérations qu'il a émises ET celles qu'il a reçues.
        return qs.filter(Q(source_account__client__user=user) | Q(destination_account__client__user=user))

    def _respond(self, request, tx):
        return Response(TransactionSerializer(tx, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="deposit", serializer_class=DepositSerializer)
    def make_deposit(self, request):
        serializer = DepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tx = deposit(user=request.user, **serializer.validated_data)
        return self._respond(request, tx)

    @action(detail=False, methods=["post"], url_path="withdraw", serializer_class=WithdrawSerializer)
    def make_withdraw(self, request):
        serializer = WithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tx = withdraw(user=request.user, **serializer.validated_data)
        return self._respond(request, tx)

    @action(detail=False, methods=["post"], url_path="transfer", serializer_class=TransferSerializer)
    def make_transfer(self, request):
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tx = transfer(user=request.user, **serializer.validated_data)
        return self._respond(request, tx)
