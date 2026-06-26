import uuid
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load system environment variables 
load_dotenv()

# Import your local modules
import analyzer  
import database  

app = Flask(__name__)

# Automatically ensure the database table is ready when Flask boots up
database.init_db()

@app.route("/submit", methods=["POST"])
def submit():
    """
    POST /submit
    Ingests text, runs Signal 1 analysis, commits a structured entry to the 
    audit log database, and returns the result.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid payload format. Expected a JSON map object."}), 400

    text_field = data.get("text")
    creator_id_field = data.get("creator_id")

    # Defensive validation boundaries
    if not text_field or not isinstance(text_field, str):
        return jsonify({"error": "Missing or invalid required field: 'text' must be a non-empty string."}), 400
    if not creator_id_field or not isinstance(creator_id_field, str):
        return jsonify({"error": "Missing or invalid required field: 'creator_id' must be a non-empty string."}), 400

    # A. Generate tracking ID
    content_id = str(uuid.uuid4())

    # B. Execute live Signal 1 analysis
    llm_score = analyzer.analyze_llm_attribution(text_field)

    # C. Map raw score to thresholds
    if llm_score >= 0.70:
        attribution = "likely_ai"
    elif llm_score <= 0.40:
        attribution = "likely_human"
    else:
        attribution = "uncertain"

    # For Milestone 3, confidence matches our raw signal 1 score
    confidence = llm_score
    status = "classified"

    # D. WRITE TO AUDIT LOG (SQLite Database)
    try:
        database.write_log_entry(
            content_id=content_id,
            creator_id=creator_id_field,
            text_content=text_field,
            attribution=attribution,
            confidence=confidence,
            llm_score=llm_score,
            status=status
        )
    except Exception as e:
        return jsonify({"error": f"Internal audit log storage failure: {str(e)}"}), 500

    # E. Compile response payload matching data contract
    response_payload = {
        "content_id": content_id,
        "attribution": attribution,
        "confidence": confidence,
        "label": f"Signal 1 Analysis complete. System analyzed pattern predictability as {llm_score}.",
        "status": status
    }

    return jsonify(response_payload), 200


@app.route("/log", methods=["GET"])
def get_log():
    """
    GET /log
    Reads all historical structured records from the SQLite database ledger 
    and returns them as a JSON array sorted from newest to oldest.
    """
    try:
        # Fetch the array of row dictionaries from database.py
        logs = database.read_all_logs()
        return jsonify({"entries": logs}), 200
    except Exception as e:
        return jsonify({"error": f"Database read transaction failure: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)