from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count, Avg
from document_chunking.models.chunking_job import ChunkingJob
from document_chunking.models.document_chunk import DocumentChunk
from document_chunking.api.serializers import ChunkingJobSerializer, DocumentChunkSerializer
from document_chunking.tasks.chunk_document import chunk_document_task

@api_view(['GET'])
def get_chunking_job(request, document_id):
    job = ChunkingJob.objects.filter(document_id=document_id).order_by('-created_at').first()
    if not job:
        return Response({'detail': 'Not found'}, status=404)
    serializer = ChunkingJobSerializer(job)
    return Response(serializer.data)

@api_view(['GET'])
def get_document_chunks(request, document_id):
    chunks = DocumentChunk.objects.filter(document_id=document_id)
    chunk_type = request.GET.get('chunk_type')
    if chunk_type:
        chunks = chunks.filter(chunk_type=chunk_type)
        
    # Simple pagination could be added here, but keeping it simple as per instructions
    serializer = DocumentChunkSerializer(chunks[:500], many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_chunking_stats(request, document_id):
    job = ChunkingJob.objects.filter(document_id=document_id).order_by('-created_at').first()
    if not job:
        return Response({'detail': 'Not found'}, status=404)
        
    total_chunks = DocumentChunk.objects.filter(document_id=document_id).count()
    breakdown_query = DocumentChunk.objects.filter(document_id=document_id).values('chunk_type').annotate(count=Count('id'))
    strategy_breakdown = {item['chunk_type']: item['count'] for item in breakdown_query}
    
    avg_length = DocumentChunk.objects.filter(document_id=document_id).aggregate(avg=Avg('char_count'))['avg'] or 0
    
    # We don't have a specific `needs_review` field, it's inside `metadata` JSON.
    # In Postgres, we could query JSON natively. Since SQLite is possible, we count in Python or use a basic filter
    # To keep it DB-agnostic without raw SQL, we can just fetch and count if small, but let's just do an approximate JSON query string match or omit.
    # The requirement says "chunks_needing_review: int".
    chunks_needing_review = DocumentChunk.objects.filter(document_id=document_id, metadata__icontains='"needs_review": true').count()
    
    return Response({
        'total_chunks': total_chunks,
        'strategy_breakdown': strategy_breakdown,
        'avg_chunk_length': round(avg_length, 2),
        'chunks_needing_review': chunks_needing_review,
    })

@api_view(['POST'])
def retry_chunking_job(request, document_id):
    chunk_document_task.delay(str(document_id))
    return Response({'status': 'Retry task dispatched'})
