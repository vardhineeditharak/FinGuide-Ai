import os
import traceback
import json
from flask import Flask, request, jsonify, render_template, Response
from dotenv import load_dotenv

from rag_pipeline import answer_query_stream

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
        history = data.get("history") or []

        if not user_message:
            return jsonify({"error": "Empty message"}), 400

        def generate():
            try:
                for event in answer_query_stream(user_message, history):
                    yield f"data: {json.dumps(event)}\n\n"
            except Exception as ex:
                yield f"data: {json.dumps({'type': 'error', 'error': str(ex)})}\n\n"

        return Response(generate(), mimetype="text/event-stream")

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "error": f"Internal error: {type(e).__name__}: {str(e)}"
        }), 500


@app.route("/api/feedback", methods=["POST"])
def feedback():
    try:
        data = request.get_json(force=True)
        query = data.get("query")
        answer = data.get("answer")
        rating = data.get("rating")

        if not (query and answer and rating):
            return jsonify({"error": "Missing required fields"}), 400

        if rating not in ["up", "down"]:
            return jsonify({"error": "Invalid rating"}), 400

        import sqlite3
        from rag_pipeline import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO feedback (query, answer, rating) VALUES (?, ?, ?);",
            (query, answer, rating)
        )
        conn.commit()
        conn.close()

        return jsonify({"status": "success"}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

