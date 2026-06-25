# Planning Document - Provenance Guard

## Overview

Provenance Guard  analyzes submitted text and estimates whether it is more likely human-written or AI-generated. The system uses multiple detection signals instead of relying on a single method. It returns a classification result, a confidence score, and a transparency label that can be shown to readers. Every decision is recorded in an audit log for accountability. Creators can also appeal a classification if they believe the result is incorrect.

---

## Detection Signals

### Signal 1: LLM-Based Attribution Analysis

This signal uses a large language model to evaluate whether the writing resembles common AI-generated text patterns. It looks at things such as tone, structure, repetition, and overall writing style. AI-generated writing is often more consistent and predictable than human writing. This signal cannot determine actual authorship and may misclassify polished human writing or heavily edited AI content.

### Signal 2: Stylometric Heuristics

This signal measures numerical writing features such as sentence length variation, vocabulary diversity, punctuation usage, and repetition. Human writing often contains more irregular patterns, while AI writing can be more statistically uniform. This signal provides an objective measurement that does not depend on another AI model. It cannot understand meaning or context and may struggle with short texts or highly edited content.


**Why they work together:** These two signals examine different aspects of the text. The LLM-based signal evaluates higher-level writing patterns and style, while the stylometric signal measures objective and numerical writing features. Using both signals reduces reliance on a single method and allows the system to be more cautious when the signals disagree, which helps lower the risk of false positives.

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
┌─────────────────────────────────────┐
│ Signal 1: LLM Attribution Analysis  │
└────────┬────────────────────────────┘
         │
         │ AI-likelihood score
         │
         ├─────────────────────────────┐
         │                             │
         ▼                             │
┌─────────────────────────────────────┐│
│ Signal 2: Stylometric Heuristics    ││
└────────┬────────────────────────────┘│
         │                             │
         │ Stylometric score           │
         ▼                             │
┌──────────────────────────────────────────────┐
│      Classification & Confidence Engine      │
└────────┬─────────────────────────────────────┘
         │
         │ Signal scores
         │ Combined confidence score
         │ Classification result
         ▼
┌─────────────────────────────────────┐
│ Transparency Label Generator        │
└────────┬────────────────────────────┘
         │
         │ Label text
         ▼
┌─────────────────┐
│   Audit Log     │
└────────┬────────┘
         │
         │ Stored decision
         ▼
┌─────────────────┐
│ API Response    │
└─────────────────┘
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