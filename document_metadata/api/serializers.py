from rest_framework import serializers
from document_metadata.models.document_metadata import DocumentMetadata

class DocumentMetadataSerializer(serializers.ModelSerializer):
    filename = serializers.SerializerMethodField()

    class Meta:
        model = DocumentMetadata
        fields = '__all__'
        
    def get_filename(self, obj):
        from document_classification.models import Document
        try:
            doc = Document.objects.get(id=obj.document_id)
            if hasattr(doc, 'filename') and doc.filename:
                return doc.filename
            if hasattr(doc, 'file') and doc.file:
                return str(doc.file).split('/')[-1].split('\\')[-1]
            return str(doc.id)
        except Document.DoesNotExist:
            return 'Unknown File'

class OverrideMetadataSerializer(serializers.Serializer):
    field_name = serializers.CharField()
    value = serializers.CharField(allow_blank=True, allow_null=True)

class VerifyMetadataSerializer(serializers.Serializer):
    verified = serializers.BooleanField()
    notes = serializers.CharField(required=False, allow_blank=True)
