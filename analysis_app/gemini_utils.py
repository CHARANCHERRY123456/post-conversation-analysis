import google.generativeai as genai
import numpy as np
import os

genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))
MODEL_NAME = "gemini-1.5-pro"


def compute_accuracy_score(pairs):
    model = genai.GenerativeModel(MODEL_NAME)
    prompt = "charan"
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        try:
            score = float(raw_text)
            label = "low"
            if score >= 0.7:
                label = "high"
            elif score >= 0.4:
                label = "medium"
            return score, label
        except ValueError:
            print("Could not convert response to float:", raw_text)
            return 0, "low"

    except Exception as e:
        print("Error generating content:", e)
        return 0, "low"