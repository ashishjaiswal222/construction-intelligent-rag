# Phase 5: Data Models and API

## 1. The `DocumentMetadata` Model

This is the most heavily indexed and critical model in the platform for search precision. It contains exactly 35 highly structured fields.

**Document Identity (3 fields)**
- `title` (CharField 500)
- `description` (TextField)
- `doc_number` (CharField 100)

**Version Control (7 fields)**
- `revision` (CharField 20)
- `revision_date` (DateField)
- `version_number` (IntegerField)
- `is_current` (BooleanField, db_index=True)
- `approval_status` (CharField 30)
- `supersedes_doc_id` (UUIDField)
- `superseded_by_id` (UUIDField)

**Project Hierarchy (6 fields)**
- `project_name` (CharField 200, db_index=True)
- `project_id` (CharField 50, db_index=True)
- `project_phase` (CharField 50)
- `contract_number` (CharField 100)
- `wbs_code` (CharField 50)
- `package_code` (CharField 50)

**Location (5 fields)**
- `location` (CharField 200)
- `building` (CharField 100)
- `floor_level` (CharField 50)
- `zone` (CharField 100)
- `grid_reference` (CharField 100)

**Parties (6 fields)**
- `main_contractor` (CharField 200)
- `sub_contractor` (CharField 200)
- `consultant` (CharField 200)
- `vendor` (CharField 200)
- `author` (CharField 100)
- `approved_by` (CharField 100)

**Drawing-Specific (3 fields)**
- `drawing_number` (CharField 50, db_index=True)
- `discipline` (CharField 30)
- `drawing_scale` (CharField 30)

**Financial (2 fields)**
- `contract_value` (DecimalField)
- `currency` (CharField 5)

**Dates (4 fields)**
- `document_date` (DateField)
- `issue_date` (DateField)
- `received_date` (DateField)
- `approved_date` (DateField)

**Content Tags (3 fields)**
- `trade` (CharField 30)
- `material_type` (CharField 100)
- `risk_level` (CharField 20)

**Quality & Audit (4 fields)**
- `metadata_confidence` (FloatField)
- `manually_verified` (BooleanField)
- `created_at` (DateTimeField)
- `updated_at` (DateTimeField)

### Database Indexing Strategy
To ensure retrieval latency remains under 50ms, extensive database indexes are applied:
- `is_current`
- `project_id`
- `drawing_number`
- `approval_status`
- **Composite Index 1**: `['project_id', 'is_current']` (The most frequently queried combination in the platform).
- **Composite Index 2**: `['project_id', 'doc_number']`

## 2. API Endpoints

The `document_metadata` app exposes a set of REST APIs for the frontend UI and human-review workflows.

- `GET /api/metadata/<uuid:document_id>/`: Returns the full 35-field metadata payload for a specific document.
- `GET /api/metadata/project/<str:project_id>/current/`: Returns a fast, lightweight list of all active (`is_current=True`) documents in a project.
- `GET /api/metadata/project/<str:project_id>/drawings/`: A specialized endpoint that returns only drawings. It supports query parameter filtering by `discipline`, `approval_status`, and `revision` for the drawing browser UI.
- `PATCH /api/metadata/<uuid:document_id>/verify/`: Used by the Human-in-the-Loop review queue to mark Groq's extraction as visually verified by an engineer.
- `PATCH /api/metadata/<uuid:document_id>/override/`: Allows an engineer to manually fix a hallucinated or missing value. Dynamically accepts field names and automatically sets `manually_verified=True`.
