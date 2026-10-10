from django.db.models import Count, Q, Sum
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.accounts.models import BankAccount
from apps.clients.models import Client
from apps.transactions.models import Transaction

class StatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_staff:
            accounts = BankAccount.objects.all()
            clients = Client.objects.all()
            completed = Transaction.objects.filter(status=Transaction.Status.COMPLETED)
        else:
            accounts = BankAccount.objects.filter(client__user=request.user)
            clients = Client.objects.filter(user=request.user)
            completed = Transaction.objects.filter(status=Transaction.Status.COMPLETED).filter(
                Q(source_account__client__user=request.user) | Q(destination_account__client__user=request.user)
            )
        return Response({
            "clients": clients.count(),
            "active_clients": clients.filter(is_active=True).count(),
            "accounts": accounts.count(),
            "active_accounts": accounts.filter(status=BankAccount.Status.ACTIVE).count(),
            "total_balance": accounts.filter(status=BankAccount.Status.ACTIVE).aggregate(v=Sum("balance"))["v"] or 0,
            "transactions": completed.count(),
            "deposits_total": completed.filter(transaction_type=Transaction.Type.DEPOSIT).aggregate(v=Sum("amount"))["v"] or 0,
            "withdrawals_total": completed.filter(transaction_type=Transaction.Type.WITHDRAW).aggregate(v=Sum("amount"))["v"] or 0,
            "transfers_total": completed.filter(transaction_type=Transaction.Type.TRANSFER).aggregate(v=Sum("amount"))["v"] or 0,
            "transaction_counts": list(completed.values("transaction_type").annotate(count=Count("id")).order_by("transaction_type")),
        })
