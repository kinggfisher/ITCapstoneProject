from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdmin, IsAdminOrReadOnly
from core.email_utils import send_compliance_failure_alert
from .models import Assessment
from .serializers import AssessmentSerializer
from .mappings import EQUIPMENT_CAPACITY_MAP


class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = Assessment.objects.select_related(
        'asset', 'asset__location', 'created_by'
    ).order_by('-created_at')
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(created_by=request.user)

        if instance.is_compliant:
            return Response({
                "is_compliant": True,
                "result": "PASS",
                "assessment_id": instance.id,
                "created_by": instance.created_by.username,
            }, status=status.HTTP_201_CREATED)

        # Compliance check failed — send email alert if enabled
        send_compliance_failure_alert(request.user, instance)

        return Response({
            "is_compliant": False,
            "result": "FAIL",
            "assessment_id": instance.id,
            "created_by": instance.created_by.username,
        }, status=status.HTTP_201_CREATED)


class EquipmentOptionsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        options = []
        for value, (capacity_name, load_label) in EQUIPMENT_CAPACITY_MAP.items():
            display = dict(Assessment.EquipmentType.choices).get(value, value)
            options.append({
                "value": value,
                "label": display,
                "load_label": load_label,
                # from load_capacities in GET /api/assets/:id/ using capacity_name to match
                "capacity_name": capacity_name,
            })
        return Response(options)
    

class AssessmentHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AssessmentHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only return assessments created by the requesting user, ordered by most recent
        return Assessment.objects.select_related(
            'asset', 'asset__location'
        ).filter(
            user=self.request.user
        ).order_by('-created_at')