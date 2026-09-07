from rest_framework import serializers

class GenerationRequestSerializer(serializers.Serializer):
    query = serializers.CharField()
    project_id = serializers.CharField(required=False, allow_null=True)
    chat_history = serializers.ListField(
        child=serializers.DictField(), required=False, default=list
    )
