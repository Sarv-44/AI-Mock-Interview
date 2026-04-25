# 🔗 Backend File Interconnections - Quick Reference

## File Dependencies & Data Flow

```
        ┌──────────────────────────┐
        │   main.py (FastAPI)      │
        │  - HTTP Endpoints        │
        │  - Request/Response      │
        │  - Whisper Orchestration │
        └──────────────┬───────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
    ┌─────────┐  ┌──────────┐  ┌─────────────┐
    │database │  │  auth.py │  │analytics.py │
    │  .py    │  │- JWT     │  │- Scoring    │
    │         │  │- Password│  │- Feedback   │
    │         │  │- Tokens  │  │             │
    └────┬────┘  └──────────┘  └─────────────┘
         │
         └─→ MySQL Database

    ┌─────────────────┐    ┌────────────────────┐
    │interview_catalog│    │pdf_generator.py    │
    │     .py         │    │- PDF Creation      │
    │- Topics         │    │- ReportLab         │
    │- Questions      │    │                    │
    │- Roles          │    │                    │
    │- Study Paths    │    │                    │
    └─────────────────┘    └────────────────────┘
```

## File-to-File Calls (Imports & Functions)

### main.py imports from:
```python
from backend.auth import:
  ├── create_auth_token(user)
  ├── extract_bearer_token(header)
  └── verify_auth_token(token)

from backend.database import:
  ├── init_database()
  ├── authenticate_user(email, password)
  ├── create_user(username, email, password)
  ├── get_interview_session_plan(topic_id, role_id)
  ├── save_interview_session(session)
  ├── save_question_record(question_data)
  ├── get_user_by_id(user_id)
  ├── get_user_interview_history(user_id)
  ├── list_all_topics()
  ├── list_all_questions()
  ├── get_score_leaderboard(role_id)
  ├── save_topic_rating(session_id, topic_id, rating)
  ├── create_study_plan(user_id, role_id)
  ├── list_study_plans(user_id)
  ├── get_study_plan(plan_id)
  └── update_study_plan_step_status(plan_id, step_id, status)

from backend.analytics import:
  └── analyze_transcript(transcript, topic, question)

from backend.pdf_generator import:
  └── generate_interview_pdf(session, output_path)

from backend.interview_catalog import:
  ├── TOPIC_CATALOG (dict of topics)
  ├── ROLE_CATALOG (dict of roles)
  ├── DURATION_BLUEPRINTS (timing)
  ├── get_topic_catalog_lookup()
  └── get_role_catalog_lookup()
```

### database.py imports from:
```python
from backend.interview_catalog import:
  ├── DURATION_BLUEPRINTS
  ├── ROLE_CATALOG
  ├── TOPIC_CATALOG
  ├── get_role_catalog_lookup()
  ├── get_topic_catalog_lookup()
  └── parse_question_bank()
```

### auth.py imports from:
```python
No backend imports - standalone security module
Uses: base64, hashlib, hmac, json, time, os
```

### analytics.py imports from:
```python
No backend imports - standalone analysis module
Defines: signal terms, scoring, feedback generation
```

### interview_catalog.py imports from:
```python
No backend imports - data-only module
Contains: all question definitions, topic info, role info
```

### pdf_generator.py imports from:
```python
External: reportlab library only
No backend imports
```

---

## Request → Response Flow by Endpoint

### Authentication Flow
```
POST /api/auth/signup
    │
    ├─→ main.py: signup(payload)
    │     ├─→ validate password length
    │     ├─→ database.py: create_user()
    │     │     ├─→ hash password (PBKDF2)
    │     │     └─→ INSERT into users table
    │     ├─→ auth.py: create_auth_token(user)
    │     └─→ return {"token": "...", "user": {...}}
    └─← Browser stores token
```

### Interview Session Flow
```
GET /api/interview/catalog
    │
    ├─→ main.py: get_interview_catalog()
    │     ├─→ database.py: list_all_topics()
    │     │     └─→ SELECT * FROM topics
    │     ├─→ database.py: list_all_roles()
    │     │     └─→ SELECT * FROM roles
    │     └─→ database.py: list_all_questions()
    │           └─→ SELECT * FROM questions
    └─← {"topics": [...], "roles": [...], "questions": [...]}

POST /api/interview/session
    │
    ├─→ main.py: start_interview_session()
    │     └─→ database.py: get_interview_session_plan(topic_id)
    │           ├─→ SELECT questions FROM questions WHERE topic_id
    │           └─→ return questions list
    └─← {"session_id": "...", "questions": [...]}

POST /api/upload-audio/{question_id}
    │
    ├─→ main.py: upload_audio(audio_file)
    │     ├─→ Save file to temp/
    │     ├─→ Load Whisper model (pre-loaded)
    │     ├─→ main.py: transcribe_with_best_effort()
    │     │     └─→ normalize_transcript_text()
    │     ├─→ analytics.py: analyze_transcript()
    │     │     └─→ Extract terms, score, feedback
    │     └─→ database.py: save_question_record()
    │           └─→ INSERT into question_records
    └─← {"transcript": "...", "score": 72, "feedback": "..."}

POST /api/interview/session/{session_id}/submit
    │
    ├─→ main.py: submit_interview_session()
    │     └─→ database.py: save_interview_session()
    │           ├─→ INSERT into interview_sessions
    │           └─→ update_leaderboard()
    └─← {"average_score": 68, "session_id": "..."}
```

### Leaderboard Flow
```
GET /api/leaderboards?role_id=senior_backend&limit=50
    │
    ├─→ main.py: get_leaderboards()
    │     └─→ database.py: get_score_leaderboard(role_id)
    │           ├─→ SELECT users ORDERED BY avg_score
    │           └─→ Add rank, metadata
    └─← {"leaderboard": [
          {"rank": 1, "username": "user1", "avg_score": 85, ...},
          {"rank": 2, "username": "user2", "avg_score": 78, ...},
          ...
        ]}
```

### Study Plan Flow
```
POST /api/study-plans
    │
    ├─→ main.py: create_study_plan_endpoint(payload)
    │     └─→ database.py: create_study_plan(user_id, role_id)
    │           ├─→ GET role curriculum from interview_catalog.py
    │           ├─→ INSERT into study_plans
    │           ├─→ INSERT multiple rows into study_plans_steps
    │           └─→ return plan_id
    └─← {"plan_id": "...", "steps": [...]}

GET /api/study-plans/{plan_id}
    │
    ├─→ main.py: get_study_plan_endpoint()
    │     └─→ database.py: get_study_plan(plan_id)
    │           ├─→ SELECT * FROM study_plans
    │           ├─→ SELECT steps with progress
    │           └─→ return plan structure
    └─← {"plan": {
          "plan_id": "...",
          "role_id": "...",
          "steps": [
            {"topic": "DataStructures", "status": "completed", ...},
            {"topic": "Algorithms", "status": "in_progress", ...}
          ]
        }}

PUT /api/study-plans/{plan_id}/step/{step_id}
    │status: "completed"│
    │
    ├─→ main.py: update_study_plan_step()
    │     └─→ database.py: update_study_plan_step_status()
    │           ├─→ UPDATE study_plans_steps SET status
    │           └─→ return success
    └─← {"success": true}
```

---

## Data Shape Examples

### User Object
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "is_admin": false,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### JWT Token Payload
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "is_admin": false,
  "exp": 1682400000
}
```

### Topic Object
```json
{
  "topic_id": "algorithms",
  "category": "coding",
  "title": "Algorithms",
  "description": "Sorting, searching, DP, graphs",
  "level_label": "Intermediate",
  "estimated_minutes": 22,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Question Object
```json
{
  "question_id": "algo_bfs_101",
  "topic_id": "algorithms",
  "question_text": "Explain breadth-first search algorithm",
  "difficulty": "medium",
  "sample_answer": "BFS uses a queue to explore nodes...",
  "ideal_answer": "BFS is a traversal that explores by breadth...",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Interview Session Object
```json
{
  "session_id": "session-uuid",
  "user_id": "user-uuid",
  "topic_id": "algorithms",
  "total_questions": 3,
  "average_score": 72,
  "answers": [
    {
      "question_id": "algo_bfs_101",
      "transcript": "BFS is a tree traversal algorithm...",
      "score": 68,
      "feedback": "Good explanation of BFS..."
    }
  ],
  "completed_at": "2024-02-15T14:30:00Z"
}
```

### Study Plan Object
```json
{
  "plan_id": "plan-uuid",
  "user_id": "user-uuid",
  "role_id": "senior_backend",
  "created_at": "2024-02-01T00:00:00Z",
  "steps": [
    {
      "step_id": "step1",
      "topic_id": "datastructures",
      "step_order": 1,
      "status": "completed",
      "completed_at": "2024-02-05T10:00:00Z"
    },
    {
      "step_id": "step2",
      "topic_id": "algorithms",
      "step_order": 2,
      "status": "in_progress",
      "completed_at": null
    }
  ]
}
```

---

## Database Operations by File

### database.py handles ALL database operations:

**CREATE (Write)**
- `create_user()` → INSERT users
- `save_question_record()` → INSERT question_records
- `save_interview_session()` → INSERT interview_sessions
- `save_topic_rating()` → INSERT topic_ratings
- `save_topic_record()` → INSERT topics
- `save_role_record()` → INSERT roles
- `create_study_plan()` → INSERT study_plans + study_plans_steps
- `save_custom_interview()` → INSERT custom_interviews
- `save_study_plan_quiz_result()` → INSERT quiz results

**READ (Query)**
- `get_user_by_id()` → SELECT users
- `authenticate_user()` → SELECT users WHERE email/username
- `list_all_topics()` → SELECT topics
- `list_all_questions()` → SELECT questions
- `list_all_roles()` → SELECT roles
- `get_interview_session_plan()` → SELECT questions
- `get_score_leaderboard()` → SELECT users ORDERED BY score
- `get_user_interview_history()` → SELECT interview_sessions
- `get_study_plan()` → SELECT study_plans
- `list_study_plans()` → SELECT study_plans WHERE user_id
- `get_topic_rating_summary()` → SELECT topic_ratings

**UPDATE (Modify)**
- `update_study_plan_step_status()` → UPDATE study_plans_steps
- `save_topic_rating()` → UPDATE leaderboards

**DELETE (Archive)**
- `delete_question_record()` → UPDATE (soft delete)
- `delete_topic_record()` → UPDATE (soft delete)
- `archive_question_record()` → UPDATE (archive)

---

## Configuration Sources

### .env Variables Used:
```
main.py reads:
├── DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
├── WHISPER_MODEL (e.g., "small")
├── WHISPER_FALLBACK_MODEL (e.g., "base")
├── WHISPER_ACCEPTABLE_SCORE (e.g., 36)
├── WHISPER_LANGUAGE_HINTS (e.g., "auto,en,hi")
├── MAX_AUDIO_UPLOAD_BYTES (e.g., 26214400)
├── APP_LOG_LEVEL (e.g., "INFO")
└── WHISPER_INITIAL_PROMPT (context for transcription)

auth.py reads:
├── AUTH_SECRET (JWT signing key)
└── AUTH_TOKEN_MAX_AGE_SECONDS (token expiration)

database.py reads:
├── DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
└── PASSWORD_ITERATIONS (PBKDF2 iterations)
```

---

## Error Handling Pattern

All endpoints follow this pattern:
```
Request
  ↓
main.py: validate (request model)
  ↓
Call backend function (database.py / auth.py / etc)
  ↓
Result:
  - Success: return {"success": true, "data": {...}}
  - Error: caught, logged, normalized
       ↓
respond_with_service_result()
       ↓
return {"success": false, "error": "message", "detail": "extra"}
```

---

## Hot Spots (Most Frequently Used)

1. **database.py**
   - Most critical file - all data persistence
   - Called by almost every endpoint in main.py
   - 50+ functions

2. **auth.py**
   - Called for every protected endpoint
   - Token creation/validation on every login
   - Small but crucial (6 functions)

3. **main.py endpoints**
   - Direct HTTP handler
   - Orchestrates calls to other files
   - 40+ endpoints

4. **analytics.py**
   - Called after every audio upload
   - Interface: analyze_transcript(transcript, topic, question)
   - Returns: {score, feedback, quality, matched_terms}

---

## Adding a New Feature Checklist

```
[ ] 1. Add API endpoint in main.py
        └─ Define Pydantic model for request
           Define response structure

[ ] 2. Add database function in database.py
        └─ Query/insert/update/delete data
           Handle errors & logging

[ ] 3. Connect auth if needed
        └─ Require authentication
           Check permissions

[ ] 4. Test the flow
        └─ Send request
           Check database changes
           Verify response

[ ] 5. Update documentation
        └─ Document endpoint
           Document data shapes
           Show example request/response
```

---

## Code Organization Summary

**By Responsibility:**

| Responsibility | File |
|---|---|
| HTTP routing & orchestration | main.py |
| User auth & session mgmt | auth.py |
| Data persistence (CRUD) | database.py |
| Transcript analysis | analytics.py |
| Content definitions | interview_catalog.py |
| Report generation | pdf_generator.py |

**By Data Domain:**

| Domain | Location |
|---|---|
| Users | database.py tables: users |
| Questions | database.py tables: questions, topics |
| Interviews | database.py tables: interview_sessions, question_records |
| Study Plans | database.py tables: study_plans, study_plans_steps |
| Leaderboards | database.py tables: leaderboards |
| Ratings | database.py tables: topic_ratings |

---

## Quick Debug Path

```
Issue: Audio not transcribing
  └─ Check: main.py upload_audio() 
     └─ Check: Whisper model loaded?
     └─ Check: temp/ file saved?
     └─ Check: audio format supported?
     └─ Check: analytics.analyze_transcript() scoring?

Issue: Login failing
  └─ Check: main.py login()
     └─ Check: database.authenticate_user()
     └─ Check: password hash matches?
     └─ Check: auth.create_auth_token() generates token?

Issue: Study plan not creating steps
  └─ Check: main.py create_study_plan_endpoint()
     └─ Check: database.create_study_plan()
     └─ Check: interview_catalog.ROLE_CATALOG has topics?
     └─ Check: INSERT into study_plans_steps succeeds?

Issue: Leaderboard empty
  └─ Check: database.get_score_leaderboard()
     └─ Check: interview_sessions table has records?
     └─ Check: SQL GROUP BY / ORDER BY correct?
```

