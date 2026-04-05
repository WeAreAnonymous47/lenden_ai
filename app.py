from flask import Flask, render_template, request, jsonify
# from sales_bot import gemini_prompt
from newbot import gemini_prompt
app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    print("user_input: ", user_input)
    
    if not user_input:
        return jsonify({"reply": "No input received"})

    reply = gemini_prompt(user_input)
    print("reply: ", reply)

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True)