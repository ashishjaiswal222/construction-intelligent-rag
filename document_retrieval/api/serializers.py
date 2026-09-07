from rest_framework import serializers

class QueryRequestSerializer(serializers.Serializer):
    query = serializers.CharField(required=True)
    project_id = serializers.CharField(required=False, allow_null=True)
