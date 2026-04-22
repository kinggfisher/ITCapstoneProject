from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from core.permissions import IsAdmin, IsAdminOrReadOnly
from core.email_utils import send_compliance_failure_alert
from .models import Assessment
from .serializers import AssessmentSerializer, AssessmentHistorySerializer
from .mappings import EQUIPMENT_CAPACITY_MAP
from django.http import HttpResponse
from datetime import datetime
import csv


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
        # Wrap in try/except: email failures must never crash the API response
        try:
            send_compliance_failure_alert(request.user, instance)
        except Exception as e:
            print(f"[assessments.views] Unexpected email error: {e}")

        return Response({
            "is_compliant": False,
            "result": "FAIL",
            "assessment_id": instance.id,
            "created_by": instance.created_by.username,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def export_csv(self, request):
        """
        Export all assessments as CSV (admin only).
        Query params for filtering:
        - is_compliant=true|false
        - equipment_type=crane_with_outriggers
        - date_from=2026-01-01
        - date_to=2026-12-31
        """
        queryset = self.get_queryset()

        # Apply filters if provided
        is_compliant = request.query_params.get('is_compliant')
        equipment_type = request.query_params.get('equipment_type')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        if is_compliant is not None:
            is_compliant_bool = is_compliant.lower() == 'true'
            queryset = queryset.filter(is_compliant=is_compliant_bool)

        if equipment_type:
            queryset = queryset.filter(equipment_type=equipment_type)

        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from_obj)
            except ValueError:
                pass

        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to_obj)
            except ValueError:
                pass

        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="all_assessments_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Asset', 'Location', 'Equipment Type', 'Load Value',
            'Capacity Metric', 'Compliant (PASS/FAIL)', 'Created By', 'Created At'
        ])

        for assessment in queryset:
            writer.writerow([
                assessment.id,
                assessment.asset.name,
                assessment.asset.location.name,
                assessment.get_equipment_type_display(),
                assessment.load_value,
                assessment.capacity_metric,
                'PASS' if assessment.is_compliant else 'FAIL',
                assessment.created_by.username if assessment.created_by else 'N/A',
                assessment.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response


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
        queryset = Assessment.objects.select_related(
            'asset', 'asset__location'
        ).filter(
            created_by=self.request.user
        ).order_by('-created_at')

        # Apply filters
        is_compliant = self.request.query_params.get('is_compliant')
        equipment_type = self.request.query_params.get('equipment_type')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        # Filter by compliance status (PASS/FAIL)
        if is_compliant is not None:
            is_compliant_bool = is_compliant.lower() == 'true'
            queryset = queryset.filter(is_compliant=is_compliant_bool)

        # Filter by equipment type
        if equipment_type:
            queryset = queryset.filter(equipment_type=equipment_type)

        # Filter by date range
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from_obj)
            except ValueError:
                pass

        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to_obj)
            except ValueError:
                pass

        return queryset

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def export_csv(self, request):
        """
        Export user's assessments as CSV.
        Query params for filtering:
        - is_compliant=true|false
        - equipment_type=crane_with_outriggers
        - date_from=2026-01-01
        - date_to=2026-12-31
        """
        queryset = self.get_queryset()

        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="my_assessments_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Asset', 'Location', 'Equipment Type', 'Load Value',
            'Capacity Metric', 'Compliant (PASS/FAIL)', 'Created At'
        ])

        for assessment in queryset:
            writer.writerow([
                assessment.id,
                assessment.asset.name,
                assessment.asset.location.name,
                assessment.get_equipment_type_display(),
                assessment.load_value,
                assessment.capacity_metric,
                'PASS' if assessment.is_compliant else 'FAIL',
                assessment.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response