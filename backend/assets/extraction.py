import re


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