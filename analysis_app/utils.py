from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import textstat
from datetime import datetime
from scipy.spatial.distance import cosine
import numpy as np
import spacy

nlp = spacy.load("en_core_web_sm")
model = SentenceTransformer('all-MiniLM-L6-v2')

def _normalize(value: float, min_val: float = 0, max_val: float = 1) -> float:
    """
    normalizes a value between min_val and max_val to a 0-1 scale
    """
    if min_val == max_val:
        return 0.0
    val = max(min_val, min(max_val, value))
    norm = (val - min_val) / (max_val - min_val)
    return round(norm, 3)

def compute_relavance_score(pairs):
    similarities = []
    for umsg , aimsg in pairs:
        umsg_emb = model.encode(umsg)
        aimsg_emb = model.encode(aimsg)
        similarity = 1 - cosine(umsg_emb , aimsg_emb)
        similarities.append(similarity)
    if not similarities:
        return 0.0, "low"
    avg_similarity = sum(similarities) / len(similarities)
    label = "low"
    if avg_similarity > 0.7:
        label = "high"
    elif avg_similarity > 0.4:
        label = "medium"
    return avg_similarity , label

def analyze_sentiment(messages):
    def get_sentiment_score(message):
        if not message or message.strip() == "":
            return 0
        vader_score = SentimentIntensityAnalyzer().polarity_scores(message)['compound']
        textblob_score = TextBlob(message).sentiment.polarity
        final = (0.7 * vader_score) + (0.3 * textblob_score)
        return final
    sentiments = [get_sentiment_score(message["message"]) for message in messages]
    if not sentiments:
        return 0, "neutral"
    avg_sentiment = sum(sentiments) / len(sentiments)

    label = "neutral"
    if avg_sentiment > 0.2:
        label = "positive"
    elif avg_sentiment < -0.2:
        label = "negative"
    return avg_sentiment , label
    
def compute_clarity(aimessages):
    claritites = []
    for message in aimessages:
        text = message["message"]
        if not text or text.strip() == "":
            continue
        clarity_score = textstat.flesch_reading_ease(text)
        claritites.append(_normalize(clarity_score,-100,121))
    avg_clarity = sum(claritites) / len(claritites) if claritites else 0
    label = "difficult"
    if avg_clarity >= 60:
        label = "clear"
    elif avg_clarity >= 30:
        label = "average"
    
    return avg_clarity , label

def compute_completeness(pairs):

    def extract_keyphrases(text):
        '''Extract nouns and verbs as key phrases'''
        doc = nlp(text)
        keyphrases = set()
        for chunk in doc.noun_chunks:
            keyphrases.add(chunk.root.text.lower())
        for token in doc:
            if token.pos_ in ['VERB', 'NOUN'] and not token.is_stop:
                keyphrases.add(token.text.lower())
        return keyphrases
    def keypoint_coverage(user_text, ai_text):
        user_keyphrases = extract_keyphrases(user_text)
        ai_keyphrases = extract_keyphrases(ai_text)
        if not user_keyphrases:
            return 0.0
        covered = user_keyphrases.intersection(ai_keyphrases)
        coverage = len(covered) / len(user_keyphrases)
        return coverage
    def semantic_relavance(user_text, ai_text):
        user_emb = model.encode(user_text)
        ai_emb = model.encode(ai_text)
        similarity = 1 - cosine(user_emb , ai_emb)
        return similarity
    def deapth_ratio(user_text, ai_text):
        user_sentences = len(list(nlp(user_text).sents))
        ai_sentences = len(list(nlp(ai_text).sents))
        if user_sentences == 0:
            return 0.0
        ratio = ai_sentences / user_sentences
        return min(ratio, 1.0)
    
    pairs_list = list(pairs) if not isinstance(pairs, list) else pairs
    
    if not pairs_list:
        return 0.0 , "incomplete"
    
    completeness_scores = []
    for umsg , aimsg in pairs_list:
        kp_coverage = keypoint_coverage(umsg, aimsg)
        sem_relavance = semantic_relavance(umsg, aimsg)
        depth_rat = deapth_ratio(umsg, aimsg)
        combined_score = (0.4 * kp_coverage) + (0.4 * sem_relavance) + (0.2 * depth_rat)
        completeness_scores.append(combined_score)
    
    if not completeness_scores:
        return 0.0, "incomplete"
    
    avg_completeness = sum(completeness_scores) / len(completeness_scores)
    label = "incomplete"
    if avg_completeness >= 0.7:
        label = "complete"
    elif avg_completeness >= 0.4:
        label = "partial"
    return avg_completeness , label

def compute_fallback_frequency(ai_msgs):
    if not ai_msgs: 
        return 0.0, "low"
    
    fallback_keywords = ['sorry', 'apologize', 'not sure', 'don\'t know', 'unclear', 'uncertain', 'maybe', 'perhaps', 'might']
    
    fallback_count = 0
    for msg in ai_msgs:
        text = msg.get('message', '').lower()
        if any(keyword in text for keyword in fallback_keywords):
            fallback_count += 1
    
    freq = fallback_count / len(ai_msgs) if ai_msgs else 0.0
    lbl = "low" if freq <= 0.1 else "medium" if freq <= 0.3 else "high"
    return round(freq, 3), lbl

def compute_resolution_rate(pairs):
    if not pairs:
        return 0.0
    
    embed = SentenceTransformer("all-MiniLM-L6-v2")
    scores = []
    for u, a in pairs:
        u_vec, a_vec = embed.encode(u), embed.encode(a)
        similarity = 1 - cosine(u_vec, a_vec)
        scores.append(similarity)
    
    avg_score = sum(scores) / len(scores)
    return round(avg_score, 3)

def compute_escalation_need(sentiment_score, completeness_score, accuracy_score, fallback_freq, resolution_score):
    neg = 1 - sentiment_score
    uncomplete = 1 - completeness_score
    inaccurate = 1 - accuracy_score
    unresolved = 1 - resolution_score
    score = (neg + uncomplete + inaccurate + fallback_freq + unresolved) / 5
    lbl = "low" if score <= 0.3 else "medium" if score <= 0.6 else "high"
    return round(score, 3), lbl

def compute_response_time(pairs):
    if not pairs: return 0.0, "no data"
    diffs = []
    for u, a in pairs:
        try:
            t1, t2 = datetime.fromisoformat(u["timestamp"]), datetime.fromisoformat(a["timestamp"])
            diffs.append((t2 - t1).total_seconds())
        except: continue
    avg = sum(diffs) / len(diffs) if diffs else 0.0
    lbl = "fast" if avg <= 2 else "moderate" if avg <= 5 else "slow"
    return round(avg, 2), lbl

def compute_user_satisfaction(pairs):
    if not pairs: 
        return 0.0, "low"
    
    analyzer = SentimentIntensityAnalyzer()
    satisfaction_scores = []
    
    for user_msg, ai_msg in pairs:
        user_sentiment = analyzer.polarity_scores(user_msg)['compound']
        ai_sentiment = analyzer.polarity_scores(ai_msg)['compound']
        
        response_quality = (ai_sentiment + 1) / 2  # Normalize to 0-1
        conversation_flow = 1 - abs(user_sentiment - ai_sentiment)
        
        satisfaction = (0.6 * response_quality) + (0.4 * conversation_flow)
        satisfaction_scores.append(satisfaction)
    
    score = sum(satisfaction_scores) / len(satisfaction_scores)
    lbl = "high" if score >= 0.75 else "medium" if score >= 0.45 else "low"
    return round(score, 3), lbl

def get_conversation_analysis(conversation):
    from .models import Message
    from .gemini_utils import compute_accuracy_score
    from .empathy_utils import compute_empathy_score
    
    messages = Message.objects.filter(conversation=conversation).values("sender", "message", "timestamp")
    messages_list = [message for message in messages if message['message'].strip() != ""]
    user_messages = [msg for msg in messages_list if msg['sender'] == 'user']
    ai_messages = [msg for msg in messages_list if msg['sender'] == 'ai']
    
    if not user_messages or not ai_messages:
        return None, {"error": "Insufficient data for analysis"}
    
    pairs = list(zip([msg["message"] for msg in user_messages], [msg["message"] for msg in ai_messages]))
    sentement_count, sentiment = analyze_sentiment(user_messages)
    relevance_score, relevance_label = compute_relavance_score(pairs)
    clarity_score, clarity_label = compute_clarity(ai_messages)
    completeness_score, completeness_label = compute_completeness(pairs)
    accuracy_score, accuracy_label = compute_accuracy_score(pairs)
    empathy_score, empathy_label = compute_empathy_score(pairs)
    fallback_freq, fallback_label = compute_fallback_frequency(ai_messages)
    resolution_rate = compute_resolution_rate(pairs)
    _, escalation_need = compute_escalation_need(sentement_count, completeness_score, accuracy_score, fallback_freq, resolution_rate)
    response_time, response_label = compute_response_time(zip(user_messages, ai_messages))
    user_satisfaction_score, user_satisfaction_label = compute_user_satisfaction(pairs)

    analytics_data = {
        "clarity": clarity_score,
        "relevance": relevance_score,
        "accuracy": accuracy_score,
        "completeness": completeness_score,
        "sentiment": sentiment,
        "empathy": empathy_score,
        "fallback_count": fallback_freq,
        "resolution": bool(resolution_rate),
        "escalation": bool(escalation_need),
        "response_time": response_time,
        "overall_score": user_satisfaction_score,
    }
    
    api_response = {
        "analytics": analytics_data,
        "sentiment_score": sentement_count,
        "sentiment_label": sentiment,
        "relevance_score": relevance_score,
        "relevance_label": relevance_label,
        "clarity_score": clarity_score,
        "clarity_label": clarity_label,
        "completeness_score": completeness_score,
        "completeness_label": completeness_label,
        "accuracy_score": accuracy_score,
        "accuracy_label": accuracy_label,
        "empathy_score": empathy_score,
        "empathy_label": empathy_label,
        "fallback_frequency": fallback_freq,
        "fallback_label": fallback_label,
        "resolution_rate": resolution_rate,
        "escalation_need": escalation_need,
        "response_time": response_time,
        "response_label": response_label,
        "user_satisfaction_score": user_satisfaction_score,
        "user_satisfaction_label": user_satisfaction_label
    }
    
    return analytics_data, api_response

