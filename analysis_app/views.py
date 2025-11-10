from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
import json
from .serializers import ConversationUploadSerializer , ConversationSerializer
# we will get the json in the req.body
@api_view(['POST','GET'])
def upload_json(req):
    serializer = ConversationUploadSerializer(data=req.data)
    if serializer.is_valid():
        conversation = serializer.save()
        res_data = ConversationSerializer(conversation).data
        res_data["message_count"] = conversation.messages.count()
        res_data["messages"] = conversation.messages.all().values("sender","message","timestamp")
        return Response(res_data , status=201)
    return Response(serializer.errors , status=400)
    
