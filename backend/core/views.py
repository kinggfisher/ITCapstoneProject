from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from assets.models import Location, Asset, LoadCapacity
from assets.extraction import extract_from_text
import pdfplumber
from PIL import Image
import io


def extract_text_from_file(file):
    """
    Extract text from uploaded file (PDF or image).
    """
    if file.name.lower().endswith('.pdf'):
        with pdfplumber.open(file) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text() + '\n'
            return text
    elif file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
        # For images, assume text is embedded or use OCR if available
        # For now, raise error
        raise ValueError("Image files are not supported yet. Please upload a PDF.")
    else:
        raise ValueError("Unsupported file type. Only PDF files are supported.")


def home(request):
    return JsonResponse({"message": "Welcome to the IT Capstone Project API"})


def demo(request):
    return render(request, 'demo.html')


@api_view(['POST'])
@permission_classes([AllowAny])
def extract_design_criteria(request):
    """
    Extract design criteria from uploaded file (PDF or image).

    Request: multipart/form-data with 'file' field
    Optional: 'auto_save' boolean

    Returns:
    {
        "project": "BuildingA",
        "drawing_number": "DA-001",
        "capacities": [{"name": "max_point_load", "value": 50, "metric": "kN"}],
        "raw_text": "...",
        "saved_ids": {"location_id": 1, "asset_id": 2, "capacity_ids": [3]}  # Only if auto_save=true
    }
    """
    try:
        file = request.FILES.get('file')
        auto_save = request.data.get('auto_save', False)

        if not file:
            return Response(
                {"error": "File field is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract text from file
        text = extract_text_from_file(file)

        if not text or not text.strip():
            return Response(
                {"error": "No text could be extracted from the file"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract data from text
        extracted = extract_from_text(text)

        # If auto_save requested, save to database
        if auto_save:
            saved_ids = {}

            # Create or get location
            project_name = extracted.get('project') or 'Unknown Project'
            location, _ = Location.objects.get_or_create(name=project_name)
            saved_ids['location_id'] = location.id

            # Create or get asset
            drawing_number = extracted.get('drawing_number') or 'Unknown Drawing'
            asset, _ = Asset.objects.get_or_create(
                location=location,
                name=drawing_number,
                defaults={'drawing_file': file}
            )
            if not asset.drawing_file:
                asset.drawing_file = file
                asset.save()
            saved_ids['asset_id'] = asset.id

            # Create load capacities
            capacity_ids = []
            for capacity_data in extracted.get('capacities', []):
                try:
                    capacity, created = LoadCapacity.objects.get_or_create(
                        asset=asset,
                        name=capacity_data['name'],
                        defaults={
                            'metric': capacity_data['metric'],
                            'max_load': capacity_data['value']
                        }
                    )
                    capacity_ids.append(capacity.id)
                except Exception as e:
                    # Skip invalid capacity names
                    pass

            saved_ids['capacity_ids'] = capacity_ids
            extracted['saved_ids'] = saved_ids

        return Response(extracted, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout endpoint to invalidate user tokens.

    Request body:
    {
        "refresh": "refresh_token_here"  (optional)
    }

    Returns:
    {"message": "Successfully logged out"}
    """
    try:
        refresh_token = request.data.get('refresh')

        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()

        return Response(
            {"message": "Successfully logged out"},
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )