import base64
import json
import re


VALID_CAPACITY_NAMES = {
    "max_point_load",
    "max_axle_load",
    "max_uniform_distributor_load",
    "max_displacement_size",
}

VALID_METRICS = {"kN", "t", "kPa"}

NAME_MAP = {
    "max_uniform_distributed_load": "max_uniform_distributor_load",
    "max_uniformly_distributed_load": "max_uniform_distributor_load",
    "max_udl": "max_uniform_distributor_load",
    "udl": "max_uniform_distributor_load",
    "uniform_distributed_load": "max_uniform_distributor_load",
    "uniformly_distributed_load": "max_uniform_distributor_load",
    "max_displacement": "max_displacement_size",
    "vessel_displacement": "max_displacement_size",
    "max_vessel_displacement": "max_displacement_size",
}

METRIC_MAP = {
    "kn": "kN",
    "kilonewton": "kN",
    "kilonewtons": "kN",
    "t": "t",
    "tonne": "t",
    "tonnes": "t",
    "tons": "t",
    "ton": "t",
    "kpa": "kPa",
    "kilopascal": "kPa",
    "kilopascals": "kPa",
}

PROMPT = """You are an expert engineering document analyzer.
Analyze this engineering drawing and extract ONLY design load capacity data that is useful for an asset compliance check.

Only extract values from sections or callouts that clearly describe:
- DESIGN CRITERIA
- DESIGN LOADS
- LOADING SPECIFICATIONS
- VERTICAL LOADS / HORIZONTAL LOADS
- deck/floor/platform load tables
- point, concentrated, outrigger, wheel, axle, UDL, or vessel displacement limits

Do NOT extract:
- general notes unless they contain a specific load capacity
- construction notes
- ordinary material specifications
- dimensions without load meaning
- standards references without a specific load value
- equipment weights that are not stated as an asset capacity limit

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

For "name", use ONLY these exact values:
- "max_point_load" for point, concentrated, wheel, outrigger, or pad loads
- "max_axle_load" for axle, axle group, truck axle, vehicle axle loads
- "max_uniform_distributor_load" for UDL, uniform distributed, uniformly distributed, floor, deck, platform, or area loads
- "max_displacement_size" for vessel displacement or vessel size limits

For "metric", use ONLY: "kN", "t", or "kPa".
If a value is unclear or not explicitly present, omit it. Do not guess.
Return pure JSON only. No markdown, no commentary."""


def _normalise_capacity_name(name):
    normalised = str(name or "").strip().lower().replace("-", "_").replace(" ", "_")
    normalised = NAME_MAP.get(normalised, normalised)
    return normalised if normalised in VALID_CAPACITY_NAMES else None


def _normalise_metric(metric):
    key = str(metric or "").strip().lower()
    return METRIC_MAP.get(key)


def _parse_number(value):
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"\d+(?:,\d{3})*(?:\.\d+)?", str(value or ""))
    if not match:
        return None
    return float(match.group(0).replace(",", ""))


def _dedupe_capacities(capacities):
    deduped = {}
    for capacity in capacities:
        name = _normalise_capacity_name(capacity.get("name"))
        metric = _normalise_metric(capacity.get("metric"))
        value = _parse_number(capacity.get("value"))
        if not name or not metric or value is None:
            continue
        deduped[name] = {
            "name": name,
            "value": value,
            "metric": metric,
        }
    return list(deduped.values())


def _parse_json_response(text):
    """Parse AI output defensively and normalize values before database save."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()

    # Some models still add prose; keep the first JSON object if needed.
    if not text.startswith("{"):
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)

    data = json.loads(text)
    return {
        "project": data.get("project"),
        "drawing_number": data.get("drawing_number"),
        "capacities": _dedupe_capacities(data.get("capacities", [])),
        "raw_text": text,
    }


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

    # Extract project name from common title-block or generated-report labels.
    project_match = re.search(r'\bProject(?:\s+Name)?[:\s]+([^\n]+)', text, re.IGNORECASE)
    if project_match:
        result["project"] = project_match.group(1).strip()

    # Extract drawing number
    drawing_match = re.search(r'\b(?:Drawing(?:\s+Number)?|Dwg\.?\s*No\.?|Drawing\s*No\.?)[:\s]+([^\n]+)', text, re.IGNORECASE)
    if drawing_match:
        result["drawing_number"] = drawing_match.group(1).strip()

    value_unit = r'([0-9][0-9,]*(?:\.[0-9]+)?)\s*(kN|KN|t|T|tonne|tonnes|tons|kPa|KPA|kilopascal|kilopascals)'

    # Extract load capacities with values and metrics. These patterns are
    # intentionally limited to load/capacity language to avoid general notes.
    capacity_patterns = [
        ('max_point_load', [
            rf'\bMax(?:imum)?\s+(?:Point|Concentrated|Wheel|Outrigger|Pad)\s+Load\s*[:=-]?\s*{value_unit}',
            rf'\b(?:Point|Concentrated|Wheel|Outrigger|Pad)\s+Load(?:\s+Limit)?\s*[:=-]?\s*{value_unit}',
        ]),
        ('max_axle_load', [
            rf'\bMax(?:imum)?\s+(?:Axle|Axle\s+Group|Vehicle\s+Axle|Truck\s+Axle)\s+Load\s*[:=-]?\s*{value_unit}',
            rf'\b(?:Axle|Axle\s+Group|Vehicle\s+Axle|Truck\s+Axle)\s+Load(?:\s+Limit)?\s*[:=-]?\s*{value_unit}',
        ]),
        ('max_uniform_distributor_load', [
            rf'\bMax(?:imum)?\s+(?:Uniform(?:ly)?\s+Distributed|Uniform\s+Distributor|UDL|Floor|Deck|Platform|Area)\s+Load\s*[:=-]?\s*{value_unit}',
            rf'\b(?:Uniform(?:ly)?\s+Distributed\s+Load|Uniform\s+Distributor\s+Load|UDL|Floor\s+Live\s+Load|Deck\s+Load|Platform\s+Load|Area\s+Load)\s*[:=-]?\s*{value_unit}',
        ]),
        ('max_displacement_size', [
            rf'\bMax(?:imum)?\s+(?:Displacement|Vessel\s+Displacement|Vessel\s+Size)(?:\s+Size)?\s*[:=-]?\s*{value_unit}',
            rf'\b(?:Displacement|Vessel\s+Displacement|Vessel\s+Size)(?:\s+Limit)?\s*[:=-]?\s*{value_unit}',
        ]),
    ]

    capacities = []
    for capacity_name, patterns in capacity_patterns:
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                capacities.append({
                    "name": capacity_name,
                    "value": match.group(1),
                    "metric": match.group(2),
                })

    result["capacities"] = _dedupe_capacities(capacities)

    return result


def extract_from_image(image_file, model="claude"):
    """Send image to Claude or Gemini Vision and return structured load capacity data."""
    if model == "gemini":
        return _extract_with_gemini(image_file)
    return _extract_with_claude(image_file)


def _extract_with_claude(image_file):
    import anthropic
    from django.conf import settings

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
    import io
    import PIL.Image
    import google.genai as genai
    from django.conf import settings

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
