from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from assets.models import Location, Asset, LoadCapacity
from assets.extraction import extract_from_text


def home(request):
    return JsonResponse({"message": "Welcome to the IT Capstone Project API"})


def demo(request):
    return render(request, 'demo.html')


@api_view(['POST'])
@permission_classes([AllowAny])
def extract_design_criteria(request):
    """
    Extract design criteria from text input.

    Request body:
    {
        "text": "Project: BuildingA\nDrawing: DA-001\nMax Point Load: 50 kN",
        "auto_save": false
    }

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
        text = request.data.get('text', '')
        auto_save = request.data.get('auto_save', False)

        if not text or not text.strip():
            return Response(
                {"error": "Text field is required and cannot be empty"},
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
                name=drawing_number
            )
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