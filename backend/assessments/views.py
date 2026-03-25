from rest_framework import viewsets
from .models import Assessment
from .serializers import AssessmentSerializer

class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = Assessment.objects.all().order_by('-created_at')
    serializer_class = AssessmentSerializer