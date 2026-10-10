from rest_framework import serializers
from .models import Employee

class EmployeeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = ["id", "user", "username", "full_name", "employee_number", "agency", "role", "phone", "is_active"]

    def get_full_name(self, obj):
        return obj.user.get_full_name()
