from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
from sentence_transformers import SentenceTransformer
import textstat
from scipy.spatial.distance import cosine
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

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
        claritites.append(clarity_score)
    avg_clarity =  np.mean(claritites) if claritites else 0
    label = "difficult"
    if avg_clarity >= 60:
        label = "clear"
    elif avg_clarity >= 30:
        label = "average"
    
    return avg_clarity , label