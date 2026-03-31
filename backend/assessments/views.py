from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Assessment
from .serializers import AssessmentSerializer
from .mappings import EQUIPMENT_CAPACITY_MAP


class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = Assessment.objects.select_related(
        'asset', 'asset__location'
    ).order_by('-created_at')
    serializer_class = AssessmentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        if instance.is_compliant:
            return Response({
                "is_compliant": True,
                "result": "PASS",
            }, status=status.HTTP_201_CREATED)

        return Response({
            "is_compliant": False,
            "result": "FAIL",
        }, status=status.HTTP_201_CREATED)


class EquipmentOptionsViewSet(viewsets.ViewSet):
    def list(self, request):
        options = []
        for value, (capacity_name, metric, load_label) in EQUIPMENT_CAPACITY_MAP.items():
            display = dict(Assessment.EquipmentType.choices).get(value, value)
            options.append({
                "value": value,
                "label": display,
                "load_label": load_label,
                "metric": metric,
            })
        return Response(options)