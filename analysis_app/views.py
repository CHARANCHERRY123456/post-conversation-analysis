from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Conversation , Message
import json
from .serializers import ConversationUploadSerializer , ConversationSerializer
# we will get the json in the req.body
@api_view(['POST','GET'])
def upload_json(req):
    if req.method == 'GET':
        conversations = ConversationSerializer(Conversation.objects.all() , many=True).data
        res_data = []
        for conversation in conversations:
            conversation["message_count"] = Message.objects.filter(conversation_id=conversation["id"]).count()
            conversation["messages"] = Message.objects.filter(conversation_id=conversation["id"]).values("sender","message","timestamp")
            res_data.append(conversation)
        return Response(res_data , status=200)
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
    
