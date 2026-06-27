import uuid
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

import analyzer  
import database  

app = Flask(__name__)
database.init_db()

# Initialize Flask-Limiter using the required local in-memory storage context
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://"
)

@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute;100 per day") # Our defensible production tier limits
def submit():
    data = request.get_json(silent=True)
    if not data or "text" not in data or "creator_id" not in data:
        return jsonify({"error": "Missing required fields: text and creator_id are mandatory."}), 400

    text_field = data["text"]
    creator_id_field = data["creator_id"]
    content_id = str(uuid.uuid4())

    # Execute Pipeline & Label Mapping
    s1_llm_score = analyzer.analyze_llm_attribution(text_field)
    s2_sty_score = analyzer.analyze_stylometric_heuristics(text_field)
    final_confidence = analyzer.calculate_combined_confidence(s1_llm_score, s2_sty_score)

    label_package = analyzer.generate_transparency_label(final_confidence)
    attribution = label_package["attribution"]
    label_text = label_package["label"]
    status = "classified"

    try:
        database.write_log_entry(
            content_id=content_id,
            creator_id=creator_id_field,
            text_content=text_field,
            attribution=attribution,
            confidence=final_confidence,
            llm_score=s1_llm_score,
            stylometric_score=s2_sty_score,
            status=status
        )
    except Exception as e:
        return jsonify({"error": f"Database write error: {str(e)}"}), 500

    return jsonify({
        "content_id": content_id,
        "attribution": attribution,
        "confidence": final_confidence,
        "label": label_text,
        "status": status
    }), 200


@app.route("/appeal", methods=["POST"])
def appeal():
    data = request.get_json(silent=True)
    if not data or "content_id" not in data or "creator_reasoning" not in data:
        return jsonify({"error": "Missing required fields."}), 400

    content_id = data["content_id"]
    reasoning = data["creator_reasoning"]

    if len(reasoning) < 10 or len(reasoning) > 500:
        return jsonify({"error": "Reasoning statement must be between 10 and 500 characters."}), 400

    record = database.get_log_by_id(content_id)
    if not record:
        return jsonify({"error": "Submission ID not found."}), 404

    if record["status"] == "under_review":
        return jsonify({"error": "Conflict: This submission has already been appealed."}), 409

    try:
        database.update_to_under_review(content_id, reasoning)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "message": "Appeal successfully accepted.",
        "content_id": content_id,
        "status": "under_review"
    }), 200


@app.route("/log", methods=["GET"])
def get_log():
    try:
        return jsonify({"entries": database.read_all_logs()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)