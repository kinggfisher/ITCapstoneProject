import re
import base64
import json
import anthropic
import google.genai as genai
from django.conf import settings


def extract_from_text(text):
    """
    Parse design criteria text and extract load capacity information.

    Returns a dict with:
    - project: Project name extracted from text
    - drawing_number: Drawing number extracted from text
    - capacities: List of {name, value, metric} dicts
    - raw_text: Original input text
    """
    result = {
        "project": None,
        "drawing_number": None,
        "capacities": [],
        "raw_text": text
    }

    # Extract project name
    project_match = re.search(r'Project[:\s]+([^\n]+)', text, re.IGNORECASE)
    if project_match:
        result["project"] = project_match.group(1).strip()

    # Extract drawing number
    drawing_match = re.search(r'Drawing[:\s]+([^\n]+)', text, re.IGNORECASE)
    if drawing_match:
        result["drawing_number"] = drawing_match.group(1).strip()

    # Extract load capacities with values and metrics
    # Patterns like "Max Point Load: 50 kN" or "Maximum Axle Load: 100 t"
    capacity_patterns = [
        (r'Max(?:imum)?\s+Point\s+Load[:\s]+([0-9.]+)\s*(kN|t|kPa)', 'max_point_load'),
        (r'Max(?:imum)?\s+Axle\s+Load[:\s]+([0-9.]+)\s*(kN|t|kPa)', 'max_axle_load'),
        (r'Max(?:imum)?\s+Uniform\s+Distributed\s+Load[:\s]+([0-9.]+)\s*(kN|t|kPa)', 'max_uniform_distributor_load'),
        (r'Max(?:imum)?\s+Displacement(?:\s+Size)?[:\s]+([0-9.]+)\s*(kN|t|kPa)', 'max_displacement_size'),
    ]

    for pattern, capacity_name in capacity_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            value = float(match.group(1))
            metric = match.group(2)
            result["capacities"].append({
                "name": capacity_name,
                "value": value,
                "metric": metric
            })

    return result


PROMPT = """You are an expert engineering document analyzer.
Analyze this engineering drawing and extract load capacity data.

Return ONLY a JSON object with this exact structure:
{
  "project": "project name or null",
  "drawing_number": "drawing number or null",
  "capacities": [
    {
      "name": "capacity_type",
      "value": numeric_value,
      "metric": "unit"
    }
  ]
}

For "name", use ONLY these exact values (omit if not found in the drawing):
- "max_point_load"               — point / concentrated / outrigger loads
- "max_axle_load"                — axle loads
- "max_uniform_distributor_load" — uniform distributed loads (UDL / kPa floor loads)
- "max_displacement_size"        — vessel displacement / vessel size

For "metric", use ONLY: "kN", "t", or "kPa"

Return only the JSON object. No markdown, no explanation."""

NAME_MAP = {
    "max_uniform_distributed_load": "max_uniform_distributor_load",
    "max_udl": "max_uniform_distributor_load",
    "max_displacement": "max_displacement_size",
}


def _parse_json_response(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    result = json.loads(text)
    for cap in result.get("capacities", []):
        cap["name"] = NAME_MAP.get(cap["name"], cap["name"])
    return result


def extract_from_image(image_file, model="claude"):
    """Send image to Claude or Gemini Vision and return structured load capacity data."""
    if model == "gemini":
        return _extract_with_gemini(image_file)
    return _extract_with_claude(image_file)


def _extract_with_claude(image_file):
    mime_type = 'image/png' if image_file.name.lower().endswith('.png') else 'image/jpeg'
    image_data = base64.b64encode(image_file.read()).decode('utf-8')

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": image_data,
                    },
                },
                {"type": "text", "text": PROMPT},
            ],
        }],
    )

    result = _parse_json_response(message.content[0].text)
    result["raw_text"] = "[Extracted from image via Claude AI]"
    return result


def _extract_with_gemini(image_file):
    import PIL.Image
    import io

    client = genai.Client(api_key=settings.GOOGLE_API_KEY)

    image_bytes = image_file.read()
    pil_image = PIL.Image.open(io.BytesIO(image_bytes))

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=[PROMPT, pil_image],
    )

    result = _parse_json_response(response.text)
    result["raw_text"] = "[Extracted from image via Google Gemini AI]"
    return result