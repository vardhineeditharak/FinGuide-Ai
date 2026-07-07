import os
import traceback
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

from rag_pipeline import answer_query

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)
        user_message = (data.get("message") or "").strip()

        if not user_message:
            return jsonify({"error": "Empty message"}), 400

        result = answer_query(user_message)

        return jsonify({
            "answer": result["answer"],
            "sources": result["sources"],
            "demo_mode": result["used_fallback"],
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "error": f"Internal error: {type(e).__name__}: {str(e)}"
        }), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
