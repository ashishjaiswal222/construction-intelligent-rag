import os
import uuid
import hashlib
from rest_framework import serializers
from ..models.document import Document, DocumentFingerprint
from ..models.choices import DocumentStatus
from django.conf import settings
from shared.storage import get_storage

class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    project_id = serializers.CharField(required=False, max_length=100)

    def validate_file(self, value):
        # We can do preliminary checks here like max_size, allowed_extensions
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 500 * 1024 * 1024) # 500MB
        if value.size > max_size:
            raise serializers.ValidationError("File size exceeds maximum allowed size.")
        return value
        
    def create(self, validated_data):
        file_obj = validated_data['file']
        project_id = validated_data.get('project_id')
        
        # Calculate Fingerprint (SHA256)
        file_content = file_obj.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        fingerprint, fp_created = DocumentFingerprint.objects.get_or_create(hash=file_hash)
        
        # Check if hash already exists in Documents
        existing_doc = Document.objects.filter(fingerprint=fingerprint).first()
        if existing_doc:
            # We reset the file pointer just in case
            file_obj.seek(0)
            return existing_doc, False
            
        file_obj.seek(0)
        
        # Save file to storage abstraction
        storage = get_storage()
        safe_filename = f"{uuid.uuid4()}_{file_obj.name}"
        storage_path = storage.save(safe_filename, file_obj)
                
        # Create Document Record
        document = Document.objects.create(
            project_id=project_id,
            filename=file_obj.name,
            original_filename=file_obj.name,
            file_hash=file_hash,
            fingerprint=fingerprint,
            file_size=file_obj.size,
            storage_path=storage_path,
            status=DocumentStatus.QUEUED
        )
        
        return document, True

class DocumentSerializer(serializers.ModelSerializer):
    doc_id = serializers.UUIDField(source='id', read_only=True)
    doc_type_display = serializers.CharField(source='get_doc_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'doc_id', 'project_id', 'filename', 'file_size', 'mime_type', 'file_url',
            'doc_type', 'doc_type_display', 'doc_subtype', 'classification_confidence',
            'status', 'status_display', 'has_tables', 'has_images', 'has_drawings',
            'has_handwriting', 'language', 'error_message', 'created_at', 'updated_at'
        ]

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.storage_path:
            # Simple local URL. If using S3, you'd use default_storage.url()
            url = f"{settings.MEDIA_URL}{obj.storage_path}"
            if request:
                return request.build_absolute_uri(url)
            return url
        return None

class ReviewTaskSerializer(serializers.ModelSerializer):
    document = DocumentSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        from ..models.review import ReviewTask
        model = ReviewTask
        fields = [
            'id', 'document', 'reason', 'status', 'status_display',
            'assigned_to', 'resolution_notes', 'created_at', 'resolved_at'
        ]
