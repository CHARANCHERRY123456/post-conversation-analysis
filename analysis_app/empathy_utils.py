from typing import List, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np


_EMOTION_MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"

_emotion_tokenizer = AutoTokenizer.from_pretrained(_EMOTION_MODEL_NAME)
_emotion_model = AutoModelForSequenceClassification.from_pretrained(_EMOTION_MODEL_NAME)


def compute_empathy_score(dialogue_pairs: List[Tuple[str, str]]) -> tuple[float, str]:

    if not dialogue_pairs:
        return 0.0, "low"

    empathy_scores = []

    for user_msg, ai_msg in dialogue_pairs:
        if not user_msg.strip() or not ai_msg.strip():
            continue

        user_inputs = _emotion_tokenizer(user_msg, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            user_outputs = _emotion_model(**user_inputs)
        user_probs = torch.softmax(user_outputs.logits, dim=1)[0]
        user_emotion_conf = float(torch.max(user_probs).item())

        ai_inputs = _emotion_tokenizer(ai_msg, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            ai_outputs = _emotion_model(**ai_inputs)
        ai_probs = torch.softmax(ai_outputs.logits, dim=1)[0]
        
        emotion_similarity = float(torch.nn.functional.cosine_similarity(
            user_probs.unsqueeze(0), ai_probs.unsqueeze(0)
        ).item())
        
        empathy_score = (0.5 * emotion_similarity) + (0.5 * user_emotion_conf)
        empathy_scores.append(empathy_score)

    if not empathy_scores:
        return 0.0, "low"

    avg_score = sum(empathy_scores) / len(empathy_scores)

    label = "low"
    if avg_score >= 0.75:
        label = "high"
    elif avg_score >= 0.45:
        label = "medium"

    return round(avg_score, 3), label
