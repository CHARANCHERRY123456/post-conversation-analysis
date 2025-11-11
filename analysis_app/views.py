from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .utils import get_conversation_analysis
from .models import Conversation, Message, ConversationAnalysis
from .serializers import ConversationUploadSerializer, ConversationSerializer, ConversationAnalysisSerializer

@api_view(['GET'])
def get_all_analyses(request):
    analyses = ConversationAnalysis.objects.select_related('conversation').all()
    serializer = ConversationAnalysisSerializer(analyses, many=True)
    return Response(serializer.data, status=200)


# we will get the json in the req.body
@api_view(['POST','GET'])
def upload_json(req):
    if req.method == 'GET':
        conversations = Conversation.objects.all()
        res_data = []
        for conversation in conversations:
            serialized = ConversationSerializer(conversation).data
            serialized["message_count"] = conversation.messages.count()
            serialized["messages"] = conversation.messages.all().values("sender", "message", "timestamp")
            res_data.append(serialized)
        return Response(res_data, status=200)
    elif req.method == 'POST':
        serializer = ConversationUploadSerializer(data=req.data)
        if serializer.is_valid():
            conversation = serializer.save()
            res_data = ConversationSerializer(conversation).data
            res_data["message_count"] = conversation.messages.count()
            res_data["messages"] = conversation.messages.all().values("sender","message","timestamp")
            return Response(res_data , status=201)
        return Response(serializer.errors , status=400)
    return Response({"error":"Invalid request method"} , status=405)
    
@api_view(['GET' , 'POST'])
def analyse_chat(request, conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        analytics_data, api_response = get_conversation_analysis(conversation)
        if analytics_data is None:
            return Response(api_response, status=status.HTTP_400_BAD_REQUEST)
        ConversationAnalysis.objects.update_or_create(
            conversation=conversation,
            defaults=analytics_data
        )
        return Response(api_response, status=status.HTTP_200_OK)
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

