from uuid import uuid4
from django.db import models

class DocumentMetadata(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    document_id = models.UUIDField(unique=True, db_index=True)

    # ── DOCUMENT IDENTITY ──────────────────────────────────────
    title = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    doc_number = models.CharField(max_length=100, blank=True)

    # ── VERSION CONTROL ─────────────────────────────────────────
    revision = models.CharField(max_length=20, blank=True)
    revision_date = models.DateField(null=True, blank=True)
    version_number = models.IntegerField(default=1)
    is_current = models.BooleanField(default=True, db_index=True)
    approval_status = models.CharField(max_length=30, blank=True)
    supersedes_doc_id = models.UUIDField(null=True, blank=True)
    superseded_by_id = models.UUIDField(null=True, blank=True)

    # ── PROJECT HIERARCHY ──────────────────────────────────────
    project_name = models.CharField(max_length=200, blank=True, db_index=True)
    project_id = models.CharField(max_length=50, blank=True, db_index=True)
    project_phase = models.CharField(max_length=50, blank=True)
    contract_number = models.CharField(max_length=100, blank=True)
    wbs_code = models.CharField(max_length=50, blank=True)
    package_code = models.CharField(max_length=50, blank=True)

    # ── LOCATION ───────────────────────────────────────────────
    location = models.CharField(max_length=200, blank=True)
    building = models.CharField(max_length=100, blank=True)
    floor_level = models.CharField(max_length=50, blank=True)
    zone = models.CharField(max_length=100, blank=True)
    grid_reference = models.CharField(max_length=100, blank=True)

    # ── PARTIES ────────────────────────────────────────────────
    main_contractor = models.CharField(max_length=200, blank=True)
    sub_contractor = models.CharField(max_length=200, blank=True)
    consultant = models.CharField(max_length=200, blank=True)
    vendor = models.CharField(max_length=200, blank=True)
    author = models.CharField(max_length=100, blank=True)
    approved_by = models.CharField(max_length=100, blank=True)

    # ── DRAWING-SPECIFIC ────────────────────────────────────────
    drawing_number = models.CharField(max_length=50, blank=True, db_index=True)
    discipline = models.CharField(max_length=30, blank=True)
    drawing_scale = models.CharField(max_length=30, blank=True)

    # ── FINANCIAL ──────────────────────────────────────────────
    contract_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=5, default='INR')

    # ── DATES ──────────────────────────────────────────────────
    document_date = models.DateField(null=True, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)
    approved_date = models.DateField(null=True, blank=True)

    # ── CONTENT TAGS ───────────────────────────────────────────
    trade = models.CharField(max_length=30, blank=True)
    material_type = models.CharField(max_length=100, blank=True)
    risk_level = models.CharField(max_length=20, blank=True)

    # ── QUALITY ────────────────────────────────────────────────
    metadata_confidence = models.FloatField(default=0.0)
    manually_verified = models.BooleanField(default=False)

    # ── AUDIT ──────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'document_metadata'
        indexes = [
            models.Index(fields=['document_id']),
            models.Index(fields=['is_current']),
            models.Index(fields=['project_id']),
            models.Index(fields=['drawing_number']),
            models.Index(fields=['approval_status']),
            models.Index(fields=['project_id', 'is_current']),
            models.Index(fields=['project_id', 'doc_number']),
        ]
