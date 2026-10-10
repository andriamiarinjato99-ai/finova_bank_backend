from rest_framework import viewsets
from apps.permissions import IsStaffOrReadOnly
from .models import Agency
from .serializers import AgencySerializer

class AgencyViewSet(viewsets.ModelViewSet):
    queryset = Agency.objects.all().order_by("code")
    serializer_class = AgencySerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ["code", "name", "address"]
    filterset_fields = ["is_active"]
