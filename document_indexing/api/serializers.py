from rest_framework import serializers
from document_indexing.models.indexing_record import IndexingRecord

class IndexingRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndexingRecord
        fields = '__all__'
