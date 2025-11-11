import google.generativeai as genai
import os
import json
import re

api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.0-flash")


def compute_accuracy_score(pairs):
    pairs_list = list(pairs) if not isinstance(pairs, list) else pairs
    if not pairs_list:
        return 0.0, "inaccurate"
    
    conversation = "\n\n".join([f"User: {u}\nAI: {a}" for u, a in pairs_list])
    prompt = f"""Rate AI accuracy (0-1) in this conversation:\n\n{conversation}\n\nRespond as JSON: {{"score": 0.8, "label": "accurate"}}"""
    
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'\{.*?\}', response.text, re.DOTALL)
        
        if json_match:
            data = json.loads(json_match.group())
            score = max(0.0, min(1.0, float(data.get("score", 0))))
            label = data.get("label", "inaccurate").lower()
            return round(score, 3), label
        
        return 0.0, "inaccurate"
    
    except Exception as e:
        print(f"Gemini error: {e}")
        return 0.0, "inaccurate"