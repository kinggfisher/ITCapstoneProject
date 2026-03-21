from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
# from django.core.mail import send_mail
from .models import Assessment
from .serializers import AssessmentSerializer
from assets.models import Asset

class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = Assessment.objects.all().order_by('-created_at')
    serializer_class = AssessmentSerializer

    def perform_create(self, serializer):
        asset = Asset.objects.get(pk=self.request.data['asset'])
        load_kg = float(self.request.data['load_kg'])

        # Compliance check
        is_compliant = load_kg <= asset.max_load_kg

        # Save assessment
        assessment = serializer.save(is_compliant=is_compliant)

        # Send email if non-compliant -- 
        # if not is_compliant:
        #     send_mail(
        #         subject=f'Non-Compliant Load Alert — {asset.name}',
        #         message=f'A load of {load_kg}kg was submitted for {asset.name}. The maximum allowed is {asset.max_load_kg}kg.',
        #         from_email='alerts@assetguard.com',
        #         recipient_list=['engineer@company.com'],
        #     )