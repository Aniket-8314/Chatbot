import os
import ssl
import json
import random
import numpy as np
import requests
from flask import Flask, render_template, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import nltk

# ==== CONFIG ====
WIT_API_KEY = "OEZZBKTD7P6S6QSJYXYYPXLHKYEPLZ7R"
WIT_URL = "https://api.wit.ai/message"
RASA_URL = "http://localhost:5005/webhooks/rest/webhook"
nltk.data.path.append(os.path.abspath("nltk_data"))
ssl._create_default_https_context = ssl._create_unverified_context
nltk.download('punkt')

# ==== Load intents ====
with open("intents.json", encoding="utf-8") as f:
    data = json.load(f)
    intents = data["intents"]

vectorizer = TfidfVectorizer()
clf = LogisticRegression(random_state=0, max_iter=10000)

tags, patterns = [], []
for intent in intents:
    for pattern in intent["patterns"]:
        tags.append(intent["tag"])
        patterns.append(pattern)

X = vectorizer.fit_transform(patterns)
y = tags
clf.fit(X, y)

# ==== Local chatbot (intents.json) ====
def chatbot_response(input_text, threshold=0.75):
    x_test = vectorizer.transform([input_text])
    probs = clf.predict_proba(x_test)[0]
    max_prob = max(probs)
    predicted_tag = clf.classes_[probs.argmax()]

    # if max_prob < threshold:
    #     return None   # low confidence → fallback

    for intent in intents:
        if intent["tag"] == predicted_tag:
            return random.choice(intent["responses"])
    return None

# ==== Wikipedia ====
def get_wikipedia_summary(query):
    try:
        # Search query
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {"action": "query", "list": "search", "srsearch": query, "format": "json"}
        resp = requests.get(search_url, params=params, headers={"User-Agent": "Chatbot/1.0"})
        data = resp.json()

        if "query" in data and data["query"]["search"]:
            title = data["query"]["search"][0]["title"]

            # Fetch summary
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
            summary_resp = requests.get(summary_url, headers={"User-Agent": "Chatbot/1.0"})
            summary_data = summary_resp.json()
            if "extract" in summary_data:
                return f"According to the 📖 Wikipedia: {summary_data['extract']}"
        return "Sorry, I couldn't find anything on Wikipedia."
    except Exception as e:
        return f"Error fetching Wikipedia: {e}"

wikiped = ["Let me check Wikipedia for you 📖",
        "Here’s what I found about that topic..."]

# ==== Flask App ====
chatbot = Flask(__name__)

@chatbot.route("/")
def index():
    return render_template("cbt.html")

@chatbot.route("/get", methods=["POST"])
def get_response():
    user_msg = request.json.get("message")

    # Step 1: Try local intents (with confidence check)
    response = chatbot_response(user_msg)
    if response:
        if response in wikiped:
            try:
                summary = get_wikipedia_summary(user_msg)
                return jsonify({"response": summary})
            except:
                pass
        else:
            return jsonify({"response": response})
    
    # Step 2: Fallback → Wikipedia
    try:
        summary = get_wikipedia_summary(user_msg)
        return jsonify({"response": summary})
    except:
        pass

    return jsonify({"response": "Sorry, I couldn’t understand that."})



if __name__ == "__main__":
    chatbot.run(debug=True)
