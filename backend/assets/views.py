from rest_framework import viewsets
from .models import Asset, Location, LoadCapacity
from .serializers import AssetSerializer, LocationSerializer, LoadCapacitySerializer

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer

    def get_queryset(self):
        queryset = Asset.objects.all()
        location_id = self.request.query_params.get('location')
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        return queryset

class LoadCapacityViewSet(viewsets.ModelViewSet):
    queryset = LoadCapacity.objects.all()
    serializer_class = LoadCapacitySerializer