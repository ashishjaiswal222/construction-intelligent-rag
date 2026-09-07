from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from document_metadata.models.document_metadata import DocumentMetadata
from document_metadata.api.serializers import DocumentMetadataSerializer, OverrideMetadataSerializer, VerifyMetadataSerializer

class DocumentMetadataDetailView(APIView):
    def get(self, request, document_id):
        metadata = get_object_or_404(DocumentMetadata, document_id=document_id)
        serializer = DocumentMetadataSerializer(metadata)
        return Response(serializer.data)

class CurrentProjectMetadataView(APIView):
    def get(self, request, project_id):
        metadata = DocumentMetadata.objects.filter(project_id=project_id, is_current=True)
        serializer = DocumentMetadataSerializer(metadata, many=True)
        return Response(serializer.data)

class ReviewQueueView(APIView):
    def get(self, request):
        metadata = DocumentMetadata.objects.filter(
            metadata_confidence__lte=0.3,
            manually_verified=False
        ).order_by('created_at')
        serializer = DocumentMetadataSerializer(metadata, many=True)
        return Response(serializer.data)

class ProjectDrawingsView(APIView):
    def get(self, request, project_id):
        qs = DocumentMetadata.objects.filter(project_id=project_id).exclude(drawing_number='')
        
        discipline = request.query_params.get('discipline')
        if discipline:
            qs = qs.filter(discipline=discipline)
            
        approval_status = request.query_params.get('approval_status')
        if approval_status:
            qs = qs.filter(approval_status=approval_status)
            
        revision = request.query_params.get('revision')
        if revision:
            qs = qs.filter(revision=revision)

        serializer = DocumentMetadataSerializer(qs, many=True)
        return Response(serializer.data)

class VerifyMetadataView(APIView):
    def patch(self, request, document_id):
        metadata = get_object_or_404(DocumentMetadata, document_id=document_id)
        serializer = VerifyMetadataSerializer(data=request.data)
        if serializer.is_valid():
            metadata.manually_verified = serializer.validated_data['verified']
            metadata.save(update_fields=['manually_verified'])
            return Response({'status': 'verified'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OverrideMetadataView(APIView):
    def patch(self, request, document_id):
        metadata = get_object_or_404(DocumentMetadata, document_id=document_id)
        # Using dict instead of serializer to allow dynamic field names
        updates = request.data
        valid_fields = [f.name for f in DocumentMetadata._meta.get_fields()]
        
        for field_name, value in updates.items():
            if field_name in valid_fields and field_name not in ['id', 'document_id', 'created_at', 'updated_at']:
                setattr(metadata, field_name, value)
                
        metadata.manually_verified = True
        metadata.save()
        return Response(DocumentMetadataSerializer(metadata).data)
