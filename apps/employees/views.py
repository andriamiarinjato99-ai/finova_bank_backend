from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from .models import Employee
from .serializers import EmployeeSerializer

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related("user", "agency").all().order_by("employee_number")
    serializer_class = EmployeeSerializer
    permission_classes = [IsAdminUser]
    search_fields = ["employee_number", "user__username", "user__first_name", "user__last_name"]
    filterset_fields = ["agency", "role", "is_active"]
