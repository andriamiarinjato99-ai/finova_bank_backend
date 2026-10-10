from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.agencies.views import AgencyViewSet
from apps.clients.views import ClientViewSet
from apps.accounts.views import BankAccountViewSet
from apps.beneficiaries.views import BeneficiaryViewSet
from apps.employees.views import EmployeeViewSet
from apps.transactions.views import TransactionViewSet
from apps.audit.views import AuditLogViewSet

router = DefaultRouter()
router.register("agencies", AgencyViewSet, basename="agency")
router.register("clients", ClientViewSet, basename="client")
router.register("accounts", BankAccountViewSet, basename="account")
router.register("beneficiaries", BeneficiaryViewSet, basename="beneficiary")
router.register("employees", EmployeeViewSet, basename="employee")
router.register("transactions", TransactionViewSet, basename="transactions")
router.register("audit", AuditLogViewSet, basename="audit")

urlpatterns = [
    path("", include(router.urls)),
    path("", include("apps.dashboard.urls")),
]
