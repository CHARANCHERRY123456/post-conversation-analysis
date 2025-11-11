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
        return 0
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
    avg_clarity =  np.mean(claritites) if claritites else 0
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
    
    # Convert pairs to list if it's an iterator
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
    if not ai_msgs: return 0.0, "low"
    clf = pipeline("text-classification", model="roberta-large-mnli")
    probs = [clf(f"This message shows uncertainty: {m}")[0]['score'] for m in ai_msgs]
    freq = np.mean(probs)
    lbl = "low" if freq <= 0.1 else "medium" if freq <= 0.3 else "high"
    return round(freq, 3), lbl

def compute_resolution_rate(pairs):
    if not pairs:return 0.0
    clf = pipeline("text-classification", model="roberta-large-mnli")
    embed = SentenceTransformer("all-MiniLM-L6-v2")
    scores = []
    for u,a in pairs:
        u_vec,a_vec = embed.encode(u), embed.encode(a)
        similarity = 1 - cosine(u_vec , a_vec)
        prob = clf(f"User request: {u} AI reply: {a}. Does the AI resolve the user's request?")[0]['score']
        combined = (0.5 * similarity) + (0.5 * prob)
        scores.append(combined)
    avg_score = sum(scores) / len(scores)
    return round(avg_score,3)

def compute_escalation_need(sentiment_score, completeness_score, accuracy_score, fallback_freq, resolution_score):
    neg = 1 - sentiment_score
    uncomplete = 1 - completeness_score
    inaccurate = 1 - accuracy_score
    unresolved = 1 - resolution_score
    score = np.mean([neg, uncomplete, inaccurate, fallback_freq, unresolved])
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
    avg = np.mean(diffs) if diffs else 0.0
    lbl = "fast" if avg <= 2 else "moderate" if avg <= 5 else "slow"
    return round(avg, 2), lbl

def compute_user_satisfaction(pairs):
    if not pairs: return 0.0, "low"
    text = " ".join([f"User: {u} AI: {a}" for u, a in pairs])
    clf = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    result = clf(text, candidate_labels=["user is satisfied", "user is unsatisfied"])
    score = result["scores"][0]
    lbl = "high" if score >= 0.75 else "medium" if score >= 0.45 else "low"
    return round(score, 3), lbl
