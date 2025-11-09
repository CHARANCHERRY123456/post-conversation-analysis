from django.db import models

class Conversation(models.Model):
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Conversation {self.id}"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.CharField(max_length=20)  # 'user' or 'ai'
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.text[:40]}"


class ConversationAnalysis(models.Model):
    conversation = models.OneToOneField(
        Conversation, on_delete=models.CASCADE, related_name="analysis"
    )

    clarity = models.FloatField(default=0)
    relevance = models.FloatField(default=0)
    accuracy = models.FloatField(default=0)
    completeness = models.FloatField(default=0)
    sentiment = models.CharField(max_length=20, default="neutral")
    empathy = models.FloatField(default=0)
    fallback_count = models.IntegerField(default=0)
    resolution = models.BooleanField(default=False)
    escalation = models.BooleanField(default=False)
    response_time = models.FloatField(default=0)
    overall_score = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.conversation}"
    
