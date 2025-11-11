from rest_framework import serializers
from django.db import transaction
from .models import Conversation, Message, ConversationAnalysis

# Serializer for ConversationAnalysis
class ConversationAnalysisSerializer(serializers.ModelSerializer):
    conversation_id = serializers.IntegerField(source='conversation.id', read_only=True)
    conversation_title = serializers.CharField(source='conversation.title', read_only=True)

    class Meta:
        model = ConversationAnalysis
        fields = [
            'id', 'conversation_id', 'conversation_title', 'clarity', 'relevance', 'accuracy', 'completeness',
            'sentiment', 'empathy', 'fallback_count', 'resolution', 'escalation', 'response_time', 'overall_score', 'created_at'
        ]

class MessageSerializer(serializers.Serializer):
    sender = serializers.ChoiceField(choices=['user', 'ai'])
    message = serializers.CharField(max_length=500)
    timestamp = serializers.DateTimeField()

    def validate_sender(self, value):
        if value not in ['user', 'ai']:
            raise serializers.ValidationError("Sender must be either 'user' or 'ai'.")
        return value
    def validate_message(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message text cannot be empty.")
        return value
    
class ConversationUploadSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    messages = MessageSerializer(many=True)
    
    @transaction.atomic
    def create(self, validated_data):
        title = validated_data.get('title', '').strip()
        messages_data = validated_data.get('messages', [])

        # create Conversation 
        conversation = Conversation.objects.create(title=title)

        # preapre message objects
        message_objects = [
            Message(
                conversation=conversation,
                sender=message['sender'].lower(),
                message=message['message'].strip(),
                timestamp=message.get('timestamp')
            )
            for message in messages_data
        ]

        Message.objects.bulk_create(message_objects)
        return conversation

class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at']

