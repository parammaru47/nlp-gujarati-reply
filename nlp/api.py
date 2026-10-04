import sys
import json
import random
import joblib
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS

import __main__
from sklearn.base import BaseEstimator, TransformerMixin
from gensim.models import FastText
from gensim.utils import simple_preprocess

class MeanFastTextTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, model_path):
        self.model_path = model_path
        self.model = None
    def fit(self, X, y=None):
        if self.model is None:
            self.model = FastText.load(self.model_path)
        return self
    def transform(self, X):
        if self.model is None:
            self.model = FastText.load(self.model_path)
        vector_size = self.model.vector_size
        X_transformed = np.zeros((len(X), vector_size))
        for i, text in enumerate(X):
            tokens = simple_preprocess(text)
            valid_tokens = [word for word in tokens if word in self.model.wv.key_to_index]
            if valid_tokens:
                X_transformed[i] = np.mean([self.model.wv[word] for word in valid_tokens], axis=0)
            else:
                X_transformed[i] = np.zeros(vector_size)
        return X_transformed

__main__.MeanFastTextTransformer = MeanFastTextTransformer

app = Flask(__name__)
CORS(app)

BANK_PATH = "data/reply_bank.json"
MODEL_PATH = "data/dialogue_act_model_dense.joblib"

# 1. Fast-Fail Initialization (Module 4.5)
try:
    with open(BANK_PATH, "r", encoding="utf-8") as f:
        reply_bank = json.load(f)
    model = joblib.load(MODEL_PATH)
except Exception as e:
    sys.stderr.write(f"FATAL API INIT: {e}\n")
    sys.exit(1)

# Group template text bank by semantic class_id
bank_by_class = {}
for entry in reply_bank:
    cid = entry.get("class_id")
    if cid is not None:
        bank_by_class.setdefault(cid, []).append(entry["text"])

# 2. Policy Engine Mapping Matrix (Act -> [Slot 1, Slot 2, Slot 3])
POLICY_MATRIX = {
    "BINARY_QUESTION": [401, 5, 7],       # Task Affirmation, Rejection, Deferral
    "OPEN_INQUIRY": [9, 8, 17],           # Status, Scheduling, Uncertainty
    "SOCIAL_SALUTATION": [102, 16, 301],  # Cultural Greeting, Wellbeing Inquiry, Neutral Reaction
    "WELLBEING_INQUIRY": [1601, 301, 102],# Affirmative Status, Neutral Reaction, Cultural Greeting
    "MILESTONE_NEWS": [14, 302, 1401],    # Celebration, Positive Reaction, Tease
    "ACTION_DIRECTIVE": [13, 401, 5],     # Action Commitment, Task Affirmation, Rejection
    "CLOSING_STATEMENT": [2, 301, 102]    # Gratitude/Close, Neutral Reaction, Cultural Greeting
}

OOD_THRESHOLD = 0.25
FALLBACK_CLASSES = [11, 17, 301] # Clarification, Uncertainty, Neutral Reaction

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(force=True)
    incoming_message = data.get("message", "").strip()

    if not incoming_message:
        return jsonify({"replies": [], "detected_act": "NONE"})

    # Stage 1: Dialogue Act Classification
    probs = model.predict_proba([incoming_message])[0]
    top_index = np.argmax(probs)
    top_prob = probs[top_index]
    detected_act = model.classes_[top_index]

    # Gatekeeper: Route Out-Of-Domain gibberish to safe fallbacks
    if top_prob < OOD_THRESHOLD:
        target_classes = FALLBACK_CLASSES
        detected_act = "OUT_OF_DOMAIN"
    else:
        target_classes = POLICY_MATRIX.get(detected_act, FALLBACK_CLASSES)

    # Stage 2: Slot Population
    replies = []
    used_texts = set()

    for cls_id in target_classes:
        candidates = bank_by_class.get(cls_id, [])
        # Shuffle candidates and pick one not already used
        random.shuffle(candidates)
        for text in candidates:
            if text not in used_texts:
                replies.append(text)
                used_texts.add(text)
                break

    # Guardrail: Ensure exactly 3 replies if class populations are sparse
    if len(replies) < 3:
        neutral_pool = bank_by_class.get(301, []) + bank_by_class.get(2, [])
        random.shuffle(neutral_pool)
        for text in neutral_pool:
            if text not in used_texts:
                replies.append(text)
                used_texts.add(text)
            if len(replies) == 3:
                break

    # Frontend contract expects a flat array for the 3 buttons
    return jsonify({
        "replies": replies[:3],
        "debug": {
            "detected_act": detected_act,
            "confidence": float(top_prob)
        }
    })

if __name__ == "__main__":
    app.run(port=5000, debug=False)
