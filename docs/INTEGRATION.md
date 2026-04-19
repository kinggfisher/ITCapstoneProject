# Frontend-Backend Integration Guide

This document outlines critical integration points between the React frontend and Django REST backend for AssetGuard AI.

---

## Known Issues & Fixes

### Issue: Assessment Creation - Location Field Type Mismatch

**Status:** OPEN (GitHub Issue [45])

**Problem:**
Frontend was sending `location` as a string (location name), but backend API expects an integer (location ID).

**Impact:**

- POST `/api/assessments/` validation fails
- Error: `"location": ["Expected an integer, received string"]`
- Users cannot create assessments/compliance checks

**Solution:**
Update `LoadEntry.jsx` to extract location ID from asset object:

```javascript
// BEFORE (WRONG)
const payload = {
  location: asset.location_name, //  This is a string
  asset: parseInt(assetId, 10),
  equipment_type: selectedEquipment,
  load_value: parseFloat(loadValue),
};

// AFTER (CORRECT)
const payload = {
  location: asset.location, //  This is an integer ID
  asset: parseInt(assetId, 10),
  equipment_type: selectedEquipment,
  load_value: parseFloat(loadValue),
};
```

**Files Requiring Update:**

- `Front-end package/assetguard-frontend/src/pages/LoadEntry.jsx` - Assessment creation logic

---

## API Integration Checklist

### Authentication

- [x] JWT token endpoints implemented (`/api/token/`, `/api/token/refresh/`)
- [x] Frontend stores access and refresh tokens in localStorage
- [x] Auto-refresh on 401 response implemented
- [x] Authorization header format: `Bearer <token>`

### Assets Module

- [x] GET `/api/assets/` - list all assets with nested load_capacities
- [x] GET `/api/assets/{id}/` - get single asset with relationships
- [x] Response includes `location` (integer ID) and `location_name` (string)
- [x] Query parameter support for location filtering
- [x] Nested `load_capacities` array in response

### Assessments Module

- [ ] **URGENT**: Fix location field type in frontend payload
- [x] POST `/api/assessments/` - create assessment and run compliance check
- [x] Response distinguishes PASS/FAIL with `is_compliant` boolean
- [x] Email alerts on FAIL responses (configured in backend)
- [x] Auto-populate `created_by` field from authenticated user

### Equipment Options

- [x] GET `/api/equipment-options/` - available equipment types
- [x] Response includes capacity type mappings for validation

### File Extraction

- [x] POST `/api/extract/` - PDF file upload and text extraction
- [x] Returns extracted project, drawing number, and load capacities
- [x] Optional `auto_save` parameter to save extracted data to database

---

## Data Flow Diagrams

### Assessment Creation Flow

```
Frontend (LoadEntry.jsx)
    ↓
    • Fetch asset details (GET /api/assets/{id}/)
    • Extract location ID from asset.location
    • Get equipment options (GET /api/equipment-options/)
    ↓
User Input (location, asset, equipment_type, load_value)
    ↓
Backend (AssessmentViewSet)
    ↓
    • Validate asset belongs to location
    • Look up equipment-capacity mapping
    • Query LoadCapacity for asset
    ↓
Compliance Check Logic
    ↓
    • Compare load_value vs capacity_limit
    • Determine is_compliant (true/false)
    ↓
Return Response
    ├─ PASS: {"is_compliant": true, "result": "PASS", ...}
    └─ FAIL: {"is_compliant": false, "result": "FAIL", ...}
        ↓ (if FAIL)
        Send Email Alert
```

### Equipment Type to Capacity Mapping

```
equipment_type (from Assessment)
    ↓
EQUIPMENT_CAPACITY_MAP lookup
    ↓
(capacity_name, load_label) tuple
    ↓
Query LoadCapacity by (asset, capacity_name)
    ↓
Get max_load and metric from database
    ↓
Compare user input load_value with max_load
```

---

## Field Mapping Reference

### Assessment Request → Assessment Response

| Frontend Field               | Backend Field     | Type     | Notes                                 |
| ---------------------------- | ----------------- | -------- | ------------------------------------- |
| `location`                   | `location`        | integer  | **MUST be ID**, not name              |
| `asset`                      | `asset`           | integer  | Asset ID from URL params              |
| `equipment_type`             | `equipment_type`  | string   | One of 6 enum values                  |
| `load_value`                 | `load_value`      | float    | User-entered number                   |
| (optional) `equipment_model` | `equipment_model` | string   | Optional equipment details            |
| (optional) `notes`           | `notes`           | string   | Optional notes                        |
| N/A                          | `capacity_name`   | string   | Auto-filled by backend                |
| N/A                          | `capacity_metric` | string   | Auto-filled by backend                |
| N/A                          | `capacity_limit`  | float    | Auto-filled by backend                |
| N/A                          | `is_compliant`    | boolean  | Auto-calculated by backend            |
| N/A                          | `created_by`      | integer  | Auto-filled by backend (current user) |
| N/A                          | `created_at`      | ISO-8601 | Auto-filled by backend on creation    |

---

## Validation Rules

### Asset Retrieval

```python
# Verify asset belongs to selected location
if asset.location != location:
    raise ValidationError('Asset does not belong to this location')
```

### Equipment Type Validation

```python
# Check equipment type has a capacity mapping
mapping = EQUIPMENT_CAPACITY_MAP.get(equipment_type)
if not mapping:
    raise ValidationError('No mapping for this equipment type')
```

### Load Capacity Validation

```python
# Ensure asset has the required capacity type
try:
    load_capacity = LoadCapacity.objects.get(
        asset=asset,
        name=capacity_name
    )
except LoadCapacity.DoesNotExist:
    raise ValidationError('Asset has no capacity defined for this equipment type')
```

---

## Error Scenarios

### Scenario 1: Location Type Mismatch (CURRENT BUG)

**Request:**

```json
{
  "location": "Ground Floor",
  "asset": 1,
  "equipment_type": "crane_with_outriggers",
  "load_value": 150.5
}
```

**Response 400:**

```json
{
  "location": ["Expected an integer, received string"]
}
```

**Fix:** Send `location: 1` instead of `location: "Ground Floor"`

---

### Scenario 2: Asset Not in Location

**Request:**

```json
{
  "location": 1,
  "asset": 5, // Asset belongs to location 2
  "equipment_type": "crane_with_outriggers",
  "load_value": 150.5
}
```

**Response 400:**

```json
{
  "asset": ["Asset 'Drawing-001' does not belong to location 'Site 1'."]
}
```

---

### Scenario 3: Asset Missing Required Capacity

**Request:**

```json
{
  "location": 1,
  "asset": 1,
  "equipment_type": "crane_with_outriggers", // Requires max_point_load
  "load_value": 150.5
}
```

**Response 400:** (if Asset 1 has no max_point_load capacity)

```json
{
  "asset": ["Asset 'Drawing-001' has no 'max_point_load' capacity defined."]
}
```

---

## Environment Configuration

### Backend (.env)

```env
# Database
DB_HOST=your_postgres_host
DB_USER=postgres_user
DB_PASSWORD=postgres_password
DB_NAME=postgres
USE_SQLITE=false  # Set to 'true' for local development with SQLite

# Django
SECRET_KEY=your_secret_key
DEBUG=True

# Email Alerts
EMAIL_ALERTS=true
EMAIL_PROVIDER=gmail  # or 'resend'
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

### Frontend (.env)

```env
REACT_APP_API_URL=http://127.0.0.1:8000
```

---

## Testing Integration

### Manual Test Checklist

1. **Authentication**
   - [ ] Login with valid credentials
   - [ ] Receive JWT tokens
   - [ ] Access protected endpoints with token

2. **Asset Loading**
   - [ ] Dashboard loads asset list
   - [ ] Asset details include location ID and name
   - [ ] Location filtering works

3. **Assessment Creation** (CRITICAL - tests bug fix)
   - [ ] Select location by asset
   - [ ] Select equipment type
   - [ ] Enter load value
   - [ ] Submit creates assessment
   - [ ] Response shows PASS/FAIL
   - [ ] No 400 validation errors

4. **Compliance Results**
   - [ ] PASS result displayed correctly
   - [ ] FAIL result displayed, email sent (if enabled)
   - [ ] Assessment ID returned and stored

---

## Testing Commands

### Backend Test Coverage

```bash
cd backend
python manage.py test assessments.tests -v 2  # Run assessment tests
python manage.py test assets.tests -v 2        # Run asset tests
```

### Manual API Testing with cURL

```bash
# Get JWT token
TOKEN=$(curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"pass"}' | jq -r '.access')

# Create assessment (CORRECT - with location ID)
curl -X POST http://127.0.0.1:8000/api/assessments/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "location": 1,
    "asset": 1,
    "equipment_type": "crane_with_outriggers",
    "load_value": 150.5
  }'
```

---

## Related Documentation

- [API Specification](api.md)
- [Backend README](../README.md)
- [Frontend README](<../Front-end\ package/assetguard-frontend/README.md>)
- [Assessment Model Tests](../backend/assessments/tests.py)
- [Asset Model Tests](../backend/assets/tests.py)
