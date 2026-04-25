from pathlib import Path
import logging
import os
import re
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")

from backend.analytics import analyze_transcript
from backend.auth import create_auth_token, extract_bearer_token, verify_auth_token
from backend.database import (
    archive_question_record,
    archive_role_record,
    archive_topic_record,
    authenticate_user,
    create_study_plan,
    create_user,
    delete_question_record,
    delete_role_record,
    delete_topic_record,
    delete_custom_interview,
    delete_study_plan,
    get_custom_interview,
    get_custom_interview_session_plan,
    get_interview_session_plan,
    get_interview_session,
    get_role_catalog,
    get_score_leaderboard,
    get_topic_catalog,
    get_topic_activity_summary,
    get_topic_rating_summary,
    list_all_roles,
    list_all_topics,
    list_all_questions,
    get_admin_dashboard_snapshot,
    get_user_by_id,
    get_user_interview_history,
    init_database,
    get_study_plan,
    get_study_plan_step_session_plan,
    list_custom_interviews,
    list_study_plans,
    save_question_record,
    save_interview_session,
    save_custom_interview,
    save_role_record,
    save_study_plan_quiz_result,
    save_topic_record,
    save_topic_rating,
    update_study_plan_step_status,
)
from backend.pdf_generator import generate_interview_pdf

try:
    import whisper
except Exception as exc:  # pragma: no cover - startup fallback
    whisper = None
    logging.getLogger(__name__).warning("Whisper import failed: %s", exc)

STATIC_DIR = PROJECT_ROOT / "static"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
TEMP_DIR = PROJECT_ROOT / "temp"
FAVICON_PATH = STATIC_DIR / "favicon.svg"
MAX_AUDIO_UPLOAD_BYTES = int(os.getenv("MAX_AUDIO_UPLOAD_BYTES", 25 * 1024 * 1024))
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "small")
WHISPER_FALLBACK_MODEL_NAME = os.getenv("WHISPER_FALLBACK_MODEL", "base")
WHISPER_LANGUAGE_HINTS = [
    value.strip().lower()
    for value in os.getenv("WHISPER_LANGUAGE_HINTS", "auto,en,hi").split(",")
    if value.strip()
]
WHISPER_ACCEPTABLE_SCORE = int(os.getenv("WHISPER_ACCEPTABLE_SCORE", "36"))
WHISPER_INITIAL_PROMPT = os.getenv(
    "WHISPER_INITIAL_PROMPT",
    (
        "This is a technical mock interview in Indian English and Hinglish. "
        "Preserve technical terms such as BFS, DFS, DBMS, SQL, API, Node.js, React, "
        "system design, cache, queue, stack, graph, tree, heap, latency, throughput, "
        "database, indexing, recursion, and dynamic programming."
    ),
)
ALLOWED_AUDIO_CONTENT_TYPES = {
    "",
    "application/octet-stream",
    "audio/mp4",
    "audio/mpeg",
    "audio/ogg",
    "audio/wav",
    "audio/webm",
    "audio/x-wav",
    "video/webm",
}

TRANSCRIPT_NORMALIZATION_RULES = [
    (r"\bbee\s+ef\s+ess\b", "BFS"),
    (r"\bdee\s+ef\s+ess\b", "DFS"),
    (r"\bnode\s+js\b", "Node.js"),
    (r"\breact\s+js\b", "React"),
    (r"\bdbms\b", "DBMS"),
    (r"\bapi('?s)?\b", "API"),
    (r"\bsql\b", "SQL"),
    (r"\bllm('?s)?\b", "LLM"),
    (r"\bqueue\b", "queue"),
    (r"\bstack\b", "stack"),
]

TEMP_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=getattr(logging, os.getenv("APP_LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def read_template(template_name: str) -> str:
    template_path = TEMPLATES_DIR / template_name
    with template_path.open(encoding="utf-8") as template_file:
        return template_file.read()


def normalize_transcript_text(transcript: str) -> str:
    normalized = str(transcript or "").strip()

    for pattern, replacement in TRANSCRIPT_NORMALIZATION_RULES:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def build_transcription_prompt(topic: str, question: str) -> str:
    prompt_parts = [WHISPER_INITIAL_PROMPT]

    if topic:
        prompt_parts.append(f"Interview topic: {topic}.")

    if question:
        prompt_parts.append(f"Current question: {question}.")

    prompt_parts.append("Keep mixed English-Hindi technical speech accurate instead of forcing unnatural translations.")
    return " ".join(part for part in prompt_parts if part)


def extract_signal_terms(topic: str, question: str) -> list[str]:
    raw_terms = re.findall(r"[a-zA-Z0-9+#.]+", f"{topic} {question}".lower())
    terms = []
    for term in raw_terms:
        if len(term) < 3:
            continue
        if term in {"what", "when", "where", "which", "with", "would", "should", "could", "explain"}:
            continue
        terms.append(term)

    terms.extend(
        [
            "bfs",
            "dfs",
            "dbms",
            "sql",
            "api",
            "react",
            "node",
            "node.js",
            "queue",
            "stack",
            "cache",
            "latency",
            "throughput",
            "graph",
            "tree",
            "heap",
        ]
    )
    return list(dict.fromkeys(terms))


def score_transcript_candidate(transcript: str, topic: str, question: str) -> dict:
    transcript_lower = transcript.lower()
    signal_terms = extract_signal_terms(topic, question)
    matched_terms = sum(1 for term in signal_terms if term in transcript_lower)
    word_count = len(re.findall(r"\b\w+\b", transcript))
    score = (matched_terms * 12) + min(word_count, 18)
    return {
        "score": score,
        "matched_terms": matched_terms,
        "word_count": word_count,
    }


def should_accept_transcript_candidate(candidate_metrics: dict) -> bool:
    if candidate_metrics["score"] >= WHISPER_ACCEPTABLE_SCORE:
        return True

    if candidate_metrics["matched_terms"] >= 2 and candidate_metrics["word_count"] >= 10:
        return True

    return candidate_metrics["matched_terms"] >= 1 and candidate_metrics["word_count"] >= 18


def transcribe_with_best_effort(model_instance, file_path: Path, topic: str, question: str) -> dict:
    transcription_prompt = build_transcription_prompt(topic, question)
    attempts = []
    device_name = str(getattr(model_instance, "device", "")).lower()

    for language_hint in WHISPER_LANGUAGE_HINTS:
        transcribe_options = {
            "initial_prompt": transcription_prompt,
            "temperature": 0,
            "condition_on_previous_text": False,
            "verbose": False,
        }

        if language_hint != "auto":
            transcribe_options["language"] = language_hint
        if "cpu" in device_name:
            transcribe_options["fp16"] = False

        try:
            result = model_instance.transcribe(str(file_path), **transcribe_options)
            normalized_text = normalize_transcript_text(result.get("text", ""))
            candidate_metrics = score_transcript_candidate(normalized_text, topic, question)
            attempts.append((candidate_metrics["score"], normalized_text, result))
            if should_accept_transcript_candidate(candidate_metrics):
                result["text"] = normalized_text
                return result
        except TypeError:
            # Older or mocked transcribe implementations may not accept keyword args.
            result = model_instance.transcribe(str(file_path))
            normalized_text = normalize_transcript_text(result.get("text", ""))
            candidate_metrics = score_transcript_candidate(normalized_text, topic, question)
            attempts.append((candidate_metrics["score"], normalized_text, result))
            break
        except Exception as exc:
            print(f"Whisper transcription attempt failed for language hint '{language_hint}': {exc}")

    if not attempts:
        raise RuntimeError("All Whisper transcription attempts failed")

    _, best_text, best_result = max(attempts, key=lambda item: item[0])
    best_result["text"] = best_text
    return best_result


def build_auth_response(result):
    if not result.get("success") or not result.get("user"):
        return result

    return {
        **result,
        "token": create_auth_token(result["user"]),
    }


def normalize_service_error(result, fallback_error: str, detail: str | None = None):
    payload = {"success": False, "error": fallback_error}
    if isinstance(result, dict):
        payload["error"] = str(result.get("error") or fallback_error)
        resolved_detail = str(result.get("detail") or detail or "").strip()
    else:
        resolved_detail = str(detail or "").strip()

    if resolved_detail:
        payload["detail"] = resolved_detail
    return payload


def log_service_failure(action: str, result=None, **context):
    error_message = "Operation failed"
    detail_message = ""
    if isinstance(result, dict):
        error_message = str(result.get("error") or error_message)
        detail_message = str(result.get("detail") or "").strip()

    context_summary = ", ".join(f"{key}={value}" for key, value in context.items() if value not in (None, ""))
    log_message = f"{action} failed: {error_message}"
    if detail_message:
        log_message += f" | detail={detail_message}"
    if context_summary:
        log_message += f" | {context_summary}"
    logger.warning(log_message)


def respond_with_service_result(result, action: str, fallback_error: str, **context):
    if isinstance(result, dict) and result.get("success"):
        return result

    log_service_failure(action, result, **context)
    return normalize_service_error(result, fallback_error)


def get_authenticated_user_payload(authorization: str | None):
    token = extract_bearer_token(authorization)
    return verify_auth_token(token)


def coerce_boolean_flag(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def require_user_access(request_user, user_id: str):
    if not request_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if request_user.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="You can only access your own data")


def require_session_access(session, request_user):
    session_user_id = session.get("user_id")
    if not session_user_id:
        return

    require_user_access(request_user, session_user_id)


def is_admin_user(user_payload):
    if not user_payload:
        return False

    user_id = str(user_payload.get("user_id") or "").strip()
    if not user_id:
        return False

    user = get_user_by_id(user_id)
    return bool(user and coerce_boolean_flag(user.get("is_admin")))


def require_admin_access(authorization: str | None):
    request_user = get_authenticated_user_payload(authorization)
    if not request_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not is_admin_user(request_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    return request_user


try:
    init_database()
    logger.info("Database initialized successfully")
except Exception as exc:
    logger.exception("Database initialization failed")
    logger.warning("Application will continue but database features may not work")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def home():
    return read_template("index.html")


@app.get("/tracks", response_class=HTMLResponse)
def tracks_page():
    return read_template("tracks.html")


@app.get("/roles", response_class=HTMLResponse)
def roles_page():
    return read_template("roles.html")


@app.get("/auth", response_class=HTMLResponse)
def auth_page():
    return read_template("auth.html")


@app.get("/profile", response_class=HTMLResponse)
def profile_page():
    return read_template("profile.html")


@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return read_template("admin.html")


@app.get("/custom-interviews", response_class=HTMLResponse)
def custom_interviews_page():
    return read_template("custom_interviews.html")


@app.get("/leaderboards", response_class=HTMLResponse)
def leaderboards_page():
    return read_template("leaderboards.html")


@app.get("/prep-paths", response_class=HTMLResponse)
def prep_paths_page():
    return read_template("prep_paths.html")


@app.get("/interview", response_class=HTMLResponse)
def interview():
    return read_template("interview.html")


@app.get("/results", response_class=HTMLResponse)
def results():
    return read_template("results.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    if FAVICON_PATH.exists():
        return FileResponse(FAVICON_PATH, media_type="image/svg+xml")
    return {"error": "favicon not found"}


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
    user_id: str | None = None


class CustomInterviewQuestionRequest(BaseModel):
    question_text: str
    weight: float | None = 1
    target_seconds: int | None = 90
    section_label: str | None = None


class CustomInterviewTemplateRequest(BaseModel):
    title: str
    description: str | None = ""
    total_duration_minutes: int = 30
    questions: list[CustomInterviewQuestionRequest]


class AdminTopicRequest(BaseModel):
    topic_id: str
    category: str
    title: str
    subtitle: str
    description: str
    level_label: str
    accent: str


class AdminQuestionRequest(BaseModel):
    question_id: str | None = None
    topic_id: str
    question_text: str
    difficulty: str = "medium"
    display_order: int = 1
    sample_answer: str | None = ""
    ideal_answer: str | None = ""


class AdminRoleRequest(BaseModel):
    role_id: str
    title: str
    subtitle: str
    description: str
    level_label: str
    default_duration: int = 30
    available_durations: list[int] | str
    topic_weights: dict[str, int] | str
    primary_topic_id: str | None = None


class StudyPlanRequest(BaseModel):
    role_id: str
    target_days: int = 40


class StudyPlanStepStatusRequest(BaseModel):
    status: str


class StudyPlanQuizResultRequest(BaseModel):
    answers: list[int]


@app.post("/api/auth/signup")
async def signup(payload: SignUpRequest):
    if len(payload.password) < 8:
        return {"success": False, "error": "Password must be at least 8 characters"}

    result = build_auth_response(create_user(payload.username, payload.email, payload.password))
    return respond_with_service_result(result, "Signup", "We could not create your account right now", email=payload.email)


@app.post("/api/auth/login")
async def login(payload: LoginRequest):
    identifier = (payload.identifier or payload.email or "").strip()
    if not identifier or not payload.password:
        return {"success": False, "error": "Email or username and password are required"}
    result = build_auth_response(authenticate_user(identifier, payload.password))
    return respond_with_service_result(result, "Login", "We could not sign you in right now", identifier=identifier)


@app.get("/api/auth/users/{user_id}")
async def get_user_profile(user_id: str, authorization: str | None = Header(default=None)):
    require_user_access(get_authenticated_user_payload(authorization), user_id)
    user = get_user_by_id(user_id)
    if not user:
        return {"success": False, "error": "User not found"}
    return {"success": True, "user": user}


@app.get("/api/auth/users/{user_id}/history")
async def get_user_history(user_id: str, limit: int = 20, authorization: str | None = Header(default=None)):
    require_user_access(get_authenticated_user_payload(authorization), user_id)
    user = get_user_by_id(user_id)
    if not user:
        return {"success": False, "error": "User not found"}

    history = get_user_interview_history(user_id, limit=limit)
    return {"success": True, "history": history}


@app.get("/api/ratings/topics")
async def get_topic_ratings():
    return {"success": True, "ratings": get_topic_rating_summary()}


@app.get("/api/topics/summary")
async def get_topic_summary():
    return {
        "success": True,
        "ratings": get_topic_rating_summary(),
        "activity": get_topic_activity_summary(),
    }


@app.get("/api/interview/catalog")
async def get_interview_catalog():
    try:
        return {
            "success": True,
            "topics": get_topic_catalog(),
            "roles": get_role_catalog(),
        }
    except Exception:
        logger.exception("Interview catalog load failed")
        return {
            "success": False,
            "error": "Interview catalog is temporarily unavailable",
            "detail": "Please refresh in a moment. If this keeps happening, check the database connection.",
        }


@app.get("/api/leaderboards")
async def get_leaderboards(
    board: str = "overall",
    limit: int = 10,
    topic_id: str | None = None,
    authorization: str | None = Header(default=None),
):
    request_user = get_authenticated_user_payload(authorization)
    result = get_score_leaderboard(
        board=board,
        limit=limit,
        topic_id=topic_id,
        current_user_id=request_user.get("user_id") if request_user else None,
    )
    if result.get("success"):
        return result
    log_service_failure("load_leaderboard", result, board=board, topic_id=topic_id)
    return normalize_service_error(result, "Failed to load leaderboard")


@app.get("/api/study-plans")
async def get_user_study_plans(limit: int = 8, authorization: str | None = Header(default=None)):
    request_user = get_authenticated_user_payload(authorization)
    if not request_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return {"success": True, "plans": list_study_plans(request_user["user_id"], limit=limit)}


@app.post("/api/study-plans")
async def create_user_study_plan(payload: StudyPlanRequest, authorization: str | None = Header(default=None)):
    request_user = get_authenticated_user_payload(authorization)
    if not request_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return respond_with_service_result(
        create_study_plan(request_user["user_id"], payload.role_id, payload.target_days),
        "Create study plan",
        "We could not create that prep path",
        user_id=request_user.get("user_id"),
        role_id=payload.role_id,
    )


@app.get("/api/study-plans/{plan_id}")
async def get_user_study_plan(plan_id: str, authorization: str | None = Header(default=None)):
    request_user = get_authenticated_user_payload(authorization)
    if not request_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    result = get_study_plan(plan_id, request_user["user_id"])
    if not result.get("success"):
        status_code = 404 if result.get("error") == "Study plan not found" else 400
        raise HTTPException(status_code=status_code, detail=result.get("error") or "Study plan could not be loaded")
    return result


@app.get("/api/study-plans/{plan_id}/steps/{step_id}/session-plan")
async def get_user_study_step_session_plan(
    plan_id: str,
    step_id: str,
    authorization: str | None = Header(default=None),
):
    request_user = get_authenticated_user_payload(authorization)
    if not request_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    result = get_study_plan_step_session_plan(request_user["user_id"], plan_id, step_id)
    if not result.get("success"):
        status_code = 404 if result.get("error") in {"Study plan not found", "Study step not found"} else 400
        raise HTTPException(status_code=status_code, detail=result.get("error") or "Study step interview could not be loaded")
    return result


@app.post("/api/study-plans/{plan_id}/steps/{step_id}/quiz-result")
async def submit_user_study_step_quiz_result(
    plan_id: str,
    step_id: str,
    payload: StudyPlanQuizResultRequest,
    authorization: str | None = Header(default=None),
):
    request_user = get_authenticated_user_payload(authorization)
    if not request_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return respond_with_service_result(
        save_study_plan_quiz_result(request_user["user_id"], plan_id, step_id, payload.answers),
        "Save study quiz result",
        "We could not save that checkpoint quiz",
        user_id=request_user.get("user_id"),
        plan_id=plan_id,
        step_id=step_id,
    )


@app.delete("/api/study-plans/{plan_id}")
async def delete_user_study_plan(plan_id: str, authorization: str | None = Header(default=None)):
    request_user = get_authenticated_user_payload(authorization)
    if not request_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return respond_with_service_result(
        delete_study_plan(request_user["user_id"], plan_id),
        "Delete study plan",
        "We could not delete that prep path",
        user_id=request_user.get("user_id"),
        plan_id=plan_id,
    )


@app.put("/api/study-plans/{plan_id}/steps/{step_id}")
async def update_user_study_step(
    plan_id: str,
    step_id: str,
    payload: StudyPlanStepStatusRequest,
    authorization: str | None = Header(default=None),
):
    request_user = get_authenticated_user_payload(authorization)
    if not request_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return respond_with_service_result(
        update_study_plan_step_status(request_user["user_id"], plan_id, step_id, payload.status),
        "Update study step",
        "We could not update that prep step",
        user_id=request_user.get("user_id"),
        plan_id=plan_id,
        step_id=step_id,
    )


@app.get("/api/admin/bootstrap")
async def get_admin_bootstrap(authorization: str | None = Header(default=None)):
    require_admin_access(authorization)
    try:
        return {
            "success": True,
            "topics": list_all_topics(),
            "roles": list_all_roles(),
            "questions": list_all_questions(),
            "insights": get_admin_dashboard_snapshot(),
        }
    except Exception:
        logger.exception("Admin bootstrap load failed")
        return {
            "success": False,
            "error": "Admin data could not be loaded",
            "detail": "The catalog tables may be unavailable right now. Please try again.",
        }


@app.get("/api/admin/access")
async def get_admin_access(authorization: str | None = Header(default=None)):
    request_user = get_authenticated_user_payload(authorization)
    return {"success": True, "is_admin": is_admin_user(request_user)}


@app.post("/api/admin/topics")
async def create_admin_topic(payload: AdminTopicRequest, authorization: str | None = Header(default=None)):
    require_admin_access(authorization)
    return respond_with_service_result(
        save_topic_record(payload.model_dump()),
        "Create topic",
        "We could not save that topic",
        topic_id=payload.topic_id,
    )


@app.put("/api/admin/topics/{topic_id}")
async def update_admin_topic(topic_id: str, payload: AdminTopicRequest, authorization: str | None = Header(default=None)):
    require_admin_access(authorization)
    return respond_with_service_result(
        save_topic_record(payload.model_dump(), topic_id=topic_id),
        "Update topic",
        "We could not update that topic",
        topic_id=topic_id,
    )


@app.post("/api/admin/topics/{topic_id}/archive")
async def archive_admin_topic(topic_id: str, authorization: str | None = Header(default=None)):
    require_admin_access(authorization)
    return respond_with_service_result(
        archive_topic_record(topic_id, is_active=False),
        "Archive topic",
        "We could not archive that topic",
        topic_id=topic_id,
    )


@app.post("/api/admin/topics/{topic_id}/restore")
async def restore_admin_topic(topic_id: str, authorization: str | None = Header(default=None)):
    require_admin_access(authorization)
    return respond_with_service_result(
        archive_topic_record(topic_id, is_active=True),
        "Restore topic",
        "We could not restore that topic",
        topic_id=topic_id,
    )


@app.delete("/api/admin/topics/{topic_id}")
async def delete_admin_topic(topic_id: str, authorization: str | None = Header(default=None)):
    require_admin_access(authorization)
    return respond_with_service_result(
        delete_topic_record(topic_id),
        "Delete topic",
        "We could not delete that topic",
        topic_id=topic_id,
    )


@app.post("/api/admin/questions")
async def create_admin_question(payload: AdminQuestionRequest, authorization: str | None = Header(default=None)):
    require_admin_access(authorization)
    return respond_with_service_result(
        save_question_record(payload.model_dump()),
        "Create question",
        "We could not save that question",
        question_id=payload.question_id,
        topic_id=payload.topic_id,
    )


@app.put("/api/admin/questions/{question_id}")
async def update_admin_question(question_id: str, payload: AdminQuestionRequest, authorization: str | None = Header(default=None)):
    require_admin_access(authorization)
    return respond_with_service_result(
        save_question_record(payload.model_dump(), question_id=question_id),
        "Update question",
        "We could not update that question",
        question_id=question_id,
        topic_id=payload.topic_id,
    )


@app.post("/api/admin/questions/{question_id}/archive")
async def archive_admin_question(question_id: str, authorization: str | None = Header(default=None)):
    require_admin_access(authorization)
    return respond_with_service_result(
        archive_question_record(question_id, is_active=False),
        "Archive question",
        "We could not archive that question",
        question_id=question_id,
    )


@app.post("/api/admin/questions/{question_id}/restore")
async def restore_admin_question(question_id: str, authorization: str | None = Header(default=None)):
    require_admin_access(authorization)
    return respond_with_service_result(
        archive_question_record(question_id, is_active=True),
        "Restore question",
        "We could not restore that question",
        question_id=question_id,
    )


@app.delete("/api/admin/questions/{question_id}")
async def delete_admin_question(question_id: str, authorization: str | None = Header(default=None)):
    require_admin_access(authorization)
    return respond_with_service_result(
        delete_question_record(question_id),
        "Delete question",
        "We could not delete that question",
        question_id=question_id,
    )


@app.post("/api/admin/roles")
async def create_admin_role(payload: AdminRoleRequest, authorization: str | None = Header(default=None)):
    require_admin_access(authorization)
    return respond_with_service_result(
        save_role_record(payload.model_dump()),
        "Create role",
        "We could not save that role",
        role_id=payload.role_id,
    )


@app.put("/api/admin/roles/{role_id}")
async def update_admin_role(role_id: str, payload: AdminRoleRequest, authorization: str | None = Header(default=None)):
    require_admin_access(authorization)
    return respond_with_service_result(
        save_role_record(payload.model_dump(), role_id=role_id),
        "Update role",
        "We could not update that role",
        role_id=role_id,
    )


@app.post("/api/admin/roles/{role_id}/archive")
async def archive_admin_role(role_id: str, authorization: str | None = Header(default=None)):
    require_admin_access(authorization)
    return respond_with_service_result(
        archive_role_record(role_id, is_active=False),
        "Archive role",
        "We could not archive that role",
        role_id=role_id,
    )


@app.post("/api/admin/roles/{role_id}/restore")
async def restore_admin_role(role_id: str, authorization: str | None = Header(default=None)):
    require_admin_access(authorization)
    return respond_with_service_result(
        archive_role_record(role_id, is_active=True),
        "Restore role",
        "We could not restore that role",
        role_id=role_id,
    )


@app.delete("/api/admin/roles/{role_id}")
async def delete_admin_role(role_id: str, authorization: str | None = Header(default=None)):
    require_admin_access(authorization)
    return respond_with_service_result(
        delete_role_record(role_id),
        "Delete role",
        "We could not delete that role",
        role_id=role_id,
    )


@app.get("/api/interview/session-plan")
async def get_session_plan(topic_id: str | None = None, role_id: str | None = None, duration_minutes: int = 30):
    plan = get_interview_session_plan(topic_id=topic_id, role_id=role_id, duration_minutes=duration_minutes)
    if not plan:
        return {"success": False, "error": "Interview plan could not be created"}
    return {"success": True, "plan": plan}


@app.get("/api/custom-interviews")
async def get_custom_interview_templates(authorization: str | None = Header(default=None)):
    request_user = get_authenticated_user_payload(authorization)
    if not request_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return {"success": True, "templates": list_custom_interviews(request_user["user_id"])}


@app.get("/api/custom-interviews/{template_id}")
async def get_custom_interview_template(template_id: str, authorization: str | None = Header(default=None)):
    request_user = get_authenticated_user_payload(authorization)
    if not request_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    template = get_custom_interview(template_id, user_id=request_user["user_id"])
    if not template:
        return {"success": False, "error": "Custom interview not found"}
    return {"success": True, "template": template}


@app.get("/api/custom-interviews/{template_id}/session-plan")
async def get_custom_interview_template_plan(template_id: str, authorization: str | None = Header(default=None)):
    request_user = get_authenticated_user_payload(authorization)
    if not request_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    plan = get_custom_interview_session_plan(template_id, request_user["user_id"])
    if not plan:
        return {"success": False, "error": "Custom interview not found"}
    return {"success": True, "plan": plan}


@app.post("/api/custom-interviews")
async def create_custom_interview_template(
    payload: CustomInterviewTemplateRequest,
    authorization: str | None = Header(default=None),
):
    request_user = get_authenticated_user_payload(authorization)
    if not request_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    return save_custom_interview(request_user["user_id"], payload.model_dump())


@app.put("/api/custom-interviews/{template_id}")
async def update_custom_interview_template(
    template_id: str,
    payload: CustomInterviewTemplateRequest,
    authorization: str | None = Header(default=None),
):
    request_user = get_authenticated_user_payload(authorization)
    if not request_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    return save_custom_interview(request_user["user_id"], payload.model_dump(), template_id=template_id)


@app.delete("/api/custom-interviews/{template_id}")
async def remove_custom_interview_template(template_id: str, authorization: str | None = Header(default=None)):
    request_user = get_authenticated_user_payload(authorization)
    if not request_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    return delete_custom_interview(request_user["user_id"], template_id)


@app.post("/api/ratings")
async def submit_topic_rating(payload: RatingRequest, authorization: str | None = Header(default=None)):
    request_user = get_authenticated_user_payload(authorization)
    if payload.user_id:
        require_user_access(request_user, payload.user_id)

    return save_topic_rating(
        session_id=payload.session_id,
        topic_id=payload.topic_id,
        rating=payload.rating,
        user_id=payload.user_id,
    )


def load_whisper_model():
    if whisper is None:
        logger.warning("Audio transcription will not be available because Whisper could not be imported")
        return None

    attempted_models = []
    for model_name in [WHISPER_MODEL_NAME, WHISPER_FALLBACK_MODEL_NAME]:
        if not model_name or model_name in attempted_models:
            continue

        attempted_models.append(model_name)
        try:
            loaded_model = whisper.load_model(model_name)
            logger.info("Whisper model '%s' loaded successfully", model_name)
            return loaded_model
        except Exception as exc:
            logger.warning("Failed to load Whisper model '%s': %s", model_name, exc)

    logger.warning("Audio transcription will not be available")
    return None


model = load_whisper_model()


@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    difficulty: str = Form("medium"),
    topic: str = Form(""),
    question: str = Form(""),
    sample_answer: str = Form(""),
    ideal_answer: str = Form(""),
    analytics_mode: str = Form("full"),
    target_seconds: int = Form(0),
    question_weight: float = Form(0),
):
    if model is None:
        return {"error": "Audio transcription not available - Whisper model failed to load"}

    content_type = (file.content_type or "").split(";")[0].lower()
    if content_type not in ALLOWED_AUDIO_CONTENT_TYPES:
        return {"error": "Unsupported audio format. Please upload a WebM, WAV, MP3, OGG, or MP4 audio file."}

    file_bytes = await file.read(MAX_AUDIO_UPLOAD_BYTES + 1)
    if not file_bytes:
        return {"error": "No audio data was uploaded"}

    if len(file_bytes) > MAX_AUDIO_UPLOAD_BYTES:
        return {"error": "Audio file is too large. Please keep uploads under 25 MB."}

    original_name = Path(file.filename or "recording.webm").name
    file_location = TEMP_DIR / f"{uuid.uuid4()}_{original_name}"

    with file_location.open("wb") as buffer:
        buffer.write(file_bytes)

    try:
        result = transcribe_with_best_effort(model, file_location, topic, question)
        transcript = result["text"]
        duration_seconds = result["segments"][-1]["end"] if result["segments"] else 0
        analysis = analyze_transcript(
            transcript,
            duration_seconds,
            difficulty=difficulty,
            topic=topic,
            question=question,
            sample_answer=sample_answer,
            ideal_answer=ideal_answer,
            analytics_mode=analytics_mode,
            target_seconds=target_seconds,
            question_weight=question_weight,
        )
        os.remove(file_location)
        return analysis
    except Exception as exc:
        if file_location.exists():
            os.remove(file_location)
        logger.exception("Transcription failed for uploaded file '%s'", original_name)
        return {
            "success": False,
            "error": "Transcription failed",
            "detail": "We could not process that recording. Please try again with a shorter or clearer audio clip.",
        }


@app.post("/save-interview")
async def save_interview(interview_data: dict, authorization: str | None = Header(default=None)):
    """Save complete interview session to database."""
    logger.info("Received interview save request for session_id=%s", interview_data.get("session_id", "unknown"))
    try:
        request_user = get_authenticated_user_payload(authorization)
        payload_user_id = interview_data.get("user_id")

        if payload_user_id:
            require_user_access(request_user, payload_user_id)

        save_result = save_interview_session(interview_data)
        if isinstance(save_result, dict):
            if save_result.get("success"):
                return {"success": True, "session_id": save_result["session_id"]}
            log_service_failure(
                "Save interview",
                save_result,
                session_id=interview_data.get("session_id"),
                user_id=payload_user_id,
            )
            return normalize_service_error(save_result, "Failed to save session")

        if save_result:
            return {"success": True, "session_id": save_result}

        failure = {
            "success": False,
            "error": "Failed to save session",
            "detail": "The interview payload was not accepted by the database.",
        }
        log_service_failure("Save interview", failure, session_id=interview_data.get("session_id"), user_id=payload_user_id)
        return failure
    except Exception:
        logger.exception("Unexpected exception while saving interview")
        return {
            "success": False,
            "error": "Failed to save session",
            "detail": "An unexpected server error occurred while saving this interview.",
        }


@app.get("/generate-pdf/{session_id}")
async def generate_pdf(session_id: str, authorization: str | None = Header(default=None)):
    """Generate and download PDF report for an interview session."""
    try:
        session = get_interview_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        require_session_access(session, get_authenticated_user_payload(authorization))

        pdf_filename = generate_interview_pdf(session["complete_data"])
        if not pdf_filename or not os.path.exists(pdf_filename):
            logger.warning("PDF generation returned no file for session_id=%s", session_id)
            return {
                "success": False,
                "error": "Failed to generate PDF",
                "detail": "The report file could not be created for this session.",
            }

        download_filename = os.path.basename(pdf_filename)
        return FileResponse(
            pdf_filename,
            media_type="application/pdf",
            filename=download_filename,
            headers={
                "Content-Disposition": f"attachment; filename={download_filename}",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
    except Exception:
        logger.exception("Error while generating PDF for session_id=%s", session_id)
        return {
            "success": False,
            "error": "Failed to generate PDF",
            "detail": "An unexpected server error occurred while building the PDF report.",
        }


@app.get("/get-session/{session_id}")
async def get_session(session_id: str, authorization: str | None = Header(default=None)):
    """Retrieve interview session data."""
    try:
        session = get_interview_session(session_id)
        if session:
            require_session_access(session, get_authenticated_user_payload(authorization))
            return {"success": True, "data": session}
        return {"success": False, "error": "Session not found"}
    except Exception:
        logger.exception("Error while loading session_id=%s", session_id)
        return {
            "success": False,
            "error": "Failed to load session",
            "detail": "An unexpected server error occurred while loading this interview.",
        }
