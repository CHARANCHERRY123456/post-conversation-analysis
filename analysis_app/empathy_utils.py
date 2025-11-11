from typing import List, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np


_EMOTION_MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"
_EMPATHY_MODEL_NAME = "bhadresh-savani/empathetic-dialogues-roberta"

_emotion_tokenizer = AutoTokenizer.from_pretrained(_EMOTION_MODEL_NAME)
_emotion_model = AutoModelForSequenceClassification.from_pretrained(_EMOTION_MODEL_NAME)

_empathy_tokenizer = AutoTokenizer.from_pretrained(_EMPATHY_MODEL_NAME)
_empathy_model = AutoModelForSequenceClassification.from_pretrained(_EMPATHY_MODEL_NAME)


def compute_empathy_score(dialogue_pairs: List[Tuple[str, str]]) -> tuple[float, str]:

    if not dialogue_pairs:
        return 0.0, "low"

    empathy_scores = []

    for user_msg, ai_msg in dialogue_pairs:
        if not user_msg.strip() or not ai_msg.strip():
            continue

        # 1️ Predict user's emotion distribution
        user_inputs = _emotion_tokenizer(user_msg, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            user_outputs = _emotion_model(**user_inputs)
        user_probs = torch.softmax(user_outputs.logits, dim=1)[0]
        user_emotion_idx = int(torch.argmax(user_probs))
        user_emotion_conf = user_probs[user_emotion_idx].item()

        # Predict AI's empathy level 
        combined_text = f"User: {user_msg} AI: {ai_msg}"
        empathy_inputs = _empathy_tokenizer(combined_text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            empathy_outputs = _empathy_model(**empathy_inputs)
        empathy_probs = torch.softmax(empathy_outputs.logits, dim=1)[0]
        
        ai_empathy_prob = empathy_probs[1].item() if empathy_probs.shape[-1] > 1 else empathy_probs[0].item()

        alignment = 1.0 - abs(0.5 - user_emotion_conf)  

        final_score = (0.6 * ai_empathy_prob) + (0.4 * alignment)
        empathy_scores.append(final_score)

    if not empathy_scores:
        return 0.0, "low"

    avg_score = float(np.mean(empathy_scores))

    label = "low"
    if avg_score >= 0.75:
        label = "high"
    elif avg_score >= 0.45:
        label = "medium"

    return round(avg_score, 3), label
