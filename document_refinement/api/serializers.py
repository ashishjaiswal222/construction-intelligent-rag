from rest_framework import serializers
from document_refinement.models import RefinedContent

class RefinedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefinedContent
        fields = '__all__'
