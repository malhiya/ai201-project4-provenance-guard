# Planning Document - Provenance Guard

## Overview

Provenance Guard  analyzes submitted text and estimates whether it is more likely human-written or AI-generated. The system uses multiple detection signals instead of relying on a single method. It returns a classification result, a confidence score, and a transparency label that can be shown to readers. Every decision is recorded in an audit log for accountability. Creators can also appeal a classification if they believe the result is incorrect.

---

## Detection Signals

This system uses two complementary signals to estimate whether a piece of text is likely AI-generated or human-written. Each signal focuses on a different aspect of writing behavior, and their outputs are combined into a single confidence score.

---

### Signal 1: LLM-Based Attribution Analysis

This signal uses a large language model to evaluate how closely the text matches common AI-generated writing patterns. It analyzes higher-level properties such as tone consistency, structure, repetition, and predictability in phrasing.

AI-generated text often appears more uniform, structured, and statistically predictable. Human writing tends to be more varied, with irregular tone, pacing, and sentence construction.

**Output:**
- A probability score between **0 and 1**
- Interpretation:
  - 0.0 → very likely human-written
  - 1.0 → very likely AI-generated

---

### Signal 2: Stylometric Heuristics

This signal uses statistical and linguistic features of the text to detect writing patterns. It does not rely on meaning or semantics, only measurable properties of the text.

It evaluates features such as:
- Sentence length variation
- Vocabulary diversity (lexical richness)
- Punctuation usage and distribution
- Structural consistency
- Repetition patterns (light-weight measurement only within stylometric scope)

Human writing typically shows more variability across these features, while AI-generated writing tends to be more uniform and evenly distributed.

**Output:**
- A normalized score between **0 and 1**
- Interpretation:
  - 0.0 → strongly human-like patterns
  - 1.0 → strongly AI-like patterns

---

## Signal Combination Strategy

The final confidence score is computed by combining both signals using a weighted average.

### Default Weights:
- LLM-Based Attribution Analysis → **65%**
- Stylometric Heuristics → **35%**

### Formula:
```python
final_score = (
    0.65 * llm_score +
    0.35 * stylometric_score
)
```
---

## Score Calibration & Uncertainty Mapping

The final combined score (ranging from 0.0 to 1.0) measures the system's estimated probability that the text is AI-generated. This score is mapped into three distinct classification zones using established thresholds.

### Classification Thresholds
* **0.00 to 0.40:** Likely Human Written
* **0.41 to 0.69:** Uncertain / Inconclusive
* **0.70 to 1.00:** Likely AI-Generated

### Calibration and Interpretation
* **A score of 0.60:** This indicates a weak, inconclusive signal. The system detects a mix of human-like stylometric variance alongside some structural pattern regularities typical of an LLM, meaning it cannot confidently assign authorship to either category.
* **Edge Case Handling:** Raw outputs from Signal 1 (LLM) and Signal 2 (Stylometrics) are min-max normalized to ensure they map perfectly to a `[0.0, 1.0]` range before entering the weighted average formula, avoiding skew from uncalibrated raw data.

---

## Transparency Label Design

The system maps the final combined confidence score to a distinct user-facing label. The confidence value returned to the UI represents the system's certainty *within that specific classification*.

### 1. High-Confidence AI-Generated
* **Trigger Condition:** Final Score $\ge$ 0.70
* **Confidence Calculation:** `confidence = final_score`
* **Exact Label Text:**
    >  **Automated Content Detected** > Our system has high confidence ($CONFIDENCE_PERCENT%) that this text matches patterns consistent with AI-generated writing.

### 2. High-Confidence Human-Written
* **Trigger Condition:** Final Score $\le$ 0.40
* **Confidence Calculation:** `confidence = 1.0 - final_score`
* **Exact Label Text:**
    >  **Verified Human Author** > Our system has high confidence ($CONFIDENCE_PERCENT%) that this text exhibits patterns consistent with original human writing.

### 3. Uncertain / Inconclusive
* **Trigger Condition:** Final Score between 0.41 and 0.69
* **Confidence Calculation:** System forces `confidence = 0.50` (representing baseline ambiguity) or leaves it raw to show the exact point of overlap.
* **Exact Label Text:**
    >  **Inconclusive Authorship** > Our system detected a mix of original and automated writing patterns. We cannot definitively determine authorship for this submission.

---

## Appeals Workflow

The appeals system allows creators to contest an automated classification. This manual override pipeline transitions a content submission from an automated state to a human-audited state.

### 1. Actor and Submission Criteria
* **Who can appeal:** Only the creator or authorized user who submitted the original piece of content can initiate an appeal.
* **Prerequisites:** An appeal can only be submitted against an existing `submission_id` that has already completed processing and holds a status of `classified`. A submission can only be appealed once.

### 2. Information Required for an Appeal
When a creator appeals a decision, the platform's frontend automatically sends the `submission_id` behind the scenes (the user does not need to know or type this ID). 

The `POST /appeal` request body must include:
* `submission_id` (Integer): The unique ID returned by the system during the initial `/submit` request.
* `reason` (String): A required explanation from the creator (between 10 and 500 characters) explaining why the classification is wrong.

### 3. System Processing and Data Mutations
Upon receiving a valid appeal request, the backend immediately executes the following synchronized updates:
* **State Mutation:** The content submission's lifecycle status in the main database transitions from `classified` to `under_review`.
* **Audit Logging:** An `appeal` event is appended to the structural Audit Log. This entry captures the timestamp, the original `submission_id`, the user-provided `reason`, and the state transition.
* **Immutable Scores:** The raw scores (`llm_score`, `stylometric_score`, `final_score`) and the original transparency label are **never** altered or deleted during an appeal; they remain preserved in the record for audit stability.

### 4. Human Reviewer Queue Specifications
When an administrator or human moderator opens the system's review queue, they must be presented with a comprehensive dashboard containing:
* **Disputed Text Content:** The raw text that was originally analyzed.
* **System Breakdown:** The calculated `final_score` alongside the individual breakdown of the signals used (e.g., exactly what the LLM scored versus what the stylometric metrics scored).
* **Creator Defenses:** The full text statement provided by the author explaining their creative origin.
* **Contextual Audit Timeline:** A sequential log showing exactly when the piece was submitted, when it was flagged, and the precise moment the appeal was logged.

---

## Anticipated Edge Cases

While the multi-signal pipeline improves overall accuracy, certain writing styles natively mimic either AI uniformity or human randomness, causing the system to handle them poorly. 

### 1. Highly Structured Traditional Poetry (Potential False AI Flag)
* **The Scenario:** A human writes a poem following a rigid, traditional structure (like a Shakespearean sonnet or a villanelle) that uses heavy repetition, perfect internal rhyme schemes, and highly predictable line lengths.
* **Why it fails:** Signal 2 (Stylometrics) will measure near-zero variation in sentence/line length and a highly uniform punctuation distribution. Because the structural metrics look completely standardized and mathematically neat, the heuristics will score it heavily as AI-generated, forcing the final score into the "Uncertain" or "Likely AI" zone despite being an original human work.

### 2. High-Density Technical or Instructional Documentation (Potential False AI Flag)
* **The Scenario:** A human writes a step-by-step software installation guide, a recipe, or a medical standard operating procedure using clear, concise, and professional language.
* **Why it fails:** Signal 1 (LLM Analysis) looks for tone consistency, lack of emotional variation, and predictable phrasing. Because technical writing *demands* maximum predictability and a dry, uniform tone, the text inherently matches the statistical patterns of an AI model trained on documentation. This can trigger an artificially high LLM score.

### 3. Deliberately Fragmented Stream-of-Consciousness Prose (Potential Evasion)
* **The Scenario:** An AI is explicitly prompted to write a chaotic, fragmented narrative with intentional grammatical errors, random run-on sentences, and erratic punctuation to mimic a high-emotion human journal entry.
* **Why it fails:** This content will easily confuse Signal 2 (Stylometrics). Because the heuristics read high variability in sentence lengths and choppy punctuation distribution, they will output a strong human-like score (close to 0.0). This dilutes the LLM signal and pulls the final combined score down into "Uncertain," allowing generated content to evade detection.

---

## API Endpoints

### POST /submit

**Purpose:**  
Accepts text content for analysis and returns an attribution result.

**Request Data Type:**
```json
{
  "content": "Text to analyze..."
}
```

**Response Data Type:**
```json
{
  "submission_id": 1,
  "classification": "ai",
  "confidence": 0.82,
  "label": "This content appears likely to have been generated with AI.",
  "status": "classified"
}
```

---

### POST /appeal

**Purpose:**  
Allows a creator to contest a classification result.

**Request Data Type:**
```json
{
  "submission_id": 1,
  "reason": "I wrote this poem myself."
}
```

**Response Data Type:**
```json
{
  "submission_id": 1,
  "status": "under_review",
  "message": "Appeal submitted successfully."
}
```

---

### GET /submission/<id>

**Purpose:**  
Returns the stored result for a previous submission.

**Response Data Type:**
```json
{
  "submission_id": 1,
  "classification": "uncertain",
  "confidence": 0.57,
  "label": "Unable to confidently determine authorship.",
  "status": "under_review"
}
```

---

### GET /log

**Purpose:**  
Displays the audit log containing classification and appeal events.

**Response Data Type:**
```json
[
  {
    "event_type": "classification",
    "submission_id": 1,
    "confidence": 0.82,
    "status": "classified"
  },
  {
    "event_type": "appeal",
    "submission_id": 1,
    "status": "under_review"
  }
]
```

---

## Architecture

### Submission Flow

```text
Creator
   │
   │ Raw text content
   ▼
┌─────────────────┐
│  POST /submit   │
└────────┬────────┘
         │
         │ Raw text
         ▼
┌─────────────────┐
│  Rate Limiter   │
└────────┬────────┘
         │
         │ Raw text (if allowed)
         ▼
┌─────────────────────────────────────────────────────────┐
│              Multi-Signal Detection Pipeline            │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Signal 1: LLM Attribution Analysis                │  │
│  └────────────────────────┬──────────────────────────┘  │
│                           │ Raw LLM score               │
│                           ▼                             │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Signal 2: Stylometric Heuristics                  │  │
│  └────────────────────────┬──────────────────────────┘  │
│                           │ Raw Stylometric score       │
└───────────────────────────┼─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│           Score Calibration & Engine                    │
│  * Min-Max Normalization of raw signal outputs          │
│  * Applies Weighted Average: (0.65 * S1) + (0.35 * S2)  │
└───────────────────────────┬─────────────────────────────┘
                            │
                            │ Final Combined Score (0.0 - 1.0)
                            ▼
┌─────────────────────────────────────────────────────────┐
│           Transparency Label & Routing Engine           │
│                                                         │
│          Is score >= 0.70? ──► High-Confidence AI       │
│          Is score <= 0.40? ──► High-Confidence Human    │
│          Is score 0.41-0.69? ─► Uncertain/Inconclusive  │
└───────────────────────────┬─────────────────────────────┘
                            │
                            │ Generated Label + Final Confidence
                            ▼
┌─────────────────────────────────────────────────────────┐
│                       Audit Log                         │
│  * Generates unique submission_id                       │
│  * Saves text, scores, label, and status ("classified") │
└───────────────────────────┬─────────────────────────────┘
                            │
                            │ Packed Data Contract
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     API Response                        │
│  {                                                      │
│    "submission_id": 12345, <-- (Frontend stores this    │
│    "classification": "ai",      internally for potential│
│    "confidence": 0.82,          future appeal)          │
│    "label": "..."                                       │
│  }                                                      │
└─────────────────────────────────────────────────────────┘
```

### Appeal Flow

```text
Creator
   │
   │ Submission ID
   │ Appeal reason
   ▼
┌─────────────────┐
│  POST /appeal   │
└────────┬────────┘
         │
         │ Appeal data
         ▼
┌─────────────────┐
│ Status Updater  │
└────────┬────────┘
         │
         │ Status changed to
         │ "under_review"
         ▼
┌─────────────────┐
│   Audit Log     │
└────────┬────────┘
         │
         │ Appeal record
         ▼
┌─────────────────┐
│ API Response    │
└─────────────────┘
```

## AI Tool Plan

This section outlines the prompting strategy, context injection, and validation loops used to co-author Provenance Guard with an AI assistant across the three implementation milestones.

---

### Milestone 3: Submission Endpoint & First Signal

#### 1. Context Provided to AI
* **Spec Sections:** `## Detection Signals` (Signal 1: LLM), `## API Endpoints` (Updated for Milestone contracts), and the complete `Submission Flow` architecture diagram.
* **Technical Constraints:** Flask 3.x boilerplate, Python `groq` SDK configuration, and a lightweight JSON or SQLite structured storage file for the audit trail.

#### 2. Generation Request
* Request a Flask application boilerplate that defines a `POST /submit` route stub and a `GET /log` route stub.
* Instruct the AI to enforce the precise incoming request schema: a JSON body containing a `"text"` string field and a `"creator_id"` string field.
* Request a standalone function `analyze_llm_attribution(text: str) -> float` using Groq's `llama-3.3-70b-versatile` that outputs a normalized score between `0.0` and `1.0`.
* Instruct the AI to wire this signal into the endpoint. The response payload must include a unique, system-generated `"content_id"`, the raw `"llm_score"`, placeholder fields for confidence/labels, and a status of `"classified"`.
* Request the implementation of a structured logging function that appends a complete JSON record (containing `content_id`, `creator_id`, `timestamp`, `llm_score`, and `status`) to the storage file upon every successful submission.

#### 3. Verification Strategy
* Call the `analyze_llm_attribution` function isolated in a local Python script with basic strings to ensure the Groq API parsing functions properly without dropping connections.
* Execute the milestone reference `curl` command against the running local server:
  ```bash
  curl -s -X POST http://localhost:5000/submit \
    -H "Content-Type: application/json" \
    -d '{"text": "The sun dipped below the horizon...", "creator_id": "test-user-1"}' | python -m json.tool

---

### Milestone 4: Multi-Signal Pipeline & Confidence Scoring

#### 1. Context Provided to AI
* **Spec Sections:** `## Detection Signals` (Signal 2 Stylometrics), `## Score Calibration & Uncertainty Mapping`, and the updated `Multi-Signal Detection Pipeline` block within the architecture diagram.

#### 2. Generation Request
* Ask the AI to write a standalone, pure-Python function `calculate_stylometric_heuristics(text: str) -> float`. It must extract 2-3 explicit metrics (e.g., sentence length variance, unique vocabulary token ratios) and map them to a normalized score `[0.0, 1.0]`.
* Request a central engine function `compute_calibrated_confidence(llm_score: float, stylo_score: float) -> dict` that executes the precise 65/35 weighted average formula and enforces calibration rules without silently drifting from the planning document thresholds.

#### 3. Verification Strategy
* Independently call the stylometric function on testing strings to ensure mathematical stability (no divide-by-zero errors on ultra-short sentences).
* Stress test the combined scoring logic with 4 explicit reference profiles:
  1. *Polished, highly predictable AI text* (Expecting a high final score $\ge 0.70$).
  2. *Casual, erratic human text* (Expecting a low final score $\le 0.40$).
  3. *Formal academic human text* (Evaluating how close it hits the borderline region).
  4. *Lightly edited AI output* (Confirming it safely triggers the middle grey zone).
* Print both raw signal outputs to the terminal alongside the final score to audit calibration alignment.

---

### Milestone 5: Production Layer Integration

#### 1. Context Provided to AI
* **Spec Sections:** `## Transparency Label Design`, `## Appeals Workflow`, and both the updated `Submission Flow` and `Appeal Flow` architecture diagrams.
* **Technical Setup:** The `Flask-Limiter` configuration block using an explicit `"memory://"` storage URI.

#### 2. Generation Request
* Request a UI-label mapping function that takes the backend classification and raw score, applies the correct math inversion logic (`1.0 - score` for human classifications), and returns the exact user-facing copy strings defined in the spec.
* Request the complete implementation of the `POST /appeal` endpoint alongside structural updates to the `GET /log` endpoint.

#### 3. Verification Strategy
* **Label Check:** Submit texts to reach all three distinct threshold bands ($0.00-0.40$, $0.41-0.69$, $0.70-1.00$) and verify that the verbatim string variants match your explicit specification copy.
* **Appeals Check:** Grab a `submission_id` from an initial response, submit an appeal payload, and confirm that the status switches to `"under_review"` in the database while leaving the calculated metrics immutable. Call `GET /log` to confirm the appeal logic successfully nests the creator's explanation.
* **Rate Limiting Check:** Execute a rapid loop of 12 requests via terminal. Confirm that requests 1-10 complete with a `200 OK` status and requests 11-12 fail cleanly with a `429 Too Many Requests` status, logging the output text for the README documentation.