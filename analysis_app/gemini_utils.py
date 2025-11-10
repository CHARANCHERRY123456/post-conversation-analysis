import google.generativeai as genai
import numpy as np
import os
import json
import re

api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
if not api_key:
    print("Gemini API key is not getting with .env")
else:
    genai.configure(api_key=api_key)

MODEL_NAME = "gemini-2.0-flash"


def compute_accuracy_score(pairs):
    """
    Compute accuracy score for AI responses using Gemini API.
    Returns: (score: float, label: str)
    """
    # Convert pairs to list if it's an iterator
    pairs_list = list(pairs) if not isinstance(pairs, list) else pairs
    
    if not pairs_list:
        return 0.0, "inaccurate"
    
    model = genai.GenerativeModel(MODEL_NAME)
    
    # Format the conversation for better readability
    conversation_text = ""
    for i, (user_msg, ai_msg) in enumerate(pairs_list, 1):
        conversation_text += f"Turn {i}:\nUser: {user_msg}\nAI: {ai_msg}\n\n"
    
    prompt = f"""You are an expert evaluator for AI factual correctness.
        Below is a full chat conversation between a human and an AI assistant.

        Conversation:
        {conversation_text}

        Your task:
        1. Carefully read the entire conversation.
        2. Judge how factually correct the AI's responses are overall.
        3. Return a single numeric factual accuracy score between 0 and 1:
        - 1.0 → fully accurate and truthful
        - 0.5 → partially accurate or somewhat vague
        - 0.0 → mostly inaccurate or hallucinated
        4. Provide a label: "accurate", "partially accurate", or "inaccurate".

        Respond ONLY in valid JSON format:
        {{
        "score": <float between 0 and 1>,
        "label": "<accurate|partially accurate|inaccurate>"
        }}
    """
    
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        
        # Try to extract JSON from the response (handle markdown code blocks)
        json_match = re.search(r'\{[^}]+\}', raw_text)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
            score = float(data.get("score", 0))
            label = data.get("label", "inaccurate").lower()
            
            # Normalize score to 0-1 range
            score = max(0.0, min(1.0, score))
            
            # Map label to our format
            if "accurate" in label and "partially" not in label and "in" not in label:
                label = "accurate"
            elif "partially" in label:
                label = "partially accurate"
            else:
                label = "inaccurate"
            
            return round(score, 3), label
        else:
            try:
                score = float(raw_text)
                score = max(0.0, min(1.0, score))
                label = "inaccurate"
                if score >= 0.7:
                    label = "accurate"
                elif score >= 0.4:
                    label = "partially accurate"
                return round(score, 3), label
            except ValueError:
                print(f"Could not parse Gemini response: {raw_text}")
                return 0.0, "inaccurate"
    
    except Exception as e:
        print(f"Error generating content from Gemini: {e}")
        return 0.0, "inaccurate"