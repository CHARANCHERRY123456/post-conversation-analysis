from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .utils import analyze_sentiment , compute_relavance_score,compute_clarity,compute_completeness
from .gemini_utils import compute_accuracy_score
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
    
@api_view(['GET' , 'POST'])
def analyse_chat(request, conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id)
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

    messages = Message.objects.filter(conversation_id=conversation.id).values("sender", "message", "timestamp")
    messages_list = list([message for message in messages if message['message'].strip() != ""])
    user_messages = [msg for msg in messages_list if msg['sender'] == 'user']
    ai_messages = [msg for msg in messages_list if msg['sender'] == 'ai']

    if not user_messages or not ai_messages:
        return Response({"error": "Insufficient data for analysis"}, status=status.HTTP_400_BAD_REQUEST)
    
    pairs = zip([msg["message"] for msg in user_messages], [msg["message"] for msg in ai_messages])
    sentement_count , sentiment = analyze_sentiment(user_messages)
    relevance_score , relevance_label = compute_relavance_score(pairs)
    clarity_score , clarity_label = compute_clarity(ai_messages)
    completeness_score , completeness_label = compute_completeness(pairs)
    accuracy_score , accuracy_label = compute_accuracy_score(pairs)

    return Response({
        "sentiment_score" : sentement_count,
        "sentiment_label" : sentiment,
        "relevance_score" : relevance_score,
        "relavance_label" : relevance_label,
        "clarity_score" : clarity_score,
        "clarity_label" : clarity_label,
        "completeness_score" : completeness_score,
        "completeness_label" : completeness_label,
        "accuracy_score" : accuracy_score,
        "accuracy_label" : accuracy_label
    })

