# Asset Guard AI — API Spec (MVP)

Base URL (dev): `http://127.0.0.1:8000`

Content-Type: `application/json`

## Conventions

- All timestamps (if present) are ISO-8601 strings (e.g. `2026-03-22T10:15:00Z`).
- IDs are integers.
- Error responses use DRF default validation format (field -> list of messages).
- All endpoints except authentication require JWT Bearer token in Authorization header.

---

## Authentication

Use JWT tokens for API access.

### POST `/api/token/`

Get JWT access and refresh tokens.

**Request Body**

```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response 200**

```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token"
}
```

**Response 401**

```json
{
  "detail": "No active account found with the given credentials"
}
```

Include the access token in Authorization header:

```
Authorization: Bearer <access_token>
```

### POST `/api/token/refresh/`

Refresh JWT access token using refresh token.

**Request Body**

```json
{
  "refresh": "jwt_refresh_token"
}
```

**Response 200**

```json
{
  "access": "new_jwt_access_token"
}
```

---

## 1) File Upload & Extraction API

### POST `/api/extract/`

Upload PDF files for design criteria extraction.

**Content-Type**: `multipart/form-data`
**Authorization**: Bearer token required

**Form Data**

- `file`: PDF file (required)
- `auto_save`: boolean (optional, default: false) - Auto-save extracted data to database

**Response 200 (Success)**

```json
{
  "project": "Building A",
  "drawing_number": "DA-001",
  "capacities": [
    {
      "name": "max_point_load",
      "value": 50.0,
      "metric": "kN"
    },
    {
      "name": "max_axle_load",
      "value": 100.0,
      "metric": "t"
    }
  ],
  "raw_text": "Project: Building A\nDrawing: DA-001\nMax Point Load: 50 kN...",
  "saved_ids": {
    "location_id": 1,
    "asset_id": 2,
    "capacity_ids": [3, 4]
  }
}
```

**Response 400 (Error)**

```json
{
  "error": "File field is required"
}
```

---

## 2) Assets API

### GET `/api/assets/`

Returns a list of all assets.

**Query Parameters**

- `location` (optional): Filter by location ID

**Response 200**

```json
[
  {
    "id": 1,
    "name": "Crane Bay A",
    "location": 1,
    "location_name": "Site 1",
    "load_capacities": [
      {
        "id": 3,
        "asset": 1,
        "name": "max_point_load",
        "metric": "kN",
        "max_load": 50.0,
        "details": "Max load applies to main beam only."
      }
    ]
  }
]
```

### GET `/api/assets/{id}/`

Get a specific asset by ID.

**Response 200**

```json
{
  "id": 1,
  "name": "Crane Bay A",
  "location": 1,
  "location_name": "Site 1",
  "load_capacities": [
    {
      "id": 3,
      "asset": 1,
      "name": "max_point_load",
      "metric": "kN",
      "max_load": 50.0,
      "details": "Max load applies to main beam only."
    }
  ]
}
```

### POST `/api/assets/`

Create a new asset. (Admin only)

**Request Body**

```json
{
  "name": "New Asset Name",
  "location": 1
}
```

### PUT `/api/assets/{id}/`

Update an asset. (Admin only)

### DELETE `/api/assets/{id}/`

Delete an asset. (Admin only)

---

## 3) Locations API

### GET `/api/locations/`

Returns a list of all locations.

**Response 200**

```json
[
  {
    "id": 1,
    "name": "Site 1"
  }
]
```

### GET `/api/locations/{id}/`

Get a specific location by ID.

### POST `/api/locations/`

Create a new location. (Admin only)

**Request Body**

```json
{
  "name": "New Location Name"
}
```

### PUT `/api/locations/{id}/`

Update a location. (Admin only)

### DELETE `/api/locations/{id}/`

Delete a location. (Admin only)

---

## 4) Load Capacities API

### GET `/api/load-capacities/`

Returns a list of all load capacities.

**Response 200**

```json
[
  {
    "id": 1,
    "asset": 1,
    "name": "max_point_load",
    "metric": "kN",
    "max_load": 50.0,
    "details": "Max load applies to main beam only."
  }
]
```

### GET `/api/load-capacities/{id}/`

Get a specific load capacity by ID.

### POST `/api/load-capacities/`

Create a new load capacity. (Admin only)

**Request Body**

```json
{
  "asset": 1,
  "name": "max_point_load",
  "metric": "kN",
  "max_load": 50.0,
  "details": "Optional details"
}
```

### PUT `/api/load-capacities/{id}/`

Update a load capacity. (Admin only)

### DELETE `/api/load-capacities/{id}/`

Delete a load capacity. (Admin only)

---

## 5) Assessments API

### GET `/api/assessments/`

Returns a list of all assessments (compliance checks).

**Response 200**

```json
[
  {
    "id": 1,
    "location": 1,
    "asset": 1,
    "equipment_type": "crane_with_outriggers",
    "equipment_model": "Model XYZ",
    "load_value": 25.0,
    "capacity_name": "max_point_load",
    "capacity_metric": "kN",
    "capacity_limit": 50.0,
    "is_compliant": true,
    "notes": "Passed compliance check",
    "created_by": 1,
    "created_by_username": "admin",
    "created_at": "2026-03-22T10:15:00Z"
  }
]
```

### GET `/api/assessments/{id}/`

Get a specific assessment by ID.

### POST `/api/assessments/`

Create a new assessment (run compliance check).

**Request Body**

```json
{
  "location": 1,
  "asset": 1,
  "equipment_type": "crane_with_outriggers",
  "equipment_model": "Model XYZ",
  "load_value": 25.0,
  "notes": "Optional notes"
}
```

**Required Fields**

- `location` (integer, required): Location ID (not name) — must match the asset's location
- `asset` (integer, required): Asset ID
- `equipment_type` (string, required): One of: `crane_with_outriggers`, `mobile_crane`, `heavy_vehicle`, `elevated_work_platform`, `storage_load`, `vessel`
- `load_value` (float, required): Load value in the appropriate unit

**Optional Fields**

- `equipment_model` (string): Model name or description of equipment
- `notes` (string): Additional notes about the assessment

**Important**: The `location` field MUST be an integer ID, not a location name. Frontend implementations should extract the location ID from the selected asset object.

**Response 201 (PASS)**

```json
{
  "is_compliant": true,
  "result": "PASS",
  "assessment_id": 1,
  "created_by": "admin"
}
```

**Response 201 (FAIL)**

```json
{
  "is_compliant": false,
  "result": "FAIL",
  "assessment_id": 1,
  "created_by": "admin"
}
```

### PUT `/api/assessments/{id}/`

Update an assessment. (Admin only)

### DELETE `/api/assessments/{id}/`

Delete an assessment. (Admin only)

---

## 6) Equipment Options API

### GET `/api/equipment-options/`

Returns available equipment types and their mappings.

**Response 200**

````json
[
  {
    "value": "crane_with_outriggers",
    "label": "Crane with outriggers",
    "load_label": "Load Value",
    "capacity_name": "max_point_load"
  },
  {
    "value": "mobile_crane",
    "label": "Mobile crane",
    "load_label": "Load Value",
    "capacity_name": "max_point_load"
  }
]

## 7) Assessment History API

### GET `/api/assessment-history/`

Returns the current authenticated user's assessment history, ordered by most recent first.

**Authorization**: Bearer token required

**Query Parameters (all optional)**

- `is_compliant` (string): Filter by compliance status - `"true"` for PASS, `"false"` for FAIL
- `equipment_type` (string): Filter by equipment type (e.g., `crane_with_outriggers`, `mobile_crane`)
- `date_from` (string): Start date filter in YYYY-MM-DD format (e.g., `2026-01-01`)
- `date_to` (string): End date filter in YYYY-MM-DD format (e.g., `2026-12-31`)

**Examples**

```bash
# Get all user's PASS results
GET /api/assessment-history/?is_compliant=true

# Get all FAIL results for crane equipment
GET /api/assessment-history/?is_compliant=false&equipment_type=crane_with_outriggers

# Get assessments in date range
GET /api/assessment-history/?date_from=2026-01-01&date_to=2026-12-31

# Combine multiple filters
GET /api/assessment-history/?is_compliant=true&equipment_type=mobile_crane&date_from=2026-03-01
````

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
- All filters are optional and can be combined

### GET `/api/assessment-history/export_csv/`

Export user's assessments as CSV file with optional filtering.

**Authorization**: Bearer token required

**Query Parameters (all optional)** - Same as assessment-history list above

**Response 200** - CSV file download

CSV columns:

- ID
- Asset
- Location
- Equipment Type
- Load Value
- Capacity Metric
- Compliant (PASS/FAIL)
- Created At

**Examples**

```bash
# Export all user's PASS assessments
GET /api/assessment-history/export_csv/?is_compliant=true

# Export crane assessments from last month
GET /api/assessment-history/export_csv/?equipment_type=crane_with_outriggers&date_from=2026-03-01&date_to=2026-03-31

# Export all assessments (no filters)
GET /api/assessment-history/export_csv/
```

---

## 8) All Assessments CSV Export API

### GET `/api/assessments/export_csv/`

Export all assessments as CSV file (includes all users' assessments). **Admin only**

**Authorization**: Bearer token required (admin user)

**Query Parameters (all optional)** - Same filters as assessment-history

**Response 200** - CSV file download

CSV columns:

- ID
- Asset
- Location
- Equipment Type
- Load Value
- Capacity Metric
- Compliant (PASS/FAIL)
- Created By (username who created it)
- Created At

**Examples**

```bash
# Export all FAIL assessments across all users
GET /api/assessments/export_csv/?is_compliant=false

# Export all crane assessments this month
GET /api/assessments/export_csv/?equipment_type=crane_with_outriggers&date_from=2026-04-01&date_to=2026-04-30

# Export all assessments
GET /api/assessments/export_csv/
```

---

## Permissions

- **Read operations** (GET): Available to all authenticated users
- **Write operations** (POST, PUT, DELETE): Admin users only (`is_staff=True`)
- **File upload** (`/api/extract/`): Admin users only

## Error Responses

### 401 Unauthorized

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden

```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found

```json
{
  "detail": "Not found."
}
```

### 400 Bad Request

```json
{
  "field_name": ["Error message"]
}
```

---

## Frontend Implementation Notes

### Authentication Flow

1. Login via POST `/api/token/` to get tokens
2. Store both `access` and `refresh` tokens in localStorage
3. Include access token in Authorization header for all API calls
4. When access token expires (401 response), use refresh token to get new access token
5. If refresh fails, redirect to login page

### File Upload

- Use FormData for file uploads to `/api/extract/`
- Handle loading states during upload process
- Display extracted data in user-friendly format
- Show success/error messages appropriately

### Assessment Creation

- Use POST `/api/assessments/` for compliance checks
- **IMPORTANT**: `location` field must be an integer ID, NOT a location name string
- Response indicates PASS/FAIL status
- Store assessment ID for reference
- Handle both PASS and FAIL responses appropriately

**Correct Implementation Example:**

```javascript
//  CORRECT - location is integer ID
const payload = {
  location: asset.location, // integer ID from asset object
  asset: asset.id, // integer ID
  equipment_type: selectedType, // string
  load_value: parseFloat(value), // float
};

await api.createAssessment(payload);
```

**Incorrect Implementation Example:**

```javascript
//  WRONG - location is string name
const payload = {
  location: "Ground Floor", // string - will cause validation error
  asset: 42,
  equipment_type: "crane_with_outriggers",
  load_value: 150.5,
};
```

### Data Relationships

- Locations contain Assets
  - `Asset.location` returns the location ID (integer)
  - Use this ID when creating assessments
- Assets have Load Capacities
- Assessments reference Location + Asset + Equipment Type
- Equipment types map to specific capacity types for comparison

### Assessment Filtering and CSV Export

**Filtering Without Download** - Get filtered JSON data:

```javascript
// Fetch filtered assessments
async function getFilteredAssessments(filters) {
  const params = new URLSearchParams();

  if (filters.isCompliant !== undefined) {
    params.append('is_compliant', filters.isCompliant.toString()); // true or false
  }
  if (filters.equipmentType) {
    params.append('equipment_type', filters.equipmentType);
  }
  if (filters.dateFrom) {
    params.append('date_from', filters.dateFrom); // YYYY-MM-DD format
  }
  if (filters.dateTo) {
    params.append('date_to', filters.dateTo); // YYYY-MM-DD format
  }

  const response = await fetch(
    `/api/assessment-history/?${params.toString()}`,
    {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }
  );
  return await response.json();
}

// Usage:
const data = await getFilteredAssessments({
  isCompliant: true,           // Optional: true for PASS, false for FAIL
  equipmentType: 'crane_with_outriggers', // Optional
  dateFrom: '2026-03-01',      // Optional: YYYY-MM-DD
  dateTo: '2026-03-31'         // Optional: YYYY-MM-DD
});
```

**CSV Export for User's Assessments**:

```javascript
// Export user's assessments as CSV
async function exportMyAssessments(filters = {}) {
  const params = new URLSearchParams();

  if (filters.isCompliant !== undefined) {
    params.append('is_compliant', filters.isCompliant.toString());
  }
  if (filters.equipmentType) {
    params.append('equipment_type', filters.equipmentType);
  }
  if (filters.dateFrom) {
    params.append('date_from', filters.dateFrom);
  }
  if (filters.dateTo) {
    params.append('date_to', filters.dateTo);
  }

  const url = `/api/assessment-history/export_csv/?${params.toString()}`;
  const response = await fetch(url, {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });

  // Trigger download
  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = `assessments_${new Date().toISOString().split('T')[0]}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// Usage:
await exportMyAssessments({
  isCompliant: false,  // Export only FAIL results
  dateFrom: '2026-03-01'
});
```

**CSV Export for All Assessments (Admin Only)**:

```javascript
// Export all assessments as CSV (admin only)
async function exportAllAssessments(filters = {}) {
  const params = new URLSearchParams();

  if (filters.isCompliant !== undefined) {
    params.append('is_compliant', filters.isCompliant.toString());
  }
  if (filters.equipmentType) {
    params.append('equipment_type', filters.equipmentType);
  }
  if (filters.dateFrom) {
    params.append('date_from', filters.dateFrom);
  }
  if (filters.dateTo) {
    params.append('date_to', filters.dateTo);
  }

  const url = `/api/assessments/export_csv/?${params.toString()}`;
  const response = await fetch(url, {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });

  // Trigger download
  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = `all_assessments_${new Date().toISOString().split('T')[0]}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// Usage:
await exportAllAssessments({
  isCompliant: true,
  equipmentType: 'mobile_crane'
});
```

**Filter Best Practices**:

1. **Date Format**: Always use `YYYY-MM-DD` format for date filters
2. **Compliance Filter**: Pass `true` or `false` as boolean, will be converted to string
3. **Equipment Types**: Use exact values from equipment dropdown - `crane_with_outriggers`, `mobile_crane`, `heavy_vehicle`, `elevated_work_platform`, `storage_load`, `vessel`
4. **Combined Filters**: All filters are optional and can be combined - backend handles missing parameters gracefully
5. **CSV Download**: Use the blob approach shown above to trigger browser downloads