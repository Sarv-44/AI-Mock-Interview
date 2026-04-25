# Backend Documentation Index

Welcome! This folder contains complete backend developer documentation for the Interview Prep App. Start here to understand the codebase.

---

## 📚 Documentation Files

### 1. **BACKEND_DEVELOPER_GUIDE.md** (READ THIS FIRST)
**What:** Complete breakdown of each backend file  
**Covers:**
- Architecture overview
- File-by-file responsibility
- Key functions with code examples
- Database schema
- Authentication system
- Audio processing pipeline
- Setup & running locally

**When to use:** Understanding how each file works and what it does
**Read time:** 30-40 minutes

---

### 2. **BACKEND_FILE_CONNECTIONS.md**
**What:** How backend files connect to each other  
**Covers:**
- Import/dependency diagram
- Request-response flows for each endpoint
- Data flow through the system
- Database operations by file
- Configuration sources
- Quick debug paths

**When to use:** Understanding how files talk to each other, or debugging issues
**Read time:** 20-30 minutes

---

### 3. **API_ENDPOINTS_REFERENCE.md**
**What:** Complete API endpoint documentation  
**Covers:**
- All 30+ endpoints
- Request/response examples
- Required authentication
- Query parameters
- HTTP status codes
- Common patterns

**When to use:** Building frontend, testing APIs, understanding contracts
**Read time:** 20-30 minutes

---

## 🎯 Quick Start Guide

### For New Backend Developers:
1. Read **BACKEND_DEVELOPER_GUIDE.md** (Architecture + File Overview sections)
2. Read **BACKEND_FILE_CONNECTIONS.md** (File Dependencies section)
3. Skim **API_ENDPOINTS_REFERENCE.md** for endpoint names
4. Pick a file and read its detailed section in Guide
5. Start coding!

### For Frontend Developers:
1. Read **API_ENDPOINTS_REFERENCE.md** (all 3 files)
2. skim **BACKEND_DEVELOPER_GUIDE.md** (Authentication System section)
3. Use endpoints reference when building features

### For DevOps/Infrastructure:
1. Read **BACKEND_DEVELOPER_GUIDE.md** (Setup & Running section)
2. Check .env variables in Guide
3. Review database schema for backups

---

## 🗂️ Backend File Structure

```
backend/
├── main.py                      ← FastAPI app, HTTP endpoints, orchestration
│   ├── 60+ endpoints
│   ├── Whisper management
│   └── Request validation
│
├── database.py                  ← ALL database operations
│   ├── User CRUD
│   ├── Interview session management
│   ├── Study plan creation
│   ├── Leaderboard queries
│   └── 50+ functions
│
├── auth.py                      ← JWT tokens, password hashing
│   ├── create_auth_token()
│   ├── verify_auth_token()
│   ├── extract_bearer_token()
│   └── Password hashing
│
├── analytics.py                 ← Transcript scoring, feedback
│   ├── analyze_transcript()
│   ├── extract_signal_terms()
│   ├── score_transcript_candidate()
│   └── Feedback generation
│
├── interview_catalog.py         ← Question bank, topic/role definitions
│   ├── TOPIC_CATALOG (dict)
│   ├── ROLE_CATALOG (dict)
│   ├── STUDY_FAMILY_PROFILES
│   └── Question templates
│
└── pdf_generator.py             ← PDF report generation
    └── generate_interview_pdf()
```

---

## 🔄 Request Flow (High Level)

```
Frontend sends HTTP request
              ↓
main.py receives request (endpoint handler)
              ↓
Validate request (Pydantic model)
              ↓
Authenticate if required (auth.py)
              ↓
Call backend function (database.py / analytics.py)
              ↓
Process data (Whisper, scoring, etc.)
              ↓
Save to MySQL via database.py
              ↓
Return JSON response to frontend
```

---

## 🔑 Key Concepts

### Authentication
- **System:** JWT (JSON Web Tokens)
- **File:** auth.py
- **Token format:** `encoded_payload.signature`
- **Usage:** Every protected endpoint requires `Authorization: Bearer <token>` header
- **Expiration:** 7 days (configurable)

### Audio Processing
- **Transcription:** OpenAI Whisper (local model)
- **Models:** Small (default), Base (fallback)
- **Scoring:** Keywords matched × 12 + word count
- **Quality check:** Must meet minimum score or have enough technical terms

### Database
- **Type:** MySQL 8.0
- **Tables:** 8+ tables (users, topics, questions, interviews, etc.)
- **Persistence:** All operations via database.py
- **Initialization:** Auto-runs on app startup via init_database()

### Interview Types
1. **Topic-based:** Questions from one topic → see algorithms, system design, etc.
2. **Role-based:** Mixed questions from multiple topics weighted by role
3. **Custom:** User-created interview templates

### Study Plans
- **Purpose:** Structured learning path towards career role
- **Auto-generated:** Based on role's topic curriculum
- **Progress tracking:** Step-by-step completion with scoring threshold
- **Example:** Backend Engineer → Data Structures → Algorithms → System Design

---

## 📊 Data Architecture

### Core Database Tables

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| users | User accounts | user_id, username, email, password_hash |
| topics | Interview categories | topic_id, title, description, level |
| questions | Interview questions | question_id, topic_id, question_text |
| interview_sessions | Completed interviews | session_id, user_id, average_score |
| question_records | User's answers | record_id, session_id, transcript, score |
| topic_ratings | User ratings of topics | rating_id, user_id, topic_id, rating |
| study_plans | Learning paths | plan_id, user_id, role_id |
| study_plans_steps | Plan milestones | step_id, plan_id, topic_id, status |
| leaderboards | User rankings | leaderboard_id, user_id, rank, avg_score |

---

## 🛣️ API Endpoints by Category

### Authentication (4 endpoints)
- POST /api/auth/signup
- POST /api/auth/login
- GET /api/auth/users/{user_id}
- GET /api/auth/users/{user_id}/history

### Interview Conduct (3 endpoints)
- GET /api/interview/catalog
- POST /api/interview/session
- POST /api/upload-audio/{question_id}
- POST /api/interview/session/{session_id}/submit

### Ratings & Feedback (2 endpoints)
- GET /api/ratings/topics
- POST /api/ratings/topics

### Leaderboards (1 endpoint)
- GET /api/leaderboards

### Study Plans (5 endpoints)
- POST /api/study-plans
- GET /api/study-plans
- GET /api/study-plans/{plan_id}
- GET /api/study-plans/{plan_id}/step/{step_id}
- PUT /api/study-plans/{plan_id}/step/{step_id}

### Admin Functions (4+ endpoints)
- GET /api/admin/dashboard
- POST /api/admin/topics
- POST /api/admin/questions
- POST /api/admin/roles

### Static Pages (11 GET endpoints)
- GET / (home)
- GET /interview
- GET /results
- GET /leaderboards
- GET /profile
- GET /prep-paths
- GET /admin
- GET /custom-interviews
- GET /tracks
- GET /roles
- GET /auth

---

## 🔌 How Files Depend on Each Other

```
main.py imports everything:
├── auth.py
│   ├── create_auth_token()
│   ├── verify_auth_token()
│   └── extract_bearer_token()
│
├── database.py (50+ functions)
│   ├── init_database()
│   ├── create_user()
│   ├── authenticate_user()
│   ├── get_interview_session_plan()
│   ├── save_interview_session()
│   ├── save_question_record()
│   └── ... 44 more functions
│
├── analytics.py
│   └── analyze_transcript()
│
├── interview_catalog.py
│   ├── TOPIC_CATALOG
│   ├── ROLE_CATALOG
│   └── get_topic_catalog_lookup()
│
└── pdf_generator.py
    └── generate_interview_pdf()

database.py imports:
└── interview_catalog.py (for catalog defaults)

Other files: No interdependencies
```

---

## 🚀 Common Tasks & Where to Find Code

### Task: Add New Endpoint
**Files:** main.py + database.py
**Steps:**
1. Add route handler in main.py
2. Add database function in database.py
3. Define Pydantic request model
4. Implement logic & error handling

### Task: Change Transcription Logic
**Files:** main.py + analytics.py
**Key Functions:**
- main.transcribe_with_best_effort()
- main.normalize_transcript_text()
- analytics.analyze_transcript()

### Task: Modify Scoring Algorithm
**Files:** analytics.py
**Key Function:**
- analytics.score_transcript_candidate()
- Scoring formula: (matched_terms × 12) + min(word_count, 18)

### Task: Add New Interview Topic
**Files:** interview_catalog.py (definitions) + admin endpoint in main.py
**Steps:**
1. Add entry to TOPIC_CATALOG in interview_catalog.py
2. Use admin endpoint to save to database
3. Questions linked via foreign key

### Task: Debug Audio Not Transcribing
**Files:** main.py
**Check:**
1. upload_audio() - file saved to temp/?
2. Whisper model loaded?
3. transcribe_with_best_effort() - exception?
4. normalization & scoring working?

---

## 📝 Code Style & Conventions

### Naming
- Functions: snake_case (e.g., get_interview_session_plan)
- Classes: PascalCase (e.g., SignUpRequest)
- Constants: UPPER_CASE (e.g., WHISPER_MODEL_NAME)

### Error Handling
All endpoints follow this pattern:
```python
try:
    result = some_operation()
    if result.get("success"):
        return result
    
    log_service_failure(...)
    return normalize_service_error(...)
except Exception as e:
    logger.error(...)
    return {"success": False, "error": "..."}
```

### Database Functions
All return dict:
```python
{
    "success": True/False,
    "data": {...},  # if success
    "error": "...",  # if failure
    "detail": "..."  # optional extra info
}
```

### Response Format
Always JSON:
```json
{
    "success": true/false,
    "data": {...},
    "error": "message if failed"
}
```

---

## 🧪 Testing Backend

### Manual Testing
```bash
# Start app
uvicorn backend.main:app --reload

# Test endpoint (in another terminal)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass"}'
```

### Test File
- tests/test_feature_connectivity.py - API connectivity tests

### Database Testing
```bash
# Connect to MySQL
mysql -u root -p interview_app

# Check tables
SHOW TABLES;

# View user data
SELECT * FROM users;
```

---

## 🐛 Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Database initialization failed" | MySQL not running | Start MySQL service |
| Whisper not loading | Model not downloaded | Run: `import whisper; whisper.load_model("small")` |
| Audio transcription fails | Unsupported format | Check ALLOWED_AUDIO_CONTENT_TYPES |
| Token validation fails | Expired or bad signature | Create new token via login |
| Leaderboard empty | No interview_sessions | Run some interviews first |
| Study plan not creating | Role topics missing | Check interview_catalog.py ROLE_CATALOG |

---

## 📖 Learning Paths

### Path 1: Understanding the App (2 hours)
1. Read BACKEND_DEVELOPER_GUIDE (Architecture section)
2. Run app locally
3. Test signup/login endpoint
4. Read interview conduct flow

### Path 2: Adding a Feature (4 hours)
1. Pick a simple feature (e.g., new rating field)
2. Add database column
3. Add database function
4. Add API endpoint in main.py
5. Test with curl

### Path 3: Debugging Performance (3 hours)
1. Enable logging (APP_LOG_LEVEL=DEBUG)
2. Read error logs
3. Check database queries (slow query log)
4. Use BACKEND_FILE_CONNECTIONS for flow tracing

---

## 🎓 Recommended Reading Order

**Day 1:**
- BACKEND_DEVELOPER_GUIDE (Sections 1-3)
- BACKEND_FILE_CONNECTIONS (File Dependencies)

**Day 2:**
- Run app locally
- Test signup & login
- Read API_ENDPOINTS_REFERENCE for 3 endpoints
- BACKEND_DEVELOPER_GUIDE (Authentication System)

**Day 3:**
- Read main.py line by line (first 200 lines)
- Read database.py (first 100 lines)
- Understand get_interview_session_plan()

**Day 4:**
- Trace 1 complete request (e.g., POST /api/auth/login)
- Use BACKEND_FILE_CONNECTIONS as guide
- Write it down in your own words

**Day 5:**
- Pick one database function
- Understand its SQL query
- Modify/extend it
- Test changes

---

## 📞 Quick Reference

### Files at a Glance
| File | Lines | Functions | Purpose |
|------|-------|-----------|---------|
| main.py | 1200+ | 60+ | HTTP endpoints, orchestration |
| database.py | 1500+ | 50+ | Data persistence |
| auth.py | 150+ | 6 | JWT & security |
| analytics.py | 400+ | 8 | Scoring & feedback |
| interview_catalog.py | 600+ | Data dicts | Content definitions |
| pdf_generator.py | 200+ | 2 | PDF creation |

### Most Important Functions
- `main.py: transcribe_with_best_effort()` - Audio pipeline
- `database.py: get_interview_session_plan()` - Interview creation
- `database.py: save_interview_session()` - Result persistence
- `auth.py: create_auth_token()` - Authentication
- `analytics.analyze_transcript()` - Scoring logic

### Most Called Functions
1. `authenticate_user()` - Every login
2. `save_interview_session()` - Every interview completion
3. `get_score_leaderboard()` - Leaderboards page load
4. `analyze_transcript()` - Every audio upload
5. `verify_auth_token()` - Every protected endpoint

---

## 🎯 Next Steps

1. **Clone/Download** the project
2. **Read** BACKEND_DEVELOPER_GUIDE (Architecture section)
3. **Run locally:** `uvicorn backend.main:app --reload`
4. **Test an endpoint:** Use curl or Postman
5. **Pick a file** and read it section-by-section
6. **Modify something small** and test
7. **Reference these docs** whenever confused

---

## 📧 Questions?

Refer to the specific documentation file:
- **"How does X file work?"** → BACKEND_DEVELOPER_GUIDE.md
- **"How do X and Y files talk?"** → BACKEND_FILE_CONNECTIONS.md
- **"What does endpoint Z do?"** → API_ENDPOINTS_REFERENCE.md
- **"How do I add a feature?"** → BACKEND_DEVELOPER_GUIDE.md (Adding Features section)

---

**Happy coding! 🚀**

