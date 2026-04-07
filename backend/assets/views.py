from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdminOrReadOnly
from .models import Asset, Location, LoadCapacity
from .serializers import AssetSerializer, LocationSerializer, LoadCapacitySerializer

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.select_related('location').prefetch_related('load_capacities').all()
    serializer_class = AssetSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = Asset.objects.all()
        location_id = self.request.query_params.get('location')
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        return queryset

class LoadCapacityViewSet(viewsets.ModelViewSet):
    queryset = LoadCapacity.objects.all()
    serializer_class = LoadCapacitySerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]