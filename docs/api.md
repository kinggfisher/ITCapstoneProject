# Asset Guard AI — API Spec (MVP)

Base URL (dev): `http://127.0.0.1:8000`

Content-Type: `application/json`

## Conventions
- All timestamps (if present) are ISO-8601 strings (e.g. `2026-03-22T10:15:00Z`).
- IDs are integers.
- Error responses use DRF default validation format (field -> list of messages).

---

## 1) Assets API

### GET `/api/assets/`
Returns a list of assets.

**Response 200 (example)**
```json
[
  {
    "id": 1,
    "name": "Crane Bay A",
    "location": "Site 1",
    "max_load_kg": 5000,
    "material_grade": "S355",
    "notes": "Max load applies to main beam only."
  }
]

## 7) Assessment History API

### GET `/api/assessment-history/`

Returns the current authenticated user's assessment history, ordered by most recent first.

**Authorization**: Bearer token required

**Response 200**

```json
[
  {
    "id": 42,
    "asset_name": "Berth 5",
    "location_name": "Port of Bunbury",
    "equipment_type": "crane_with_outriggers",
    "load_label": "Max Outrigger Load",
    "load_value": 850.0,
    "capacity_metric": "kN",
    "capacity_limit": 1000.0,
    "is_compliant": true,
    "notes": null,
    "created_at": "2026-04-10T08:32:00Z"
  }
]
```

**Response 200 (no records)**

```json
[]
```

**Response 401**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Notes**
- Only returns assessments created by the requesting user
- Results are ordered by `created_at` descending (newest first)