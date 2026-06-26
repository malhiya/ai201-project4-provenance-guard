import uuid
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

import analyzer  
import database  

app = Flask(__name__)
database.init_db()

@app.route("/submit", methods=["POST"])
def submit():
    """
    POST /submit
    Ingests text content, fires the multi-signal detection pipeline, 
    calibrates thresholds, writes to the persistent audit log ledger,
    and returns the structured data contract payload.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid payload format. Expected a JSON map object."}), 400

    text_field = data.get("text")
    creator_id_field = data.get("creator_id")

    # Defensive boundary validation checks
    if not text_field or not isinstance(text_field, str):
        return jsonify({"error": "Missing or invalid required field: 'text' must be a non-empty string."}), 400
    if not creator_id_field or not isinstance(creator_id_field, str):
        return jsonify({"error": "Missing or invalid required field: 'creator_id' must be a non-empty string."}), 400

    # A. Generate tracking ID
    content_id = str(uuid.uuid4())

    # B. Execute the multi-signal detection pipeline
    s1_llm_score = analyzer.analyze_llm_attribution(text_field)
    s2_sty_score = analyzer.analyze_stylometric_heuristics(text_field)

    # C. Run Combination Strategy Engineering math
    final_confidence = analyzer.calculate_combined_confidence(s1_llm_score, s2_sty_score)

    # D. Calibrate the output to your specification thresholds
    if final_confidence >= 0.70:
        attribution = "likely_ai"
    elif final_confidence <= 0.40:
        attribution = "likely_human"
    else:
        attribution = "uncertain"

    status = "classified"

    # E. Commit the transaction parameters into the persistent database log
    try:
        database.write_log_entry(
            content_id=content_id,
            creator_id=creator_id_field,
            text_content=text_field,
            attribution=attribution,
            confidence=final_confidence,     # Unified weighted score
            llm_score=s1_llm_score,          # Preserving individual Signal 1 tracking
            status=status
        )
    except Exception as e:
        return jsonify({"error": f"Internal audit log storage failure: {str(e)}"}), 500

    # F. Construct standard API Response Payload
    response_payload = {
        "content_id": content_id,
        "attribution": attribution,
        "confidence": final_confidence,
        "label": f"Pipeline analysis complete. Combined probability: {final_confidence}. (Signal 1: {s1_llm_score}, Signal 2: {s2_sty_score}).",
        "status": status
    }

    return jsonify(response_payload), 200


@app.route("/log", methods=["GET"])
def get_log():
    """
    GET /log
    Surfaces audit trailing arrays back for validation and documentation.
    """
    try:
        logs = database.read_all_logs()
        return jsonify({"entries": logs}), 200
    except Exception as e:
        return jsonify({"error": f"Database read transaction failure: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)