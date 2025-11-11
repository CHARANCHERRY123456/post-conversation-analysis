# All imports at the top
from .models import Conversation, ConversationAnalysis
from .utils import get_conversation_analysis


def run_daily_analysis():
    conversations = Conversation.objects.all()
    for conversation in conversations:
        analytics_data, _ = get_conversation_analysis(conversation)
        
        if analytics_data is None:
            continue
        
        # Store / update the analysis record
        ConversationAnalysis.objects.update_or_create(
            conversation=conversation,
            defaults=analytics_data
        )
