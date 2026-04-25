# 🎯 BACKEND DEVELOPER GUIDE - Interview Prep App

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Backend File Structure](#backend-file-structure)
3. [File-by-File Breakdown](#file-by-file-breakdown)
4. [Data Flow & Request Handlers](#data-flow--request-handlers)
5. [Key Functions & Responsibilities](#key-functions--responsibilities)
6. [Database Layer](#database-layer)
7. [Authentication System](#authentication-system)
8. [Audio Processing Pipeline](#audio-processing-pipeline)
9. [Setup & Running](#setup--running)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (main.py)                    │
│  • Route handlers (GET/POST/PUT)                                │
│  • Request validation (Pydantic models)                         │
│  • Audio transcription orchestration                            │
│  • Response formatting & error handling                         │
└────────────────┬─────────────────────────────┬──────────────────┘
                 │                             │
                 ▼                             ▼
    ┌──────────────────────┐      ┌────────────────────┐
    │  database.py         │      │  auth.py           │
    │  ─────────────────── │      │  ──────────────── │
    │ • MySQL queries      │      │ • JWT generation  │
    │ • Data persistence   │      │ • Token verify    │
    │ • CRUD operations    │      │ • Password hash   │
    │ • Schema mgmt        │      │ • Bearer extract  │
    └──────────────────────┘      └────────────────────┘
                 │                       │
                 └──────────┬────────────┘
                            ▼
                    ┌─────────────────┐
                    │   MySQL DB      │
                    │ (8+ tables)     │
                    └─────────────────┘

    ┌──────────────────────┐      ┌────────────────────────┐
    │ analytics.py         │      │ interview_catalog.py   │
    │ ──────────────────── │      │ ─────────────────────  │
    │ • Score transcripts  │      │ • Topic definitions    │
    │ • Extract keywords   │      │ • Role mappings        │
    │ • Generate feedback  │      │ • Question templates   │
    │ • Quality metrics    │      │ • Study profiles       │
    └──────────────────────┘      └────────────────────────┘

    ┌────────────────────────────┐
    │  pdf_generator.py          │
    │  ────────────────────────  │
    │ • Convert results → PDF    │
    │ • ReportLab integration    │
    └────────────────────────────┘
```

---

## Backend File Structure

```
backend/
├── __init__.py                 # Package marker
├── main.py                     # FastAPI app, routes, orchestration
├── database.py                 # MySQL queries, persistence, CRUD
├── auth.py                     # JWT tokens, password hashing
├── analytics.py                # Transcript scoring, feedback generation
├── interview_catalog.py        # Question bank, taxonomy, defaults
└── pdf_generator.py            # PDF report generation
```

---

## File-by-File Breakdown

### 1. **main.py** - The Entry Point & API Router

**Purpose:** FastAPI application, HTTP request handling, orchestration

**What it does:**
- Initializes FastAPI app with CORS middleware
- Mounts static files (/static → static/)
- Loads configuration from .env
- Routes all HTTP requests
- Loads Whisper model at startup
- Handles audio uploads & transcription
- Returns HTML pages + JSON responses

**Key Components:**

#### A. Configuration & Initialization
```python
# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")

# Directories
STATIC_DIR = PROJECT_ROOT / "static"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
TEMP_DIR = PROJECT_ROOT / "temp"

# Audio settings
MAX_AUDIO_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB
WHISPER_MODEL_NAME = "small" or "base"
WHISPER_LANGUAGE_HINTS = ["auto", "en", "hi"]
WHISPER_ACCEPTABLE_SCORE = 36

# Transcript normalization rules
TRANSCRIPT_NORMALIZATION_RULES = [
    (r"\bbee\s+ef\s+ess\b", "BFS"),    # bee ef ess → BFS
    (r"\bdee\s+ef\s+ess\b", "DFS"),    # dee ef ess → DFS
    # ... more rules
]

# Initialize FastAPI with CORS
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=[...])

# Load database at startup
init_database()

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
```

#### B. Helper Functions for Transcription

```python
def normalize_transcript_text(transcript: str) -> str:
    """
    Converts speech-to-text patterns to standard technical terms
    Example: "bee ef ess algorithm" → "BFS algorithm"
    """
    normalized = str(transcript or "").strip()
    for pattern, replacement in TRANSCRIPT_NORMALIZATION_RULES:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    return normalized.strip()

def build_transcription_prompt(topic: str, question: str) -> str:
    """
    Creates context-aware Whisper prompt for better transcription
    Tells Whisper: topic we're discussing + current question
    Example prompt: "This is a technical interview on algorithms about BFS..."
    """
    prompt_parts = [WHISPER_INITIAL_PROMPT]
    if topic:
        prompt_parts.append(f"Interview topic: {topic}.")
    if question:
        prompt_parts.append(f"Current question: {question}.")
    return " ".join(prompt_parts)

def score_transcript_candidate(transcript: str, topic: str, question: str) -> dict:
    """
    Scores a transcribed answer based on technical signal terms
    
    Score = (matched_terms × 12) + min(word_count, 18)
    
    Returns: {"score": 42, "matched_terms": 2, "word_count": 15}
    """
    signal_terms = extract_signal_terms(topic, question)
    matched_terms = sum(1 for term in signal_terms if term in transcript.lower())
    word_count = len(re.findall(r"\b\w+\b", transcript))
    score = (matched_terms * 12) + min(word_count, 18)
    return {"score": score, "matched_terms": matched_terms, "word_count": word_count}

def should_accept_transcript_candidate(candidate_metrics: dict) -> bool:
    """
    Decides if transcription quality is acceptable
    Accept if:
    - Score ≥ 36, OR
    - 2+ signal terms + 10+ words, OR
    - 1+ signal term + 18+ words
    """
    if candidate_metrics["score"] >= WHISPER_ACCEPTABLE_SCORE:
        return True
    if candidate_metrics["matched_terms"] >= 2 and candidate_metrics["word_count"] >= 10:
        return True
    return candidate_metrics["matched_terms"] >= 1 and candidate_metrics["word_count"] >= 18

def transcribe_with_best_effort(model_instance, file_path: Path, topic: str, question: str) -> dict:
    """
    Multi-attempt transcription strategy
    
    Tries language hints: [auto, en, hi]
    Returns best attempt (highest score)
    
    Stops early if quality accepted
    """
    attempts = []
    transcription_prompt = build_transcription_prompt(topic, question)
    
    for language_hint in WHISPER_LANGUAGE_HINTS:
        transcribe_options = {
            "initial_prompt": transcription_prompt,
            "temperature": 0,
            "condition_on_previous_text": False,
            "verbose": False,
        }
        
        if language_hint != "auto":
            transcribe_options["language"] = language_hint
        
        try:
            result = model_instance.transcribe(str(file_path), **transcribe_options)
            normalized_text = normalize_transcript_text(result.get("text", ""))
            candidate_metrics = score_transcript_candidate(normalized_text, topic, question)
            attempts.append((candidate_metrics["score"], normalized_text, result))
            
            if should_accept_transcript_candidate(candidate_metrics):
                result["text"] = normalized_text
                return result  # Accept early
        except Exception as exc:
            print(f"Transcription attempt failed for '{language_hint}': {exc}")
    
    # Return best attempt if no early accept
    if not attempts:
        raise RuntimeError("All transcription attempts failed")
    
    _, best_text, best_result = max(attempts, key=lambda item: item[0])
    best_result["text"] = best_text
    return best_result
```

#### C. Authentication Helpers

```python
def get_authenticated_user_payload(authorization: str | None):
    """
    Extracts & validates JWT from Authorization header
    Returns user payload or None
    """
    token = extract_bearer_token(authorization)
    return verify_auth_token(token)

def require_user_access(request_user, user_id: str):
    """
    Authorization check: user can only access own data
    Raises 401 if not authenticated, 403 if unauthorized
    """
    if not request_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    if request_user.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="You can only access your own data")

def require_admin_access(authorization: str | None):
    """
    Checks if user is admin (is_admin flag in database)
    Raises 401/403 if not authorized
    """
    request_user = get_authenticated_user_payload(authorization)
    if not request_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    user_obj = get_user_by_id(request_user.get("user_id"))
    if not coerce_boolean_flag(user_obj.get("is_admin")):
        raise HTTPException(status_code=403, detail="Admin access required")
    return request_user

def is_admin_user(user_payload):
    """Helper: checks if user has admin role"""
    if not user_payload:
        return False
    user = get_user_by_id(user_payload.get("user_id"))
    return bool(user and coerce_boolean_flag(user.get("is_admin")))
```

#### D. Error Handling

```python
def respond_with_service_result(result, action: str, fallback_error: str, **context):
    """
    Standardizes error responses across all endpoints
    Logs failures with context for debugging
    """
    if isinstance(result, dict) and result.get("success"):
        return result
    
    # Log the failure
    log_service_failure(action, result, **context)
    
    # Return normalized error
    return normalize_service_error(result, fallback_error)

def normalize_service_error(result, fallback_error: str, detail: str | None = None):
    """
    Converts various error types to standard JSON format:
    {"success": false, "error": "message", "detail": "extra info"}
    """
    payload = {"success": False, "error": fallback_error}
    if isinstance(result, dict):
        payload["error"] = str(result.get("error") or fallback_error)
        resolved_detail = str(result.get("detail") or detail or "").strip()
    else:
        resolved_detail = str(detail or "").strip()
    
    if resolved_detail:
        payload["detail"] = resolved_detail
    return payload
```

#### E. Request Models (Pydantic)

```python
# Request validation - Pydantic automatically validates & converts
class SignUpRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    identifier: str | None = None
    email: str | None = None
    password: str

class RatingRequest(BaseModel):
    session_id: str
    topic_id: str
    rating: int

class CustomInterviewQuestionRequest(BaseModel):
    question_text: str
    weight: float | None = 1
    target_seconds: int | None = 90

class CustomInterviewTemplateRequest(BaseModel):
    title: str
    description: str | None = ""
    total_duration_minutes: int = 30
    questions: list[CustomInterviewQuestionRequest]

class AdminTopicRequest(BaseModel):
    topic_id: str
    category: str
    title: str
    description: str
    level_label: str
    accent: str

class StudyPlanRequest(BaseModel):
    role_id: str
    target_days: int = 40
```

#### F. HTML Page Routes (Server-Rendered)

```python
@app.get("/", response_class=HTMLResponse)
def home():
    """Home page - Dashboard"""
    return read_template("index.html")

@app.get("/interview", response_class=HTMLResponse)
def interview():
    """Interview conduct page - Where user answers questions"""
    return read_template("interview.html")

@app.get("/results", response_class=HTMLResponse)
def results():
    """Results page - Shows feedback & scores"""
    return read_template("results.html")

@app.get("/leaderboards", response_class=HTMLResponse)
def leaderboards_page():
    """Leaderboards page - User rankings"""
    return read_template("leaderboards.html")

@app.get("/profile", response_class=HTMLResponse)
def profile_page():
    """User profile & interview history"""
    return read_template("profile.html")

@app.get("/prep-paths", response_class=HTMLResponse)
def prep_paths_page():
    """Study plan builder & tracker"""
    return read_template("prep_paths.html")

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    """Admin dashboard - Catalog management"""
    return read_template("admin.html")

# ... more routes
```

#### G. Authentication API Endpoints

```python
@app.post("/api/auth/signup")
async def signup(payload: SignUpRequest):
    """
    Create new user account
    1. Validate password length (min 8 chars)
    2. Call database.create_user()
    3. Generate JWT token (via auth.create_auth_token())
    4. Return token + user info
    """
    if len(payload.password) < 8:
        return {"success": False, "error": "Password must be at least 8 characters"}
    
    result = build_auth_response(
        create_user(payload.username, payload.email, payload.password)
    )
    return respond_with_service_result(
        result, "Signup", "We could not create your account", email=payload.email
    )

@app.post("/api/auth/login")
async def login(payload: LoginRequest):
    """
    Authenticate user with email/username + password
    1. Call database.authenticate_user()
    2. Generate JWT token
    3. Return token + user info
    """
    identifier = (payload.identifier or payload.email or "").strip()
    if not identifier or not payload.password:
        return {"success": False, "error": "Email/username and password required"}
    
    result = build_auth_response(
        authenticate_user(identifier, payload.password)
    )
    return respond_with_service_result(
        result, "Login", "Could not sign you in", identifier=identifier
    )

@app.get("/api/auth/users/{user_id}")
async def get_user_profile(user_id: str, authorization: str | None = Header(None)):
    """
    Get user profile by ID
    - Requires authentication (same user or admin)
    - Returns user details + stats
    """
    require_user_access(get_authenticated_user_payload(authorization), user_id)
    user = get_user_by_id(user_id)
    return {"success": True, "user": user}

@app.get("/api/auth/users/{user_id}/history")
async def get_user_interview_history(user_id: str, authorization: str | None = Header(None)):
    """
    Get user's interview session history
    - Requires authentication (same user or admin)
    - Returns list of past interview sessions
    """
    require_user_access(get_authenticated_user_payload(authorization), user_id)
    history = get_user_interview_history(user_id)
    return {"success": True, "history": history}
```

#### H. Interview Catalog API

```python
@app.get("/api/interview/catalog")
async def get_interview_catalog():
    """
    Get all available interview topics + roles
    Returns:
    {
        "success": true,
        "topics": [...],      # Available topics for topic-based interviews
        "roles": [...],       # Available roles for role-based interviews
        "questions": [...]    # All questions in catalog
    }
    """
    topics = list_all_topics()
    roles = list_all_roles()
    questions = list_all_questions()
    return {
        "success": True,
        "topics": topics,
        "roles": roles,
        "questions": questions
    }

@app.post("/api/interview/session")
async def start_interview_session(
    topic_id: str | None = None,
    role_id: str | None = None,
    custom_interview_id: str | None = None,
    duration_minutes: int = 30,
    authorization: str | None = Header(None)
):
    """
    Start a new interview session
    1. Create session record in database
    2. Fetch interview plan (questions to ask)
    3. Return session_id + questions
    """
    request_user = get_authenticated_user_payload(authorization)
    user_id = request_user.get("user_id") if request_user else None
    
    session_plan = get_interview_session_plan(
        topic_id, role_id, custom_interview_id, duration_minutes
    )
    
    session = {
        "session_id": str(uuid.uuid4()),
        "user_id": user_id,
        "interview_plan": session_plan,
        "created_at": int(time.time())
    }
    
    return {"success": True, "session": session}

@app.post("/api/interview/session/{session_id}/submit")
async def submit_interview_session(
    session_id: str,
    finish: bool = False,
    authorization: str | None = Header(None)
):
    """
    Submit completed interview session
    1. Save interview session to database
    2. Calculate average score
    3. Return results summary
    """
    request_user = get_authenticated_user_payload(authorization)
    session = get_interview_session(session_id)
    
    if request_user:
        require_session_access(session, request_user)
    
    saved = save_interview_session(session)
    
    avg_score = sum(q["score"] for q in session.get("answers", [])) / len(
        session.get("answers", [])
    ) if session.get("answers") else 0
    
    return {
        "success": True,
        "session_id": session_id,
        "average_score": avg_score,
        "submission_time": int(time.time())
    }
```

#### I. Audio Upload & Transcription

```python
@app.post("/api/upload-audio/{question_id}")
async def upload_audio(
    question_id: str,
    session_id: str = Form(...),
    audio_file: UploadFile = File(...),
    authorization: str | None = Header(None)
):
    """
    CRITICAL FUNCTION: Handles entire audio pipeline
    
    Flow:
    1. Validate audio file (size, type)
    2. Save to temp/ folder
    3. Load Whisper model (pre-loaded at startup)
    4. Transcribe with context-aware prompt
    5. Normalize transcript (bee ef ess → BFS)
    6. Score transcript
    7. Generate feedback
    8. Save question record to database
    9. Return transcript + score + feedback
    """
    
    # Authentication check
    request_user = get_authenticated_user_payload(authorization)
    
    # Validate file
    if audio_file.content_type not in ALLOWED_AUDIO_CONTENT_TYPES:
        return {"success": False, "error": "Invalid audio format"}
    
    file_size = len(await audio_file.read())
    if file_size > MAX_AUDIO_UPLOAD_BYTES:
        return {"success": False, "error": "File too large"}
    
    # Save to temp
    await audio_file.seek(0)
    temp_filename = f"{session_id}_{question_id}.wav"
    temp_path = TEMP_DIR / temp_filename
    
    with open(temp_path, "wb") as f:
        f.write(await audio_file.read())
    
    try:
        # Get question context
        question = get_question_by_id(question_id)
        topic = question.get("topic", "")
        question_text = question.get("question_text", "")
        
        # Transcribe (uses Whisper loaded at startup)
        result = transcribe_with_best_effort(
            whisper_model, temp_path, topic, question_text
        )
        transcript = result.get("text", "")
        
        # Analyze transcript
        analysis = analyze_transcript(transcript, topic, question_text)
        
        # Save to database
        question_record = {
            "session_id": session_id,
            "question_id": question_id,
            "audio_path": str(temp_path),
            "transcript": transcript,
            "score": analysis.get("score"),
            "feedback": analysis.get("feedback"),
            "timestamp": int(time.time())
        }
        
        save_question_record(question_record)
        
        return {
            "success": True,
            "question_id": question_id,
            "transcript": transcript,
            "score": analysis.get("score"),
            "feedback": analysis.get("feedback"),
            "matched_terms": analysis.get("matched_terms")
        }
    
    finally:
        # Cleanup temp file
        if temp_path.exists():
            temp_path.unlink()
```

#### J. Leaderboards & Statistics

```python
@app.get("/api/leaderboards")
async def get_leaderboards(
    role_id: str | None = None,
    limit: int = 50
):
    """
    Get ranked user list
    Optionally filtered by role
    
    Returns top N users by average interview score
    Includes: rank, username, avg_score, interview_count, last_interview
    """
    leaderboard = get_score_leaderboard(role_id, limit)
    return {"success": True, "leaderboard": leaderboard}

@app.get("/api/ratings/topics")
async def get_topic_ratings(authorization: str | None = Header(None)):
    """
    Get user's topic difficulty/usefulness ratings
    Called on profile page to show which topics user finds hardest/easiest
    """
    request_user = get_authenticated_user_payload(authorization)
    user_id = request_user.get("user_id") if request_user else None
    
    if not user_id:
        return {"success": False, "error": "Authentication required"}
    
    ratings = get_topic_rating_summary(user_id)
    return {"success": True, "ratings": ratings}

@app.post("/api/ratings/topics")
async def save_topic_rating(
    payload: RatingRequest,
    authorization: str | None = Header(None)
):
    """
    Save user's rating for a topic after interview
    Rating: 1-5 (difficulty/usefulness)
    """
    request_user = get_authenticated_user_payload(authorization)
    
    result = save_topic_rating(
        payload.session_id,
        payload.topic_id,
        payload.rating,
        request_user.get("user_id") if request_user else None
    )
    
    return respond_with_service_result(result, "Save rating", "Could not save rating")
```

#### K. Study Plans (Prep Paths)

```python
@app.post("/api/study-plans")
async def create_study_plan_endpoint(
    payload: StudyPlanRequest,
    authorization: str | None = Header(None)
):
    """
    Create new study plan for a role
    Auto-generates steps based on role curriculum
    """
    request_user = get_authenticated_user_payload(authorization)
    user_id = request_user.get("user_id") if request_user else None
    
    plan = create_study_plan(user_id, payload.role_id, payload.target_days)
    return respond_with_service_result(plan, "Create plan", "Could not create plan")

@app.get("/api/study-plans")
async def list_study_plans_endpoint(
    authorization: str | None = Header(None)
):
    """
    Get all study plans for authenticated user
    Shows progress: completed steps, current step, next steps
    """
    request_user = get_authenticated_user_payload(authorization)
    user_id = request_user.get("user_id") if request_user else None
    
    if not user_id:
        return {"success": False, "error": "Authentication required"}
    
    plans = list_study_plans(user_id)
    return {"success": True, "plans": plans}

@app.get("/api/study-plans/{plan_id}")
async def get_study_plan_endpoint(
    plan_id: str,
    authorization: str | None = Header(None)
):
    """
    Get detail of a specific study plan
    Includes: all steps, progress, timeline
    """
    plan = get_study_plan(plan_id)
    return {"success": True, "plan": plan}

@app.go("/api/study-plans/{plan_id}/step/{step_id}")
async def get_plan_step_session(
    plan_id: str,
    step_id: str
):
    """
    Get quiz/interview for a study plan step
    User must complete this to mark step as done
    """
    session_plan = get_study_plan_step_session_plan(plan_id, step_id)
    return {"success": True, "session_plan": session_plan}

@app.put("/api/study-plans/{plan_id}/step/{step_id}")
async def update_study_plan_step(
    plan_id: str,
    step_id: str,
    payload: StudyPlanStepStatusRequest
):
    """
    Mark study plan step as completed
    Only allowed if user's score ≥ threshold (usually 70%)
    """
    result = update_study_plan_step_status(plan_id, step_id, payload.status)
    return respond_with_service_result(result, "Update plan step", "Could not update")
```

#### L. Admin Functions

```python
@app.get("/api/admin/dashboard")
async def get_admin_dashboard(authorization: str | None = Header(None)):
    """
    Admin-only: Get dashboard snapshot
    Shows: user count, interview count, avg scores, trending topics
    """
    require_admin_access(authorization)
    
    snapshot = get_admin_dashboard_snapshot()
    return {"success": True, "dashboard": snapshot}

@app.post("/api/admin/topics")
async def create_admin_topic(
    payload: AdminTopicRequest,
    authorization: str | None = Header(None)
):
    """
    Admin: Create or update interview topic
    Topics group questions (e.g., Algorithms, System Design)
    """
    require_admin_access(authorization)
    
    result = save_topic_record(payload.dict())
    return respond_with_service_result(result, "Create topic", "Could not create")

@app.post("/api/admin/questions")
async def create_admin_question(
    payload: AdminQuestionRequest,
    authorization: str | None = Header(None)
):
    """
    Admin: Create or update interview question
    Questions are asked in interviews
    """
    require_admin_access(authorization)
    
    result = save_question_record(payload.dict())
    return respond_with_service_result(result, "Create question", "Could not create")

# ... more admin endpoints
```

---

### 2. **database.py** - Data Persistence Layer

**Purpose:** All MySQL operations, CRUD functions, data schema

**What it does:**
- Manages MySQL connection pool
- Auto-initializes database schema on startup
- Provides CRUD functions for all entities
- Handles transactions & data validation
- Converts data to/from JSON where needed

**Key Components:**

#### A. Database Connection

```python
def get_db_connection():
    """
    Gets MySQL connection
    Reads credentials from .env:
    - DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
    """
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "interview_app")
    )

def execute_query(query: str, params=None, fetch=True):
    """
    Helper: Executes query & returns results
    Handles connection, cursor, error handling
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.rowcount
        return result
    except Error as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()
```

#### B. Schema Initialization

```python
def init_database():
    """
    Called on app startup
    Creates all tables if they don't exist
    Loads default topics, roles, questions from interview_catalog.py
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(36) PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create topics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                topic_id VARCHAR(50) PRIMARY KEY,
                category VARCHAR(50),
                title VARCHAR(100) NOT NULL,
                description TEXT,
                level_label VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create questions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                question_id VARCHAR(100) PRIMARY KEY,
                topic_id VARCHAR(50) NOT NULL,
                question_text TEXT NOT NULL,
                difficulty VARCHAR(20),
                sample_answer TEXT,
                ideal_answer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
            )
        """)
        
        # Create interview_sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interview_sessions (
                session_id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36),
                topic_id VARCHAR(50),
                role_id VARCHAR(50),
                total_questions INT,
                average_score INT,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
            )
        """)
        
        # Create question_records table (answers to Q's)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS question_records (
                record_id VARCHAR(36) PRIMARY KEY,
                session_id VARCHAR(36) NOT NULL,
                question_id VARCHAR(100) NOT NULL,
                audio_path VARCHAR(255),
                transcript TEXT,
                score INT,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES interview_sessions(session_id),
                FOREIGN KEY (question_id) REFERENCES questions(question_id)
            )
        """)
        
        # Create topic_ratings table (user ratings)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topic_ratings (
                rating_id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36),
                topic_id VARCHAR(50),
                rating INT,
                session_id VARCHAR(36),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (topic_id) REFERENCES topics(topic_id),
                FOREIGN KEY (session_id) REFERENCES interview_sessions(session_id)
            )
        """)
        
        # Create study_plans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_plans (
                plan_id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                role_id VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Create study_plans_steps table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_plans_steps (
                step_id VARCHAR(36) PRIMARY KEY,
                plan_id VARCHAR(36),
                topic_id VARCHAR(50),
                step_order INT,
                status VARCHAR(20) DEFAULT 'pending',
                completed_at TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES study_plans(plan_id),
                FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
            )
        """)
        
        # Create leaderboards table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leaderboards (
                leaderboard_id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36),
                rank INT,
                average_score INT,
                interview_count INT,
                last_interview_date TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        conn.commit()
        
        # Load default data from interview_catalog.py
        _load_catalog_defaults()
        
        logger.info("Database initialized successfully")
        
    except Error as e:
        logger.error(f"Database initialization failed: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
```

#### C. User Management

```python
def create_user(username: str, email: str, password: str) -> dict:
    """
    Create new user account
    1. Hash password with PBKDF2 (200k iterations)
    2. Insert into users table
    3. Return user object with JWT token
    """
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        secrets.token_bytes(32),
        PASSWORD_ITERATIONS
    )
    
    user_id = str(uuid.uuid4())
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (user_id, username, email, password_hash, is_admin)
            VALUES (%s, %s, %s, %s, FALSE)
        """, (user_id, username, email, password_hash.hex()))
        
        conn.commit()
        
        return {
            "success": True,
            "user": {
                "user_id": user_id,
                "username": username,
                "email": email,
                "is_admin": False
            }
        }
    
    except Error as e:
        logger.error(f"Create user failed: {e}")
        return {"success": False, "error": str(e)}
    finally:
        cursor.close()
        conn.close()


def authenticate_user(identifier: str, password: str) -> dict:
    """
    Validate user login
    identifier can be username OR email
    Returns user object if password matches
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Find user by username or email
        cursor.execute("""
            SELECT user_id, username, email, password_hash, is_admin
            FROM users
            WHERE username = %s OR email = %s
            LIMIT 1
        """, (identifier, identifier))
        
        user = cursor.fetchone()
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Verify password (compare hashes)
        # Note: In production, use bcrypt or argon2
        # This is simplified
        if not verify_password(password, user["password_hash"]):
            return {"success": False, "error": "Invalid password"}
        
        return {
            "success": True,
            "user": {
                "user_id": user["user_id"],
                "username": user["username"],
                "email": user["email"],
                "is_admin": user["is_admin"]
            }
        }
    
    except Error as e:
        logger.error(f"Authenticate user failed: {e}")
        return {"success": False, "error": "Authentication failed"}
    finally:
        cursor.close()
        conn.close()


def get_user_by_id(user_id: str) -> dict:
    """Get user details by ID"""
    query = "SELECT * FROM users WHERE user_id = %s"
    result = execute_query(query, (user_id,))
    return result[0] if result else None
```

#### D. Interview Session Management

```python
def get_interview_session_plan(
    topic_id: str | None,
    role_id: str | None,
    custom_interview_id: str | None,
    duration_minutes: int = 30
) -> dict:
    """
    Fetch questions for an interview session
    
    Returns structure:
    {
        "session_type": "topic" | "role" | "custom",
        "topic_name": "Algorithms",
        "questions": [
            {
                "question_id": "q1",
                "question_text": "Explain BFS algorithm",
                "duration_seconds": 90
            }
        ]
    }
    """
    if topic_id:
        questions = execute_query("""
            SELECT question_id, question_text
            FROM questions
            WHERE topic_id = %s
            LIMIT 5
        """, (topic_id,))
        
        topic = execute_query("""
            SELECT title FROM topics WHERE topic_id = %s
        """, (topic_id,))
        
        return {
            "session_type": "topic",
            "topic_id": topic_id,
            "topic_name": topic[0]["title"] if topic else "",
            "questions": questions
        }
    
    elif role_id:
        # Get role details & linked topics
        role_info = execute_query("""
            SELECT * FROM roles WHERE role_id = %s
        """, (role_id,))
        
        # Fetch questions from role's topics
        role_topics = json.loads(role_info[0].get("topic_ids", "[]"))
        questions = []
        for t_id in role_topics[:3]:  # Limit to 3 topics
            qs = execute_query("""
                SELECT question_id, question_text
                FROM questions
                WHERE topic_id = %s
                LIMIT 2
            """, (t_id,))
            questions.extend(qs)
        
        return {
            "session_type": "role",
            "role_id": role_id,
            "role_name": role_info[0]["title"] if role_info else "",
            "questions": questions
        }
    
    return {"error": "No interview type specified"}


def save_interview_session(session: dict) -> dict:
    """
    Save completed interview session to database
    Calculates average score from all answers
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        session_id = session.get("session_id")
        user_id = session.get("user_id")
        topic_id = session.get("topic_id")
        answers = session.get("answers", [])
        
        avg_score = sum(a["score"] for a in answers) / len(answers) if answers else 0
        
        cursor.execute("""
            INSERT INTO interview_sessions
            (session_id, user_id, topic_id, total_questions, average_score, completed_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (session_id, user_id, topic_id, len(answers), int(avg_score)))
        
        # Update leaderboard
        update_leaderboard(user_id)
        
        conn.commit()
        
        return {"success": True, "session_id": session_id, "average_score": avg_score}
    
    except Error as e:
        logger.error(f"Save interview session failed: {e}")
        return {"success": False, "error": str(e)}
    finally:
        cursor.close()
        conn.close()


def get_user_interview_history(user_id: str) -> list:
    """
    Get all interview sessions for a user
    Returns list of sessions with scores & dates
    """
    query = """
        SELECT
            session_id, topic_id, average_score, completed_at
        FROM interview_sessions
        WHERE user_id = %s
        ORDER BY completed_at DESC
        LIMIT 50
    """
    return execute_query(query, (user_id,)) or []
```

#### E. Topic & Question Management

```python
def list_all_topics() -> list:
    """Get all available interview topics"""
    query = "SELECT * FROM topics ORDER BY title"
    return execute_query(query) or []

def list_all_questions() -> list:
    """Get all questions in catalog"""
    query = """
        SELECT q.question_id, q.question_text, q.topic_id, q.difficulty,
               t.title as topic_title
        FROM questions q
        JOIN topics t ON q.topic_id = t.topic_id
        ORDER BY t.title, q.question_text
    """
    return execute_query(query) or []

def save_topic_record(topic_data: dict) -> dict:
    """Create or update topic"""
    try:
        topic_id = topic_data.get("topic_id", str(uuid.uuid4()))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO topics (topic_id, category, title, description, level_label)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                category = VALUES(category),
                title = VALUES(title),
                description = VALUES(description),
                level_label = VALUES(level_label)
        """, (
            topic_id,
            topic_data.get("category"),
            topic_data.get("title"),
            topic_data.get("description"),
            topic_data.get("level_label")
        ))
        
        conn.commit()
        return {"success": True, "topic_id": topic_id}
    
    except Error as e:
        logger.error(f"Save topic failed: {e}")
        return {"success": False, "error": str(e)}
    finally:
        cursor.close()
        conn.close()

def save_question_record(question_data: dict) -> dict:
    """Create or update question"""
    try:
        question_id = question_data.get(
            "question_id",
            str(uuid.uuid4())
        )
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO questions
            (question_id, topic_id, question_text, difficulty, sample_answer, ideal_answer)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                topic_id = VALUES(topic_id),
                question_text = VALUES(question_text),
                difficulty = VALUES(difficulty),
                sample_answer = VALUES(sample_answer),
                ideal_answer = VALUES(ideal_answer)
        """, (
            question_id,
            question_data.get("topic_id"),
            question_data.get("question_text"),
            question_data.get("difficulty", "medium"),
            question_data.get("sample_answer"),
            question_data.get("ideal_answer")
        ))
        
        conn.commit()
        return {"success": True, "question_id": question_id}
    
    except Error as e:
        logger.error(f"Save question failed: {e}")
        return {"success": False, "error": str(e)}
    finally:
        cursor.close()
        conn.close()
```

#### F. Leaderboard & Ranking

```python
def get_score_leaderboard(role_id: str | None = None, limit: int = 50) -> list:
    """
    Get ranked list of users by average interview score
    Optionally filtered by role
    """
    if role_id:
        query = """
            SELECT
                u.user_id, u.username,
                AVG(s.average_score) as avg_score,
                COUNT(s.session_id) as interview_count,
                MAX(s.completed_at) as last_interview
            FROM users u
            JOIN interview_sessions s ON u.user_id = s.user_id
            WHERE s.role_id = %s
            GROUP BY u.user_id
            ORDER BY avg_score DESC
            LIMIT %s
        """
        params = (role_id, limit)
    else:
        query = """
            SELECT
                u.user_id, u.username,
                AVG(s.average_score) as avg_score,
                COUNT(s.session_id) as interview_count,
                MAX(s.completed_at) as last_interview
            FROM users u
            JOIN interview_sessions s ON u.user_id = s.user_id
            GROUP BY u.user_id
            ORDER BY avg_score DESC
            LIMIT %s
        """
        params = (limit,)
    
    leaderboard = execute_query(query, params) or []
    
    # Add rank position
    for i, entry in enumerate(leaderboard, 1):
        entry["rank"] = i
    
    return leaderboard

def update_leaderboard(user_id: str):
    """Recalculate user's rank after new interview"""
    # Simplified - would need indexes in production
    avg_score = execute_query("""
        SELECT AVG(average_score) as avg_score
        FROM interview_sessions
        WHERE user_id = %s
    """, (user_id,))
    
    if not avg_score:
        return
    
    # Update leaderboard table
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO leaderboards (leaderboard_id, user_id, average_score)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE average_score = VALUES(average_score)
    """, (str(uuid.uuid4()), user_id, int(avg_score[0]["avg_score"])))
    
    conn.commit()
    cursor.close()
    conn.close()
```

#### G. Study Plans

```python
def create_study_plan(user_id: str, role_id: str, target_days: int = 40) -> dict:
    """
    Create new study plan for user targeting a role
    Auto-generates steps from role's topic curriculum
    
    Example for "Senior Backend Engineer" role:
    - Step 1: Data Structures (4 days)
    - Step 2: Algorithms (6 days)
    - Step 3: System Design (8 days)
    - Step 4: Backend APIs (6 days)
    """
    try:
        plan_id = str(uuid.uuid4())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create plan
        cursor.execute("""
            INSERT INTO study_plans (plan_id, user_id, role_id)
            VALUES (%s, %s, %s)
        """, (plan_id, user_id, role_id))
        
        # Get role's topics
        role = execute_query("""
            SELECT topic_ids FROM roles WHERE role_id = %s
        """, (role_id,))
        
        topic_ids = json.loads(role[0].get("topic_ids", "[]")) if role else []
        
        # Create steps for each topic
        for i, topic_id in enumerate(topic_ids, 1):
            step_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO study_plans_steps
                (step_id, plan_id, topic_id, step_order, status)
                VALUES (%s, %s, %s, %s, 'pending')
            """, (step_id, plan_id, topic_id, i))
        
        conn.commit()
        
        return {
            "success": True,
            "plan_id": plan_id,
            "role_id": role_id,
            "created_at": int(time.time())
        }
    
    except Error as e:
        logger.error(f"Create study plan failed: {e}")
        return {"success": False, "error": str(e)}
    finally:
        cursor.close()
        conn.close()

def list_study_plans(user_id: str) -> list:
    """Get user's study plans with progress"""
    plans = execute_query("""
        SELECT p.plan_id, p.role_id, r.title as role_title,
               COUNT(s.step_id) as total_steps,
               SUM(CASE WHEN s.status = 'completed' THEN 1 ELSE 0 END) as completed_steps
        FROM study_plans p
        LEFT JOIN roles r ON p.role_id = r.role_id
        LEFT JOIN study_plans_steps s ON p.plan_id = s.plan_id
        WHERE p.user_id = %s
        GROUP BY p.plan_id
    """, (user_id,))
    
    for plan in plans:
        plan["progress_percent"] = (
            int(100 * plan.get("completed_steps", 0) / plan.get("total_steps", 1))
            if plan.get("total_steps") else 0
        )
    
    return plans or []

def get_study_plan(plan_id: str) -> dict:
    """Get study plan details with all steps"""
    plan_query = "SELECT * FROM study_plans WHERE plan_id = %s"
    plan = execute_query(plan_query, (plan_id,))
    
    if not plan:
        return {}
    
    plan = plan[0]
    
    steps = execute_query("""
        SELECT s.step_id, s.topic_id, s.step_order, s.status,
               t.title as topic_title
        FROM study_plans_steps s
        JOIN topics t ON s.topic_id = t.topic_id
        WHERE s.plan_id = %s
        ORDER BY s.step_order
    """, (plan_id,))
    
    plan["steps"] = steps or []
    
    return plan

def update_study_plan_step_status(
    plan_id: str,
    step_id: str,
    status: str
) -> dict:
    """Mark step as completed"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE study_plans_steps
            SET status = %s, completed_at = NOW()
            WHERE step_id = %s AND plan_id = %s
        """, (status, step_id, plan_id))
        
        conn.commit()
        
        return {"success": True}
    
    except Error as e:
        logger.error(f"Update step status failed: {e}")
        return {"success": False, "error": str(e)}
    finally:
        cursor.close()
        conn.close()
```

---

### 3. **auth.py** - Authentication & Security

**Purpose:** JWT token management, password hashing, security

**What it does:**
- Creates & validates JWT tokens
- Hashes & verifies passwords
- Extracts tokens from HTTP headers
- Manages token expiration

**Key Functions:**

```python
def create_auth_token(user: dict) -> str:
    """
    Generate JWT token for authenticated user
    
    Payload:
    {
        "user_id": "123",
        "email": "user@example.com",
        "username": "john",
        "is_admin": false,
        "exp": 1682400000
    }
    
    Returns: "encoded_payload.signature"
    """
    expires_at = int(time.time()) + AUTH_TOKEN_MAX_AGE_SECONDS  # 7 days default
    
    payload = {
        "user_id": user["user_id"],
        "email": user.get("email"),
        "username": user.get("username"),
        "is_admin": bool(user.get("is_admin")),
        "exp": expires_at,
    }
    
    encoded_payload = _encode_payload(payload)
    signature = _sign(encoded_payload)
    
    return f"{encoded_payload}.{signature}"


def verify_auth_token(token: str | None) -> dict | None:
    """
    Validate JWT token
    
    Checks:
    1. Token format (encoded_payload.signature)
    2. Signature validity (HMAC-SHA256)
    3. Expiration time
    
    Returns: payload dict if valid, None if invalid
    """
    if not token:
        return None
    
    encoded_payload, separator, signature = token.partition(".")
    
    if not separator or not encoded_payload or not signature:
        return None
    
    # Verify signature
    expected_signature = _sign(encoded_payload)
    if not hmac.compare_digest(signature, expected_signature):
        return None  # Signature invalid
    
    # Decode payload
    try:
        payload = _decode_payload(encoded_payload)
    except (ValueError, json.JSONDecodeError):
        return None
    
    # Check expiration
    if int(payload.get("exp", 0)) < int(time.time()):
        return None  # Token expired
    
    return payload


def extract_bearer_token(authorization_header: str | None) -> str | None:
    """
    Extract JWT from "Authorization: Bearer <token>" header
    
    Example input: "Bearer eyJhbGciOiJIUzI1NiI..."
    Returns: "eyJhbGciOiJIUzI1NiI..."
    """
    if not authorization_header:
        return None
    
    scheme, _, token = authorization_header.partition(" ")
    
    if scheme.lower() != "bearer" or not token:
        return None
    
    return token.strip()


def _encode_payload(payload: dict) -> str:
    """
    Encode payload to base64url format
    JSON → UTF-8 bytes → base64url
    """
    raw_payload = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True
    ).encode("utf-8")
    
    return base64.urlsafe_b64encode(raw_payload).decode("utf-8").rstrip("=")


def _sign(encoded_payload: str) -> str:
    """
    Sign payload with secret using HMAC-SHA256
    Returns hex-encoded signature
    """
    return hmac.new(
        AUTH_SECRET.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
```

---

### 4. **analytics.py** - Transcript Scoring & Feedback

**Purpose:** Score interview answers, generate feedback

**What it does:**
- Extracts technical keywords from questions
- Scores transcript based on matched terms
- Generates feedback for user
- Classifies answer quality

**Key Functions:**

```python
def analyze_transcript(transcript: str, topic: str, question: str) -> dict:
    """
    Analyze transcribed answer and generate feedback
    
    Returns:
    {
        "score": 72,
        "matched_terms": ["BFS", "time_complexity"],
        "feedback": "Good explanation of BFS traversal...",
        "quality": "good"  # excellent|good|needs_improvement
    }
    """
    signal_terms = extract_signal_terms(topic, question)
    transcript_lower = transcript.lower()
    
    matched_terms = [t for t in signal_terms if t in transcript_lower]
    
    # Calculate score
    word_count = len(re.findall(r"\b\w+\b", transcript))
    score = (len(matched_terms) * 12) + min(word_count, 18)
    score = min(score, 100)  # Cap at 100
    
    # Generate feedback
    feedback = _generate_feedback(
        matched_terms, signal_terms, transcript, topic
    )
    
    # Classify quality
    if score >= 75:
        quality = "excellent"
    elif score >= 50:
        quality = "good"
    else:
        quality = "needs_improvement"
    
    return {
        "score": score,
        "matched_terms": matched_terms,
        "feedback": feedback,
        "quality": quality
    }


def extract_signal_terms(topic: str, question: str) -> list[str]:
    """
    Extract important keywords from topic + question
    
    Returns: ["BFS", "algorithm", "traversal", ...]
    """
    # Extract from question text
    raw_terms = re.findall(
        r"[a-zA-Z0-9+#.]+",
        f"{topic} {question}".lower()
    )
    
    # Filter: remove short words & common words
    terms = [
        t for t in raw_terms
        if len(t) >= 3 and t not in STOP_WORDS
    ]
    
    # Add always-relevant terms
    terms.extend([
        "bfs", "dfs", "api", "cache", "queue",
        "database", "latency", "throughput", "scale"
    ])
    
    return list(dict.fromkeys(terms))  # Remove duplicates


def _generate_feedback(
    matched_terms: list,
    expected_terms: list,
    transcript: str,
    topic: str
) -> str:
    """
    Create constructive feedback
    
    Highlights:
    - What was done well
    - What was missing
    - Suggestions for improvement
    """
    feedback_parts = []
    
    # Strengths
    if matched_terms:
        feedback_parts.append(
            f"✓ Good: You mentioned {', '.join(matched_terms[:3])}"
        )
    
    # Gaps
    missing_terms = set(expected_terms) - set(matched_terms)
    if missing_terms:
        feedback_parts.append(
            f"→ Consider: {', '.join(list(missing_terms)[:3])}"
        )
    
    # Word count feedback
    word_count = len(transcript.split())
    if word_count < 50:
        feedback_parts.append(
            "→ Tip: Expand your explanation with more details"
        )
    
    return " | ".join(feedback_parts)
```

---

### 5. **interview_catalog.py** - Content & Taxonomy

**Purpose:** Question bank, topic definitions, role mappings

**What it does:**
- Defines topics (Algorithms, System Design, etc.)
- Defines roles (Senior Backend Engineer, etc.)
- Maps questions to topics
- Provides study guidance & learning paths

**Key Data:**

```python
TOPIC_CATALOG = {
    "algorithms": {
        "category": "coding",
        "title": "Algorithms",
        "description": "Sorting, searching, dynamic programming, graphs",
        "level_label": "Intermediate",
        "estimated_minutes": 22,
        "questions": [
            "algo_bfs_101",
            "algo_dfs_102",
            ...
        ]
    },
    "systemdesign": {
        "category": "architecture",
        "title": "System Design",
        "description": "Scale, reliability, tradeoffs at system level",
        "level_label": "Advanced",
        "estimated_minutes": 28,
        "questions": [...]
    },
    ...
}

ROLE_CATALOG = {
    "senior_backend": {
        "title": "Senior Backend Engineer",
        "description": "...",
        "topic_weights": {
            "algorithms": 2,
            "systemdesign": 2,
            "backend": 3,
            "database": 2,
        }
    },
    ...
}

STUDY_FAMILY_PROFILES = {
    "algorithms": {
        "scenario": "a coding problem where correctness and time complexity matter",
        "answer_focus": "the pattern, the data structure, and complexity tradeoff",
        "mistake_pattern": "jumping to code before naming the pattern"
    },
    ...
}
```

---

### 6. **pdf_generator.py** - Report Generation

**Purpose:** Generate PDF reports of interview results

**What it does:**
- Converts interview session → PDF document
- Includes questions, answers, scores, feedback
- Uses ReportLab library

**Key Function:**

```python
def generate_interview_pdf(session: dict, output_path: str) -> bool:
    """
    Generate PDF report of interview session
    
    Includes:
    - Interview metadata (date, duration, topic)
    - Question-by-question breakdown
    - Transcript & feedback for each question
    - Overall score & rating
    - Suggestions for improvement
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph(
        f"<b>{session['topic_name']} Interview Report</b>",
        styles['Title']
    )
    story.append(title)
    story.append(Spacer(1, 0.3*inch))
    
    # Summary
    summary = Paragraph(
        f"<b>Score:</b> {session['average_score']}/100<br/>"
        f"<b>Date:</b> {session['completed_at']}<br/>"
        f"<b>Questions:</b> {len(session['answers'])}",
        styles['Normal']
    )
    story.append(summary)
    story.append(Spacer(1, 0.3*inch))
    
    # Question-by-question
    for i, answer in enumerate(session['answers'], 1):
        story.append(PageBreak())
        
        q_title = Paragraph(
            f"<b>Question {i}</b>",
            styles['Heading2']
        )
        story.append(q_title)
        
        q_text = Paragraph(answer['question_text'], styles['Normal'])
        story.append(q_text)
        
        story.append(Spacer(1, 0.15*inch))
        
        # Your answer
        story.append(Paragraph("<b>Your Answer:</b>", styles['Heading3']))
        transcript = Paragraph(answer['transcript'], styles['Normal'])
        story.append(transcript)
        
        # Feedback
        story.append(Spacer(1, 0.15*inch))
        story.append(Paragraph("<b>Feedback:</b>", styles['Heading3']))
        feedback = Paragraph(answer['feedback'], styles['Normal'])
        story.append(feedback)
        
        # Score
        score_text = Paragraph(
            f"<b>Score:</b> {answer['score']}/100",
            styles['Normal']
        )
        story.append(score_text)
    
    # Build PDF
    doc.build(story)
    return True
```

---

## Data Flow & Request Handlers

```
USER REQUEST                  MAIN.PY                 DATABASE.PY             RESPONSE
─────────────────────────────────────────────────────────────────────────────────
POST /api/auth/signup ────→ signup()
                             validation
                             create_user() ────────→ INSERT users table
                                                      ← user_id
                             create_auth_token()
                             ← {"token": "xyz"}  ← user data
                             ← JSON response 

POST /api/interview/session ── start_interview_session()
                               get_interview_session_plan() ──→ SELECT questions
                                                                ← questions list
                               ← JSON: session_id, questions

POST /api/upload-audio ──→ upload_audio()
                          transcribe_with_best_effort()  (Whisper)
                          normalize_transcript_text()
                          analyze_transcript()
                          save_question_record() ───→ INSERT question_records
                          ← {"transcript": "...",
                             "score": 72,
                             "feedback": "..."}

GET /api/leaderboards ───→ get_leaderboards()
                          get_score_leaderboard() ──→ SELECT users ranked
                                                      by avg score
                          ← leaderboard list
```

---

## Key Functions & Responsibilities

| Function | File | Purpose |
|----------|------|---------|
| `init_database()` | database.py | Create tables, seed defaults |
| `create_user()` | database.py | Register new user account |
| `authenticate_user()` | database.py | Login validation |
| `create_auth_token()` | auth.py | Generate JWT |
| `verify_auth_token()` | auth.py | Validate JWT |
| `get_interview_session_plan()` | database.py | Fetch questions for interview |
| `save_interview_session()` | database.py | Save completed interview |
| `transcribe_with_best_effort()` | main.py | Convert audio → text (Whisper) |
| `analyze_transcript()` | analytics.py | Score answer + feedback |
| `get_score_leaderboard()` | database.py | Fetch Rankings |
| `create_study_plan()` | database.py | Generate prep path |
| `update_study_plan_step_status()` | database.py | Mark study step completed |
| `generate_interview_pdf()` | pdf_generator.py | Create PDF report |

---

## Database Layer

**Tables & Relationships:**

```
users
├── user_id (PK)
├── username
├── email
├── password_hash
├── is_admin
└── created_at

topics
├── topic_id (PK)
├── title
├── description
├── category
└── level_label

questions
├── question_id (PK)
├── topic_id (FK → topics)
├── question_text
├── difficulty
├── sample_answer
└── ideal_answer

interview_sessions
├── session_id (PK)
├── user_id (FK → users)
├── topic_id (FK → topics)
├── average_score
├── completed_at
└── created_at

question_records (user's answers)
├── record_id (PK)
├── session_id (FK → interview_sessions)
├── question_id (FK → questions)
├── transcript
├── score
├── feedback
└── created_at

topic_ratings (user ratings)
├── rating_id (PK)
├── user_id (FK → users)
├── topic_id (FK → topics)
├── rating (1-5)
└── created_at

study_plans
├── plan_id (PK)
├── user_id (FK → users)
├── role_id
└── created_at

study_plans_steps
├── step_id (PK)
├── plan_id (FK → study_plans)
├── topic_id (FK → topics)
├── status (pending|completed)
└── completed_at

leaderboards
├── leaderboard_id (PK)
├── user_id (FK → users)
├── rank
├── average_score
└── interview_count
```

---

## Authentication System

```
Browser                     Backend
  │                           │
  ├─ POST /api/auth/signup ──→│
  │  email, password, username│
  │                           │ create_user()
  │                           │  - Hash password (PBKDF2)
  │                           │  - INSERT into users table
  │                           │
  │                           │ create_auth_token(user)
  │                           │  - Create JWT payload with user_id, exp
  │                           │  - Sign with AUTH_SECRET (HMAC-SHA256)
  │                           │
  │  ← {"token": "xyz..."}   │
  │                           │
  │ (Store token in localStorage/sessionStorage)
  │                           │
  ├─ GET /api/protected ─────→│ (with header)
  │  Authorization:           │ Authorization: Bearer xyz...
  │  Bearer xyz...            │
  │                           │ extract_bearer_token()
  │                           │ verify_auth_token(token)
  │                           │  - Check signature
  │                           │  - Check expiration
  │                           │  - Decode payload
  │                           │
  │  ← 200 (authorized)      │
```

---

## Audio Processing Pipeline

```
User records audio (browser)
         ↓
Audio blob → Server (POST /api/upload-audio/)
         ↓
Save to temp/ folder
         ↓
Load Whisper model (pre-loaded at startup)
         ↓
For each language hint (auto, en, hi):
         ├─ Create context prompt with topic+question
         ├─ Call whisper.transcribe()
         ├─ Normalize text (bee ef ess → BFS)
         ├─ Score transcript (matched_terms × 12 + word_count)
         ├─ Check if quality acceptable
         └─ If good score → return, else try next language
         ↓
Return best attempt
         ↓
analyze_transcript()
  ├─ Extract matched technical terms
  ├─ Calculate quality score
  └─ Generate feedback
         ↓
save_question_record() → Database
         ↓
Return to Frontend: {transcript, score, feedback}
```

---

## Setup & Running

**1. Install Dependencies**
```bash
pip install -r requirements.txt
```

**2. Configure .env**
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=interview_app

WHISPER_MODEL=small
WHISPER_FALLBACK_MODEL=base
WHISPER_ACCEPTABLE_SCORE=36
WHISPER_LANGUAGE_HINTS=auto,en,hi

MAX_AUDIO_UPLOAD_BYTES=26214400

AUTH_SECRET=your-secret-key
AUTH_TOKEN_MAX_AGE_SECONDS=604800

APP_LOG_LEVEL=INFO
```

**3. Start Database**
```bash
# Ensure MySQL is running
mysql -u root -p
```

**4. Run App**
```bash
uvicorn backend.main:app --reload
```

**5. Open Browser**
```
http://localhost:8000
```

---

## Summary for Backend Developers

### What Each File Does:
1. **main.py** - HTTP endpoints, Whisper orchestration
2. **database.py** - MySQL CRUD, persistence, schema
3. **auth.py** - JWT, password hashing, security
4. **analytics.py** - Transcript scoring, feedback
5. **interview_catalog.py** - Content, taxonomy, defaults
6. **pdf_generator.py** - PDF report creation

### Request-Response Flow:
1. Client sends request
2. main.py receives & validates
3. Calls database.py / auth.py as needed
4. Processes (Whisper for audio, scoring, etc.)
5. Saves to MySQL via database.py
6. Returns JSON response

### Adding New Features:
1. Add API endpoint in main.py
2. Add database function in database.py
3. Add validation (Pydantic models)
4. Add error handling & logging

