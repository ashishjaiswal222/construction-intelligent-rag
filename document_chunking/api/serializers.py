from rest_framework import serializers
from document_chunking.models.chunking_job import ChunkingJob
from document_chunking.models.document_chunk import DocumentChunk

class ChunkingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkingJob
        fields = '__all__'

class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = '__all__'
