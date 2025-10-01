from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Rasa server URL (make sure Rasa is running: `rasa run --enable-api --cors "*"`)
RASA_URL = "http://localhost:5005/webhooks/rest/webhook"

def get_rasa_response(message, sender="user1"):
    payload = {"sender": sender, "message": message}
    try:
        response = requests.post(RASA_URL, json=payload)
        data = response.json()
        if data and "text" in data[0]:
            return data[0]["text"]
    except Exception as e:
        print("⚠️ Rasa error:", e)
    return "Sorry, I couldn’t get a response from Rasa."

@app.route("/")
def index():
    return render_template("rasa.html")

@app.route("/get", methods=["POST"])
def chat():
    user_msg = request.json.get("message")
    bot_response = get_rasa_response(user_msg)
    return jsonify({"response": bot_response})

if __name__ == "__main__":
    app.run(debug=True)
