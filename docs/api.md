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
