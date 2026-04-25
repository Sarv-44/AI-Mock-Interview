import hashlib
import hmac
import json
import logging
import os
import random
import secrets
import time
import uuid
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

from backend.interview_catalog import (
    DURATION_BLUEPRINTS,
    ROLE_CATALOG,
    TOPIC_CATALOG,
    get_role_catalog_lookup,
    get_topic_catalog_lookup,
    parse_question_bank,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

PASSWORD_ITERATIONS = 200_000
logger = logging.getLogger(__name__)


def summarize_context(**context):
    return ", ".join(f"{key}={value}" for key, value in context.items() if value not in (None, ""))


def describe_database_error(exc):
    if not exc:
        return ""

    if getattr(exc, "errno", None) == 1062:
        return "A record with the same unique value already exists."
    if getattr(exc, "errno", None) == 1451:
        return "This record is still referenced by other data, so it cannot be changed yet."
    if getattr(exc, "errno", None) == 1452:
        return "One of the related records does not exist anymore. Refresh the page and try again."
    if getattr(exc, "errno", None) == 1048:
        return "A required database field was empty."

    message = str(exc).lower()
    if "data too long" in message:
        return "One of the values is too long for the database schema."
    return ""


def database_failure(error_message, exc=None, *, detail=None, **context):
    context_summary = summarize_context(**context)
    detail_message = str(detail or describe_database_error(exc) or "").strip()

    if exc is not None:
        if context_summary:
            logger.exception("%s | %s", error_message, context_summary)
        else:
            logger.exception("%s", error_message)
    else:
        logger.warning("%s%s", error_message, f" | {context_summary}" if context_summary else "")

    payload = {"success": False, "error": error_message}
    if detail_message:
        payload["detail"] = detail_message
    return payload


def get_db_config():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "interview_db"),
    }


def create_database_connection(include_database=True):
    """Create database connection with retry logic."""
    max_retries = 3
    retry_delay = 1
    config = get_db_config()

    if not include_database:
        config.pop("database", None)

    for attempt in range(max_retries):
        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            logger.debug("Database connection established on attempt %s", attempt + 1)
            return connection
        except Error as exc:
            logger.warning("Database connection attempt %s failed: %s", attempt + 1, exc)
            if attempt < max_retries - 1:
                logger.info("Retrying database connection in %s seconds", retry_delay)
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error("All database connection attempts failed")
                return None
        except Exception as exc:
            logger.exception("Unexpected database connection error on attempt %s", attempt + 1)
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                return None

    return None


def hash_password(password, salt=None):
    """Hash a password using PBKDF2-HMAC-SHA256."""
    if salt is None:
        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PASSWORD_ITERATIONS,
    ).hex()
    return salt, password_hash


def verify_password(password, salt, password_hash):
    """Verify a password against a stored salt + hash."""
    _, computed_hash = hash_password(password, salt=salt)
    return hmac.compare_digest(computed_hash, password_hash)


def coerce_boolean_flag(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def normalize_user_row(row):
    if not row:
        return None

    return {
        "user_id": row["user_id"],
        "username": row["username"],
        "email": row["email"],
        "is_admin": coerce_boolean_flag(row.get("is_admin")),
        "created_at": str(row["created_at"]) if row.get("created_at") else None,
    }


def parse_json_field(value, default):
    if value in (None, ""):
        return default

    if isinstance(value, (dict, list)):
        return value

    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def normalize_custom_duration_minutes(duration_minutes, fallback=30):
    try:
        normalized = int(duration_minutes)
    except (TypeError, ValueError):
        normalized = fallback

    return max(5, min(normalized, 240))


def normalize_custom_question(question, position):
    if not isinstance(question, dict):
        return None

    question_text = str(question.get("question_text") or question.get("q") or "").strip()
    if not question_text:
        return None

    try:
        weight = float(question.get("weight", 1) or 1)
    except (TypeError, ValueError):
        weight = 1.0

    try:
        target_seconds = int(question.get("target_seconds", 90) or 90)
    except (TypeError, ValueError):
        target_seconds = 90

    return {
        "question_id": str(question.get("question_id") or f"custom_{position:03d}"),
        "topic_id": "custom",
        "question_text": question_text,
        "q": question_text,
        "difficulty": "custom",
        "weight": round(max(0.1, weight), 2),
        "target_seconds": max(15, min(target_seconds, 1800)),
        "section_label": str(question.get("section_label") or f"Custom {position}"),
    }


def normalize_custom_questions(questions):
    normalized = []
    for index, question in enumerate(questions or [], start=1):
        item = normalize_custom_question(question, index)
        if item:
            normalized.append(item)
    return normalized


def normalize_custom_interview_row(row):
    questions = normalize_custom_questions(parse_json_field(row.get("questions_json"), []))
    return {
        "template_id": row["template_id"],
        "user_id": row["user_id"],
        "title": row["title"],
        "description": row.get("description") or "",
        "total_duration_minutes": normalize_custom_duration_minutes(row.get("total_duration_minutes"), fallback=30),
        "question_count": len(questions),
        "questions": questions,
        "created_at": str(row.get("created_at")) if row.get("created_at") else None,
        "updated_at": str(row.get("updated_at")) if row.get("updated_at") else None,
    }


def normalize_study_plan_days(target_days, fallback=40):
    try:
        normalized = int(target_days)
    except (TypeError, ValueError):
        normalized = fallback

    return max(7, min(normalized, 120))


def normalize_study_plan_status(status):
    resolved = str(status or "").strip().lower()
    if resolved in {"completed", "archived"}:
        return resolved
    return "active"


def normalize_study_step_status(status):
    resolved = str(status or "").strip().lower()
    if resolved in {"in_progress", "done"}:
        return resolved
    return "planned"


def build_study_plan_id():
    return f"plan_{uuid.uuid4().hex[:20]}"


def build_study_step_id():
    return f"step_{uuid.uuid4().hex[:20]}"


def normalize_study_material_row(row):
    rapid_fire_points = [
        str(item).strip()
        for item in parse_json_field(row.get("rapid_fire_points"), [])
        if str(item).strip()
    ]
    practice_prompts = [
        str(item).strip()
        for item in parse_json_field(row.get("practice_prompts"), [])
        if str(item).strip()
    ]
    return {
        "topic_id": row["topic_id"],
        "topic_title": row.get("topic_title") or row["topic_id"].replace("_", " ").title(),
        "overview": str(row.get("overview") or "").strip(),
        "revision_notes": str(row.get("revision_notes") or "").strip(),
        "common_mistakes": str(row.get("common_mistakes") or "").strip(),
        "rapid_fire_points": rapid_fire_points,
        "practice_prompts": practice_prompts,
        "estimated_minutes": int(row.get("estimated_minutes") or 20),
        "updated_at": str(row.get("updated_at")) if row.get("updated_at") else None,
    }


def normalize_study_plan_row(row):
    plan_summary = parse_json_field(row.get("plan_summary"), {})
    focus_topic_ids = [
        str(item).strip()
        for item in parse_json_field(row.get("focus_topic_ids"), [])
        if str(item).strip()
    ]
    return {
        "plan_id": row["plan_id"],
        "user_id": row["user_id"],
        "role_id": row["role_id"],
        "role_title": row.get("role_title") or row["role_id"].replace("_", " ").title(),
        "title": row.get("title") or row.get("role_title") or "Study plan",
        "target_days": normalize_study_plan_days(row.get("target_days"), fallback=40),
        "status": normalize_study_plan_status(row.get("status")),
        "focus_topic_ids": focus_topic_ids,
        "step_count": int(row.get("step_count") or plan_summary.get("step_count") or 0),
        "completed_steps": int(row.get("completed_steps") or 0),
        "plan_summary": plan_summary,
        "created_at": str(row.get("created_at")) if row.get("created_at") else None,
        "updated_at": str(row.get("updated_at")) if row.get("updated_at") else None,
    }


def normalize_study_plan_step_row(row):
    question_ids = [
        str(item).strip()
        for item in parse_json_field(row.get("question_ids"), [])
        if str(item).strip()
    ]
    snapshot = parse_json_field(row.get("snapshot_json"), {})
    return {
        "step_id": row["step_id"],
        "plan_id": row["plan_id"],
        "sequence_no": int(row.get("sequence_no") or 0),
        "phase_key": str(row.get("phase_key") or "").strip() or "foundation",
        "step_type": str(row.get("step_type") or "").strip() or "revise",
        "scheduled_day": int(row.get("scheduled_day") or 1),
        "scheduled_label": str(row.get("scheduled_label") or f"Day {int(row.get('scheduled_day') or 1)}"),
        "topic_id": row.get("topic_id"),
        "topic_title": row.get("topic_title"),
        "role_id": row.get("role_id"),
        "role_title": row.get("role_title"),
        "question_ids": question_ids,
        "status": normalize_study_step_status(row.get("status")),
        "snapshot": snapshot,
        "last_score": int(snapshot.get("last_score") or 0) if snapshot.get("last_score") not in (None, "") else None,
        "updated_at": str(row.get("updated_at")) if row.get("updated_at") else None,
    }


def average_numbers(values, digits=1):
    normalized = []
    for value in values or []:
        try:
            normalized.append(float(value))
        except (TypeError, ValueError):
            continue
    if not normalized:
        return 0.0
    return round(sum(normalized) / len(normalized), digits)


def build_question_selection_plan(*difficulties, fallback_count=4):
    plan = [str(difficulty).strip().lower() for difficulty in difficulties if str(difficulty).strip()]
    return plan[: max(1, fallback_count)] or ["medium"] * max(1, fallback_count)


def pick_questions_for_difficulty_plan(all_questions, difficulty_plan, exclude_ids=None):
    if not all_questions:
        return []

    remaining_by_difficulty = {"easy": [], "medium": [], "hard": []}
    excluded = {str(question_id).strip() for question_id in (exclude_ids or []) if str(question_id).strip()}

    for question in all_questions:
        if question["question_id"] in excluded:
            continue
        remaining_by_difficulty.setdefault(question["difficulty"], []).append(question)

    for items in remaining_by_difficulty.values():
        random.shuffle(items)

    selected = []
    seen_ids = set()
    for difficulty in difficulty_plan:
        pool = remaining_by_difficulty.get(difficulty, [])
        while pool:
            candidate = pool.pop()
            if candidate["question_id"] in seen_ids:
                continue
            selected.append(candidate)
            seen_ids.add(candidate["question_id"])
            break

    if len(selected) < len(difficulty_plan):
        remaining = [
            question
            for question in all_questions
            if question["question_id"] not in excluded and question["question_id"] not in seen_ids
        ]
        random.shuffle(remaining)
        selected.extend(remaining[: len(difficulty_plan) - len(selected)])

    return selected[: len(difficulty_plan)]


def build_topic_round_questions(topic_id, round_stage):
    all_questions = get_questions_for_topic(topic_id)
    if not all_questions:
        return []

    if int(round_stage or 1) >= 2:
        primary_plan = build_question_selection_plan("medium", "medium", "hard", "hard", "medium", fallback_count=5)
        exclude_ids = [
            question["question_id"]
            for question in pick_questions_for_difficulty_plan(
                all_questions,
                build_question_selection_plan("easy", "easy", "medium", "medium", "medium", fallback_count=5),
            )
        ]
        selected = pick_questions_for_difficulty_plan(all_questions, primary_plan, exclude_ids=exclude_ids)
    else:
        primary_plan = build_question_selection_plan("easy", "easy", "medium", "medium", "medium", fallback_count=5)
        selected = pick_questions_for_difficulty_plan(all_questions, primary_plan)

    return selected


def build_mixed_round_questions(topic_ids, difficulty_plan, rotation_seed=0):
    resolved_topic_ids = [str(topic_id).strip() for topic_id in (topic_ids or []) if str(topic_id).strip()]
    if not resolved_topic_ids:
        return []

    topic_banks = {topic_id: get_questions_for_topic(topic_id) for topic_id in resolved_topic_ids}
    for bank in topic_banks.values():
        random.shuffle(bank)

    selected = []
    used_question_ids = set()
    ordered_topic_ids = resolved_topic_ids[:]
    if ordered_topic_ids:
        offset = int(rotation_seed or 0) % len(ordered_topic_ids)
        ordered_topic_ids = ordered_topic_ids[offset:] + ordered_topic_ids[:offset]

    for difficulty in difficulty_plan:
        picked_question = None
        for topic_id in ordered_topic_ids:
            pool = [
                question
                for question in topic_banks.get(topic_id, [])
                if question["question_id"] not in used_question_ids and question["difficulty"] == difficulty
            ]
            if pool:
                picked_question = pool[0]
                break

        if picked_question is None:
            for topic_id in ordered_topic_ids:
                pool = [
                    question
                    for question in topic_banks.get(topic_id, [])
                    if question["question_id"] not in used_question_ids
                ]
                if pool:
                    picked_question = pool[0]
                    break

        if picked_question is None:
            break

        selected.append(picked_question)
        used_question_ids.add(picked_question["question_id"])

    return selected


def get_questions_by_ids(question_ids):
    resolved_question_ids = [str(question_id).strip() for question_id in (question_ids or []) if str(question_id).strip()]
    if not resolved_question_ids:
        return []

    connection = create_database_connection()
    if connection is None:
        question_map = {}
        for question_id in resolved_question_ids:
            topic_id = question_id.rsplit("_", 1)[0] if "_" in question_id else ""
            for question in get_questions_for_topic(topic_id):
                question_map[question["question_id"]] = question
        return [question_map[question_id] for question_id in resolved_question_ids if question_id in question_map]

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        placeholders = ", ".join(["%s"] * len(resolved_question_ids))
        cursor.execute(
            f"""
            SELECT question_id, topic_id, question_text, difficulty, sample_answer, ideal_answer, display_order, is_active
            FROM questions
            WHERE question_id IN ({placeholders}) AND is_active = TRUE
            """,
            tuple(resolved_question_ids),
        )
        rows = cursor.fetchall() or []
        question_map = {row["question_id"]: normalize_question_row(row) for row in rows}
        return [question_map[question_id] for question_id in resolved_question_ids if question_id in question_map]
    except Error:
        logger.exception("Database error loading questions by IDs")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def build_default_study_material(topic, questions=None):
    topic_title = str((topic or {}).get("title") or (topic or {}).get("topic_title") or "Topic").strip() or "Topic"
    subtitle = str((topic or {}).get("subtitle") or "").strip()
    description = str((topic or {}).get("description") or "").strip()
    prompt_texts = [
        str(question.get("question_text") or question.get("q") or "").strip()
        for question in (questions or [])
        if str(question.get("question_text") or question.get("q") or "").strip()
    ]
    rapid_fire_points = [
        f"Define {topic_title} in one clear sentence before adding detail.",
        f"Explain the main workflow behind {subtitle or topic_title} with one concrete example.",
        f"Call out trade-offs, edge cases, and when {topic_title} is the wrong fit.",
    ]
    if prompt_texts:
        rapid_fire_points.append(f"Practice this prompt aloud: {prompt_texts[0]}")

    return {
        "topic_id": str((topic or {}).get("topic_id") or "").strip(),
        "topic_title": topic_title,
        "overview": (
            f"{topic_title} usually appears when the interviewer wants confidence around "
            f"{subtitle.lower() if subtitle else topic_title.lower()}. "
            f"{description or 'Stay ready with fundamentals, reasoning, and one interview-friendly example.'}"
        ).strip(),
        "revision_notes": (
            f"Revise the definition, the core pattern, complexity or trade-offs, and one crisp real-world use case for {topic_title}. "
            f"Keep your explanation compact enough to fit into a 60 to 90 second answer."
        ),
        "common_mistakes": (
            f"Candidates often stay too textbook-heavy in {topic_title}, skip edge cases, or forget to compare alternatives."
        ),
        "rapid_fire_points": rapid_fire_points[:4],
        "practice_prompts": prompt_texts[:4],
        "estimated_minutes": 20,
    }


def build_custom_interview_plan(template):
    questions = normalize_custom_questions((template or {}).get("questions") or [])
    duration_minutes = normalize_custom_duration_minutes(
        (template or {}).get("total_duration_minutes"),
        fallback=max(15, round(sum(question["target_seconds"] for question in questions) / 60)) if questions else 30,
    )
    title = str((template or {}).get("title") or "Custom Interview").strip() or "Custom Interview"
    description = str((template or {}).get("description") or "").strip()
    subtitle = description or (
        f"Custom interview with {len(questions)} user-defined question"
        f"{'' if len(questions) == 1 else 's'} and delivery-focused analytics."
    )

    return {
        "mode": "custom",
        "analytics_mode": "delivery_only",
        "template_id": (template or {}).get("template_id"),
        "title": title,
        "subtitle": subtitle,
        "duration_minutes": duration_minutes,
        "blueprint_label": "Custom flow",
        "primary_topic_id": "custom",
        "questions": [
            {
                "question_id": question["question_id"],
                "topic_id": "custom",
                "q": question["q"],
                "difficulty": "custom",
                "weight": question["weight"],
                "target_seconds": question["target_seconds"],
                "section_label": question["section_label"],
            }
            for question in questions
        ],
    }


def table_has_column(cursor, table_name, column_name):
    try:
        cursor.execute(f"SHOW COLUMNS FROM `{table_name}` LIKE %s", (column_name,))
        return cursor.fetchone() is not None
    except Error:
        return False


def table_exists(cursor, table_name):
    try:
        cursor.execute("SHOW TABLES LIKE %s", (table_name,))
        return cursor.fetchone() is not None
    except Error:
        return False


def load_role_topic_weights(connection, role_ids=None):
    if not connection or not connection.is_connected():
        return {}

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        if not table_exists(cursor, "role_topic_weights"):
            return {}

        query = """
            SELECT role_id, topic_id, weight
            FROM role_topic_weights
        """
        params = ()
        if role_ids:
            placeholders = ", ".join(["%s"] * len(role_ids))
            query += f" WHERE role_id IN ({placeholders})"
            params = tuple(role_ids)

        cursor.execute(query, params)
        rows = cursor.fetchall() or []
        result = {}
        for row in rows:
            result.setdefault(row["role_id"], {})[row["topic_id"]] = int(row.get("weight") or 0)
        return result
    except Error:
        return {}
    finally:
        if cursor:
            cursor.close()


def normalize_duration_minutes(duration_minutes):
    try:
        normalized = int(duration_minutes)
    except (TypeError, ValueError):
        normalized = 30

    if normalized not in DURATION_BLUEPRINTS:
        return 30

    return normalized


def build_question_id(topic_id, display_order):
    return f"{topic_id}_{int(display_order):03d}"


def seed_interview_catalog(cursor):
    question_bank = parse_question_bank()

    for topic in TOPIC_CATALOG:
        question_count = len(question_bank.get(topic["topic_id"], []))
        cursor.execute(
            """
            INSERT INTO topics (topic_id, category, title, subtitle, description, level_label, accent, question_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            category = VALUES(category),
            title = VALUES(title),
            subtitle = VALUES(subtitle),
            description = VALUES(description),
            level_label = VALUES(level_label),
            accent = VALUES(accent),
            question_count = VALUES(question_count)
            """,
            (
                topic["topic_id"],
                topic["category"],
                topic["title"],
                topic["subtitle"],
                topic["description"],
                topic["level_label"],
                topic["accent"],
                question_count,
            ),
        )

    for topic_id, items in question_bank.items():
        for display_order, item in enumerate(items, start=1):
            cursor.execute(
                """
                INSERT INTO questions (
                    question_id,
                    topic_id,
                    question_text,
                    difficulty,
                    display_order,
                    sample_answer,
                    ideal_answer
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                topic_id = VALUES(topic_id),
                question_text = VALUES(question_text),
                difficulty = VALUES(difficulty),
                display_order = VALUES(display_order),
                sample_answer = VALUES(sample_answer),
                ideal_answer = VALUES(ideal_answer),
                updated_at = CURRENT_TIMESTAMP
                """,
                (
                    build_question_id(topic_id, display_order),
                    topic_id,
                    item["question_text"],
                    item["difficulty"],
                    display_order,
                    item.get("sample_answer") or "",
                    item.get("ideal_answer") or "",
                ),
            )

    for role in ROLE_CATALOG:
        primary_topic_id = max(role["topic_weights"].items(), key=lambda entry: entry[1])[0]
        if table_has_column(cursor, "job_roles", "topic_weights"):
            cursor.execute(
                """
                INSERT INTO job_roles (
                    role_id,
                    title,
                    subtitle,
                    description,
                    level_label,
                    default_duration,
                    available_durations,
                    topic_weights,
                    primary_topic_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                subtitle = VALUES(subtitle),
                description = VALUES(description),
                level_label = VALUES(level_label),
                default_duration = VALUES(default_duration),
                available_durations = VALUES(available_durations),
                topic_weights = VALUES(topic_weights),
                primary_topic_id = VALUES(primary_topic_id),
                updated_at = CURRENT_TIMESTAMP
                """,
                (
                    role["role_id"],
                    role["title"],
                    role["subtitle"],
                    role["description"],
                    role["level_label"],
                    role["default_duration"],
                    json.dumps(role["available_durations"]),
                    json.dumps(role["topic_weights"]),
                    primary_topic_id,
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO job_roles (
                    role_id,
                    title,
                    subtitle,
                    description,
                    level_label,
                    default_duration_minutes,
                    available_durations,
                    is_active
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                subtitle = VALUES(subtitle),
                description = VALUES(description),
                level_label = VALUES(level_label),
                default_duration_minutes = VALUES(default_duration_minutes),
                available_durations = VALUES(available_durations),
                updated_at = CURRENT_TIMESTAMP
                """,
                (
                    role["role_id"],
                    role["title"],
                    role["subtitle"],
                    role["description"],
                    role["level_label"],
                    role["default_duration"],
                    json.dumps(role["available_durations"]),
                ),
            )

            if table_exists(cursor, "role_topic_weights"):
                for topic_id, weight in role["topic_weights"].items():
                    cursor.execute(
                        """
                        INSERT INTO role_topic_weights (role_id, topic_id, weight, is_core)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        weight = VALUES(weight),
                        is_core = VALUES(is_core)
                        """,
                        (role["role_id"], topic_id, weight, 1 if topic_id == primary_topic_id else 0),
                    )


def normalize_topic_row(row):
    return {
        "topic_id": row["topic_id"],
        "category": row["category"],
        "title": row["title"],
        "subtitle": row["subtitle"],
        "description": row["description"],
        "level_label": row["level_label"],
        "accent": row["accent"],
        "question_count": int(row.get("question_count") or 0),
        "is_active": bool(row.get("is_active", True)),
    }


def normalize_role_row(row, topic_weights_override=None):
    topic_weights = topic_weights_override or parse_json_field(row.get("topic_weights"), {})
    available_durations = parse_json_field(row.get("available_durations"), [15, 30, 60])
    topic_lookup = get_topic_catalog_lookup()
    focus_topics = [
        {
            "topic_id": topic_id,
            "title": topic_lookup.get(topic_id, {}).get("title", topic_id.replace("_", " ").title()),
            "weight": weight,
        }
        for topic_id, weight in sorted(topic_weights.items(), key=lambda entry: entry[1], reverse=True)
    ]

    return {
        "role_id": row["role_id"],
        "title": row["title"],
        "subtitle": row["subtitle"],
        "description": row["description"],
        "level_label": row["level_label"],
        "default_duration": int(row.get("default_duration") or row.get("default_duration_minutes") or 30),
        "available_durations": [int(value) for value in available_durations],
        "topic_weights": topic_weights,
        "focus_topics": focus_topics,
        "primary_topic_id": row.get("primary_topic_id") or (focus_topics[0]["topic_id"] if focus_topics else None),
        "is_active": bool(row.get("is_active", True)),
    }


def build_default_topic_catalog():
    question_bank = parse_question_bank()
    return [
        normalize_topic_row(
            {
                "topic_id": topic["topic_id"],
                "category": topic["category"],
                "title": topic["title"],
                "subtitle": topic["subtitle"],
                "description": topic["description"],
                "level_label": topic["level_label"],
                "accent": topic["accent"],
                "question_count": len(question_bank.get(topic["topic_id"], [])),
            }
        )
        for topic in TOPIC_CATALOG
    ]


def build_default_role_catalog():
    return [
        normalize_role_row(
            {
                "role_id": role["role_id"],
                "title": role["title"],
                "subtitle": role["subtitle"],
                "description": role["description"],
                "level_label": role["level_label"],
                "default_duration": role["default_duration"],
                "available_durations": role["available_durations"],
                "primary_topic_id": max(role["topic_weights"].items(), key=lambda entry: entry[1])[0],
            },
            role["topic_weights"],
        )
        for role in ROLE_CATALOG
    ]


def build_default_question_rows(topic_id):
    question_bank = parse_question_bank()
    items = question_bank.get(topic_id, [])
    return [
        normalize_question_row(
            {
                "question_id": build_question_id(topic_id, display_order),
                "topic_id": topic_id,
                "question_text": item["question_text"],
                "difficulty": item["difficulty"],
                "sample_answer": item.get("sample_answer") or "",
                "ideal_answer": item.get("ideal_answer") or "",
                "display_order": display_order,
            }
        )
        for display_order, item in enumerate(items, start=1)
    ]


def normalize_question_row(row):
    return {
        "question_id": row["question_id"],
        "topic_id": row["topic_id"],
        "question_text": row["question_text"],
        "difficulty": row.get("difficulty") or "medium",
        "sample_answer": row.get("sample_answer") or "",
        "ideal_answer": row.get("ideal_answer") or "",
        "display_order": int(row.get("display_order") or 0),
        "is_active": bool(row.get("is_active", True)),
    }


def build_unique_question_id(cursor, topic_id, display_order):
    base_id = build_question_id(topic_id, display_order)
    cursor.execute("SELECT question_id FROM questions WHERE question_id = %s", (base_id,))
    if cursor.fetchone() is None:
        return base_id
    return f"{base_id}_{str(uuid.uuid4())[:8]}"


def refresh_topic_question_counts(cursor, topic_ids):
    for topic_id in {value for value in (topic_ids or []) if value}:
        cursor.execute(
            """
            UPDATE topics
            SET question_count = (
                SELECT COUNT(*)
                FROM questions
                WHERE topic_id = %s AND is_active = TRUE
            )
            WHERE topic_id = %s
            """,
            (topic_id, topic_id),
                    )    


def seed_topic_study_materials(cursor):
    if not table_exists(cursor, "topic_study_materials"):
        return

    cursor.execute(
        """
        SELECT topic_id, title, subtitle, description
        FROM topics
        """
    )
    topic_rows = cursor.fetchall() or []

    for row in topic_rows:
        if isinstance(row, dict):
            topic_id = row["topic_id"]
            title = row["title"]
            subtitle = row.get("subtitle") or ""
            description = row.get("description") or ""
        else:
            topic_id, title, subtitle, description = row
        topic = {
            "topic_id": topic_id,
            "title": title,
            "subtitle": subtitle or "",
            "description": description or "",
        }
        cursor.execute(
            """
            SELECT question_text
            FROM questions
            WHERE topic_id = %s AND is_active = TRUE
            ORDER BY display_order ASC
            LIMIT 4
            """,
            (topic_id,),
        )
        prompt_rows = cursor.fetchall() or []
        material = build_default_study_material(
            topic,
            [
                {"question_text": prompt_row.get("question_text") if isinstance(prompt_row, dict) else prompt_row[0]}
                for prompt_row in prompt_rows
            ],
        )
        cursor.execute(
            """
            INSERT INTO topic_study_materials (
                topic_id,
                topic_title,
                overview,
                revision_notes,
                common_mistakes,
                rapid_fire_points,
                practice_prompts,
                estimated_minutes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            topic_title = VALUES(topic_title)
            """,
            (
                material["topic_id"],
                material["topic_title"],
                material["overview"],
                material["revision_notes"],
                material["common_mistakes"],
                json.dumps(material["rapid_fire_points"]),
                json.dumps(material["practice_prompts"]),
                material["estimated_minutes"],
            ),
        )


def init_database():
    """Initialize database and create tables."""
    connection = create_database_connection(include_database=False)
    if connection is None:
        return False

    cursor = None
    try:
        cursor = connection.cursor()
        database_name = get_db_config()["database"]
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}`")
        cursor.execute(f"USE `{database_name}`")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(36) UNIQUE NOT NULL,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                is_admin BOOLEAN NOT NULL DEFAULT FALSE,
                password_salt VARCHAR(32) NOT NULL,
                password_hash VARCHAR(128) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute("SHOW COLUMNS FROM users LIKE 'is_admin'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE AFTER email")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS interviews (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(64) UNIQUE NOT NULL,
                user_id VARCHAR(36) NULL,
                topic VARCHAR(100) NOT NULL,
                session_mode VARCHAR(20) NOT NULL DEFAULT 'topic',
                role_id VARCHAR(100) NULL,
                final_score INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                complete_data JSON NOT NULL,
                INDEX idx_interviews_user_id (user_id),
                INDEX idx_interviews_role_id (role_id),
                CONSTRAINT fk_interviews_user_id
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                    ON DELETE SET NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS topic_ratings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(64) UNIQUE NOT NULL,
                user_id VARCHAR(36) NULL,
                topic_id VARCHAR(100) NOT NULL,
                rating TINYINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_topic_ratings_topic_id (topic_id),
                INDEX idx_topic_ratings_user_id (user_id),
                CONSTRAINT fk_topic_ratings_session_id
                    FOREIGN KEY (session_id) REFERENCES interviews(session_id)
                    ON DELETE CASCADE,
                CONSTRAINT fk_topic_ratings_user_id
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                    ON DELETE SET NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS topic_activity (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(64) UNIQUE NOT NULL,
                user_id VARCHAR(36) NOT NULL,
                topic_id VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_topic_activity_topic_id (topic_id),
                INDEX idx_topic_activity_user_id (user_id),
                CONSTRAINT fk_topic_activity_session_id
                    FOREIGN KEY (session_id) REFERENCES interviews(session_id)
                    ON DELETE CASCADE,
                CONSTRAINT fk_topic_activity_user_id
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                    ON DELETE CASCADE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS topics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                topic_id VARCHAR(100) UNIQUE NOT NULL,
                category VARCHAR(100) NOT NULL,
                title VARCHAR(150) NOT NULL,
                subtitle VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                level_label VARCHAR(100) NOT NULL,
                accent VARCHAR(100) NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                question_count INT NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                question_id VARCHAR(100) UNIQUE NOT NULL,
                topic_id VARCHAR(100) NOT NULL,
                question_text TEXT NOT NULL,
                difficulty VARCHAR(20) NOT NULL,
                display_order INT NOT NULL,
                sample_answer TEXT NULL,
                ideal_answer TEXT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_questions_topic_id (topic_id),
                INDEX idx_questions_difficulty (difficulty),
                CONSTRAINT fk_questions_topic_id
                    FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
                    ON DELETE CASCADE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS job_roles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                role_id VARCHAR(100) UNIQUE NOT NULL,
                title VARCHAR(150) NOT NULL,
                subtitle VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                level_label VARCHAR(100) NOT NULL,
                default_duration INT NOT NULL DEFAULT 30,
                available_durations JSON NOT NULL,
                topic_weights JSON NOT NULL,
                primary_topic_id VARCHAR(100) NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS custom_interviews (
                id INT AUTO_INCREMENT PRIMARY KEY,
                template_id VARCHAR(64) UNIQUE NOT NULL,
                user_id VARCHAR(36) NOT NULL,
                title VARCHAR(160) NOT NULL,
                description TEXT NULL,
                total_duration_minutes INT NOT NULL DEFAULT 30,
                questions_json LONGTEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_custom_interviews_user_id (user_id),
                CONSTRAINT fk_custom_interviews_user_id
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                    ON DELETE CASCADE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS topic_study_materials (
                id INT AUTO_INCREMENT PRIMARY KEY,
                topic_id VARCHAR(100) UNIQUE NOT NULL,
                topic_title VARCHAR(150) NOT NULL,
                overview TEXT NOT NULL,
                revision_notes TEXT NOT NULL,
                common_mistakes TEXT NULL,
                rapid_fire_points JSON NOT NULL,
                practice_prompts JSON NOT NULL,
                estimated_minutes INT NOT NULL DEFAULT 20,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                CONSTRAINT fk_topic_study_materials_topic_id
                    FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
                    ON DELETE CASCADE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS study_plans (
                id INT AUTO_INCREMENT PRIMARY KEY,
                plan_id VARCHAR(64) UNIQUE NOT NULL,
                user_id VARCHAR(36) NOT NULL,
                role_id VARCHAR(100) NOT NULL,
                role_title VARCHAR(150) NOT NULL,
                title VARCHAR(180) NOT NULL,
                target_days INT NOT NULL DEFAULT 40,
                focus_topic_ids JSON NOT NULL,
                role_snapshot JSON NOT NULL,
                plan_summary JSON NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_study_plans_user_id (user_id),
                INDEX idx_study_plans_role_id (role_id),
                CONSTRAINT fk_study_plans_user_id
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                    ON DELETE CASCADE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS study_plan_steps (
                id INT AUTO_INCREMENT PRIMARY KEY,
                step_id VARCHAR(64) UNIQUE NOT NULL,
                plan_id VARCHAR(64) NOT NULL,
                sequence_no INT NOT NULL,
                phase_key VARCHAR(30) NOT NULL,
                step_type VARCHAR(30) NOT NULL,
                scheduled_day INT NOT NULL,
                scheduled_label VARCHAR(80) NOT NULL,
                topic_id VARCHAR(100) NULL,
                topic_title VARCHAR(150) NULL,
                role_id VARCHAR(100) NULL,
                role_title VARCHAR(150) NULL,
                question_ids JSON NULL,
                snapshot_json JSON NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'planned',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_study_plan_steps_plan_id (plan_id),
                INDEX idx_study_plan_steps_day (scheduled_day),
                INDEX idx_study_plan_steps_status (status),
                CONSTRAINT fk_study_plan_steps_plan_id
                    FOREIGN KEY (plan_id) REFERENCES study_plans(plan_id)
                    ON DELETE CASCADE
            )
            """
        )

        cursor.execute("SHOW COLUMNS FROM interviews LIKE 'user_id'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE interviews ADD COLUMN user_id VARCHAR(36) NULL AFTER session_id")

        cursor.execute("SHOW COLUMNS FROM topics LIKE 'is_active'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE topics ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE AFTER accent")

        cursor.execute("SHOW COLUMNS FROM job_roles LIKE 'is_active'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE job_roles ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE AFTER primary_topic_id")

        cursor.execute("SHOW COLUMNS FROM interviews LIKE 'session_mode'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE interviews ADD COLUMN session_mode VARCHAR(20) NOT NULL DEFAULT 'topic' AFTER topic")

        cursor.execute("SHOW COLUMNS FROM interviews LIKE 'role_id'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE interviews ADD COLUMN role_id VARCHAR(100) NULL AFTER session_mode")

        cursor.execute("SHOW INDEX FROM interviews WHERE Key_name = 'idx_interviews_user_id'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE interviews ADD INDEX idx_interviews_user_id (user_id)")

        cursor.execute("SHOW INDEX FROM interviews WHERE Key_name = 'idx_interviews_role_id'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE interviews ADD INDEX idx_interviews_role_id (role_id)")

        seed_interview_catalog(cursor)
        seed_topic_study_materials(cursor)

        connection.commit()
        logger.info("Database initialized successfully")
        return True
    except Error as exc:
        if exc.errno == 1826:
            # Constraint already exists from a previous schema run.
            logger.info("Database initialized successfully")
            return True
        logger.exception("Database initialization error")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def create_user(username, email, password):
    """Create a new user account."""
    username = username.strip()
    email = email.strip().lower()

    if not username or not email or not password:
        return {"success": False, "error": "Username, email, and password are required"}

    connection = create_database_connection()
    if connection is None:
        return {
            "success": False,
            "error": "Database connection failed",
            "detail": "Make sure the database server is running and the connection settings are correct.",
        }

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT username, email
            FROM users
            WHERE LOWER(username) = LOWER(%s) OR LOWER(email) = LOWER(%s)
            """,
            (username, email),
        )
        existing_user = cursor.fetchone()
        if existing_user:
            username_taken = existing_user["username"].lower() == username.lower()
            email_taken = existing_user["email"].lower() == email

            if username_taken and email_taken:
                error_message = "That username and email are already registered"
            elif username_taken:
                error_message = "That username is already taken"
            else:
                error_message = "That email is already registered"

            return {"success": False, "error": error_message}

        user_id = str(uuid.uuid4())
        salt, password_hash = hash_password(password)

        cursor.execute(
            """
            INSERT INTO users (user_id, username, email, password_salt, password_hash)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, username, email, salt, password_hash),
        )
        connection.commit()

        return {
            "success": True,
            "user": {
                "user_id": user_id,
                "username": username,
                "email": email,
                "is_admin": False,
            },
        }
    except Error as exc:
        if exc.errno == 1062:
            message = str(exc).lower()
            if "username" in message:
                return {"success": False, "error": "That username is already taken"}
            if "email" in message:
                return {"success": False, "error": "That email is already registered"}
            return {"success": False, "error": "That username or email already exists"}
        return database_failure(
            "Failed to create user",
            exc,
            detail="The account could not be created right now. Please try again in a moment.",
            username=username,
            email=email,
        )
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def authenticate_user(identifier, password):
    """Authenticate a user by username or email."""
    identifier = identifier.strip()

    connection = create_database_connection()
    if connection is None:
        return {
            "success": False,
            "error": "Database connection failed",
            "detail": "Make sure the database server is running and the connection settings are correct.",
        }

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT user_id, username, email, is_admin, password_salt, password_hash, created_at
            FROM users
            WHERE username = %s OR email = %s
            """,
            (identifier, identifier.lower()),
        )
        user = cursor.fetchone()

        if not user or not verify_password(password, user["password_salt"], user["password_hash"]):
            return {"success": False, "error": "Invalid credentials"}

        return {"success": True, "user": normalize_user_row(user)}
    except Error as exc:
        return database_failure(
            "Failed to authenticate user",
            exc,
            detail="Sign-in is temporarily unavailable. Please try again shortly.",
            identifier=identifier,
        )
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def get_user_by_id(user_id):
    """Fetch a user profile by user_id."""
    connection = create_database_connection()
    if connection is None:
        return None

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, username, email, is_admin, created_at FROM users WHERE user_id = %s",
            (user_id,),
        )
        return normalize_user_row(cursor.fetchone())
    except Error as exc:
        logger.exception("Database error loading user | user_id=%s", user_id)
        return None
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def get_user_interview_history(user_id, limit=20):
    """Fetch recent interview sessions for a user."""
    connection = create_database_connection()
    if connection is None:
        return []

    cursor = None
    try:
        safe_limit = max(1, min(int(limit), 50))
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT session_id, user_id, topic, session_mode, role_id, final_score, created_at, complete_data
            FROM interviews
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (user_id, safe_limit),
        )
        rows = cursor.fetchall() or []

        history = []
        for row in rows:
            details = {}
            raw_complete_data = row.get("complete_data")
            if raw_complete_data:
                if isinstance(raw_complete_data, dict):
                    details = raw_complete_data
                else:
                    try:
                        details = json.loads(raw_complete_data)
                    except (TypeError, json.JSONDecodeError):
                        details = {}

            questions = details.get("questions", []) if isinstance(details, dict) else []
            durations = details.get("durations", []) if isinstance(details, dict) else []
            total_duration = sum(durations) if durations else sum(
                question.get("duration", 0) for question in questions if isinstance(question, dict)
            )

            history.append(
                {
                    "session_id": row["session_id"],
                    "user_id": row["user_id"],
                    "topic": row["topic"],
                    "session_mode": row.get("session_mode") or "topic",
                    "role_id": row.get("role_id"),
                    "session_title": details.get("session_title"),
                    "final_score": row["final_score"],
                    "created_at": str(row["created_at"]) if row.get("created_at") else None,
                    "questions_total": details.get("questions_total") or len(questions),
                    "duration_seconds": round(total_duration, 1) if total_duration else 0,
                    "interview_date": details.get("interview_date"),
                }
            )

        return history
    except Error as exc:
        logger.exception("Database error loading history | user_id=%s", user_id)
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def list_all_topics():
    connection = create_database_connection()
    if connection is None:
        return build_default_topic_catalog()

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT topic_id, category, title, subtitle, description, level_label, accent, question_count, is_active
            FROM topics
            ORDER BY is_active DESC, title ASC
            """
        )
        rows = cursor.fetchall() or []
        return [normalize_topic_row(row) for row in rows]
    except Error as exc:
        logger.exception("Database error loading all topics")
        return build_default_topic_catalog()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def list_all_questions():
    connection = create_database_connection()
    if connection is None:
        return []

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT question_id, topic_id, question_text, difficulty, sample_answer, ideal_answer, display_order, is_active
            FROM questions
            ORDER BY is_active DESC, topic_id ASC, display_order ASC, question_id ASC
            """
        )
        rows = cursor.fetchall() or []
        return [normalize_question_row(row) for row in rows]
    except Error as exc:
        logger.exception("Database error loading all questions")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def list_all_roles():
    connection = create_database_connection()
    if connection is None:
        return build_default_role_catalog()

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM job_roles ORDER BY is_active DESC, title ASC")
        rows = cursor.fetchall() or []
        if not rows:
            return []
        weights_by_role = load_role_topic_weights(connection, [row["role_id"] for row in rows])
        return [normalize_role_row(row, weights_by_role.get(row["role_id"])) for row in rows]
    except Error as exc:
        logger.exception("Database error loading all roles")
        return build_default_role_catalog()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def get_admin_dashboard_snapshot(user_limit=20, session_limit=12):
    connection = create_database_connection()
    if connection is None:
        return {
            "overview": {
                "total_users": 0,
                "admin_users": 0,
                "total_sessions": 0,
                "active_users_7d": 0,
                "sessions_7d": 0,
                "custom_templates": 0,
                "average_score": 0,
            },
            "mode_breakdown": [],
            "top_topics": [],
            "recent_sessions": [],
            "users": [],
        }

    cursor = None
    try:
        safe_user_limit = max(1, min(int(user_limit), 50))
        safe_session_limit = max(1, min(int(session_limit), 50))
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_users,
                SUM(CASE WHEN is_admin = TRUE THEN 1 ELSE 0 END) AS admin_users
            FROM users
            """
        )
        user_counts = cursor.fetchone() or {}

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_sessions,
                SUM(CASE WHEN created_at >= (UTC_TIMESTAMP() - INTERVAL 7 DAY) THEN 1 ELSE 0 END) AS sessions_7d,
                COUNT(DISTINCT CASE WHEN created_at >= (UTC_TIMESTAMP() - INTERVAL 7 DAY) AND user_id IS NOT NULL THEN user_id END) AS active_users_7d,
                AVG(final_score) AS average_score
            FROM interviews
            """
        )
        session_counts = cursor.fetchone() or {}

        cursor.execute("SELECT COUNT(*) AS custom_templates FROM custom_interviews")
        template_counts = cursor.fetchone() or {}

        cursor.execute(
            """
            SELECT
                COALESCE(session_mode, 'topic') AS session_mode,
                COUNT(*) AS session_count,
                AVG(final_score) AS average_score
            FROM interviews
            GROUP BY COALESCE(session_mode, 'topic')
            ORDER BY session_count DESC, session_mode ASC
            """
        )
        mode_rows = cursor.fetchall() or []

        cursor.execute(
            """
            SELECT
                topic,
                COUNT(*) AS session_count,
                AVG(final_score) AS average_score,
                MAX(created_at) AS latest_session_at
            FROM interviews
            WHERE topic IS NOT NULL AND topic != ''
            GROUP BY topic
            ORDER BY session_count DESC, average_score DESC, topic ASC
            LIMIT 8
            """
        )
        topic_rows = cursor.fetchall() or []

        cursor.execute(
            """
            SELECT
                interviews.session_id,
                interviews.user_id,
                interviews.topic,
                interviews.session_mode,
                interviews.role_id,
                interviews.final_score,
                interviews.created_at,
                interviews.complete_data,
                users.username,
                users.email
            FROM interviews
            LEFT JOIN users ON users.user_id = interviews.user_id
            ORDER BY interviews.created_at DESC
            LIMIT %s
            """,
            (safe_session_limit,),
        )
        recent_session_rows = cursor.fetchall() or []

        cursor.execute(
            """
            SELECT
                users.user_id,
                users.username,
                users.email,
                users.is_admin,
                users.created_at,
                COUNT(interviews.session_id) AS session_count,
                AVG(interviews.final_score) AS average_score,
                MAX(interviews.created_at) AS latest_session_at,
                SUM(CASE WHEN interviews.created_at >= (UTC_TIMESTAMP() - INTERVAL 7 DAY) THEN 1 ELSE 0 END) AS sessions_7d
            FROM users
            LEFT JOIN interviews ON interviews.user_id = users.user_id
            GROUP BY users.user_id, users.username, users.email, users.is_admin, users.created_at
            ORDER BY latest_session_at DESC, users.created_at DESC
            LIMIT %s
            """,
            (safe_user_limit,),
        )
        user_rows = cursor.fetchall() or []

        recent_sessions = []
        for row in recent_session_rows:
            details = parse_json_field(row.get("complete_data"), {})
            questions = details.get("questions", []) if isinstance(details, dict) else []
            recent_sessions.append(
                {
                    "session_id": row["session_id"],
                    "user_id": row.get("user_id"),
                    "username": row.get("username") or "Guest",
                    "email": row.get("email") or "",
                    "topic": row.get("topic") or "",
                    "session_mode": row.get("session_mode") or "topic",
                    "role_id": row.get("role_id"),
                    "session_title": details.get("session_title") or details.get("title") or "",
                    "final_score": int(row.get("final_score") or 0),
                    "questions_total": int(details.get("questions_total") or len(questions) or 0),
                    "created_at": str(row.get("created_at")) if row.get("created_at") else None,
                }
            )

        users = [
            {
                "user_id": row["user_id"],
                "username": row["username"],
                "email": row["email"],
                "is_admin": coerce_boolean_flag(row.get("is_admin")),
                "created_at": str(row.get("created_at")) if row.get("created_at") else None,
                "session_count": int(row.get("session_count") or 0),
                "sessions_7d": int(row.get("sessions_7d") or 0),
                "average_score": round(float(row.get("average_score") or 0), 1) if row.get("average_score") is not None else 0,
                "latest_session_at": str(row.get("latest_session_at")) if row.get("latest_session_at") else None,
            }
            for row in user_rows
        ]

        return {
            "overview": {
                "total_users": int(user_counts.get("total_users") or 0),
                "admin_users": int(user_counts.get("admin_users") or 0),
                "total_sessions": int(session_counts.get("total_sessions") or 0),
                "active_users_7d": int(session_counts.get("active_users_7d") or 0),
                "sessions_7d": int(session_counts.get("sessions_7d") or 0),
                "custom_templates": int(template_counts.get("custom_templates") or 0),
                "average_score": round(float(session_counts.get("average_score") or 0), 1) if session_counts.get("average_score") is not None else 0,
            },
            "mode_breakdown": [
                {
                    "session_mode": row.get("session_mode") or "topic",
                    "session_count": int(row.get("session_count") or 0),
                    "average_score": round(float(row.get("average_score") or 0), 1) if row.get("average_score") is not None else 0,
                }
                for row in mode_rows
            ],
            "top_topics": [
                {
                    "topic": row.get("topic") or "",
                    "session_count": int(row.get("session_count") or 0),
                    "average_score": round(float(row.get("average_score") or 0), 1) if row.get("average_score") is not None else 0,
                    "latest_session_at": str(row.get("latest_session_at")) if row.get("latest_session_at") else None,
                }
                for row in topic_rows
            ],
            "recent_sessions": recent_sessions,
            "users": users,
        }
    except Error as exc:
        logger.exception("Database error loading admin dashboard snapshot")
        return {
            "overview": {
                "total_users": 0,
                "admin_users": 0,
                "total_sessions": 0,
                "active_users_7d": 0,
                "sessions_7d": 0,
                "custom_templates": 0,
                "average_score": 0,
            },
            "mode_breakdown": [],
            "top_topics": [],
            "recent_sessions": [],
            "users": [],
        }
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def save_topic_record(payload, topic_id=None):
    resolved_topic_id = str(topic_id or payload.get("topic_id") or "").strip()
    if not resolved_topic_id:
        return {"success": False, "error": "Topic ID is required"}

    title = str(payload.get("title") or "").strip()
    if not title:
        return {"success": False, "error": "Topic title is required"}

    category = str(payload.get("category") or "").strip() or "General"
    subtitle = str(payload.get("subtitle") or "").strip() or title
    description = str(payload.get("description") or "").strip() or subtitle
    level_label = str(payload.get("level_label") or "").strip() or "Intermediate"
    accent = str(payload.get("accent") or "").strip() or resolved_topic_id.lower().replace(" ", "")

    connection = create_database_connection()
    if connection is None:
        return {
            "success": False,
            "error": "Database connection failed",
            "detail": "The topic could not be saved because the database is unavailable.",
        }

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT question_count FROM topics WHERE topic_id = %s", (resolved_topic_id,))
        existing_topic = cursor.fetchone()
        question_count = int((existing_topic or {}).get("question_count") or 0)

        cursor.execute(
            """
            INSERT INTO topics (topic_id, category, title, subtitle, description, level_label, accent, question_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            category = VALUES(category),
            title = VALUES(title),
            subtitle = VALUES(subtitle),
            description = VALUES(description),
            level_label = VALUES(level_label),
            accent = VALUES(accent),
            updated_at = CURRENT_TIMESTAMP
            """,
            (
                resolved_topic_id,
                category,
                title,
                subtitle,
                description,
                level_label,
                accent,
                question_count,
            ),
        )
        connection.commit()
        topic = get_topic_by_id(resolved_topic_id, include_inactive=True)
        return {"success": True, "topic": topic}
    except Error as exc:
        return database_failure(
            "Failed to save topic",
            exc,
            detail="The topic record could not be written to the database.",
            topic_id=resolved_topic_id,
        )
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def save_question_record(payload, question_id=None):
    topic_id = str(payload.get("topic_id") or "").strip()
    if not topic_id:
        return {"success": False, "error": "Topic ID is required for a question"}

    if not get_topic_by_id(topic_id, include_inactive=True):
        return {
            "success": False,
            "error": "Selected topic does not exist",
            "detail": "Choose an existing topic before creating or moving a question.",
        }

    question_text = str(payload.get("question_text") or "").strip()
    if not question_text:
        return {"success": False, "error": "Question text is required"}

    difficulty = str(payload.get("difficulty") or "medium").strip().lower()
    if difficulty not in {"easy", "medium", "hard", "custom"}:
        difficulty = "medium"

    try:
        display_order = int(payload.get("display_order") or 1)
    except (TypeError, ValueError):
        display_order = 1
    display_order = max(1, display_order)

    sample_answer = str(payload.get("sample_answer") or "").strip()
    ideal_answer = str(payload.get("ideal_answer") or "").strip()
    old_topic_id = None
    resolved_question_id = str(question_id or payload.get("question_id") or "").strip()

    connection = create_database_connection()
    if connection is None:
        return {
            "success": False,
            "error": "Database connection failed",
            "detail": "The question could not be saved because the database is unavailable.",
        }

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        if resolved_question_id:
            cursor.execute("SELECT topic_id FROM questions WHERE question_id = %s", (resolved_question_id,))
            existing = cursor.fetchone()
            old_topic_id = existing["topic_id"] if existing else None

        if not resolved_question_id:
            resolved_question_id = build_unique_question_id(cursor, topic_id, display_order)

        cursor.execute(
            """
            INSERT INTO questions (
                question_id, topic_id, question_text, difficulty, display_order, sample_answer, ideal_answer
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            topic_id = VALUES(topic_id),
            question_text = VALUES(question_text),
            difficulty = VALUES(difficulty),
            display_order = VALUES(display_order),
            sample_answer = VALUES(sample_answer),
            ideal_answer = VALUES(ideal_answer),
            updated_at = CURRENT_TIMESTAMP
            """,
            (
                resolved_question_id,
                topic_id,
                question_text,
                difficulty,
                display_order,
                sample_answer,
                ideal_answer,
            ),
        )
        refresh_topic_question_counts(cursor, [topic_id, old_topic_id])
        connection.commit()
        questions = list_all_questions()
        question = next((item for item in questions if item["question_id"] == resolved_question_id), None)
        return {"success": True, "question": question}
    except Error as exc:
        return database_failure(
            "Failed to save question",
            exc,
            detail="The question record could not be written to the database.",
            question_id=question_id or resolved_question_id,
            topic_id=topic_id,
        )
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def save_role_record(payload, role_id=None):
    resolved_role_id = str(role_id or payload.get("role_id") or "").strip()
    if not resolved_role_id:
        return {"success": False, "error": "Role ID is required"}

    title = str(payload.get("title") or "").strip()
    if not title:
        return {"success": False, "error": "Role title is required"}

    subtitle = str(payload.get("subtitle") or "").strip() or title
    description = str(payload.get("description") or "").strip() or subtitle
    level_label = str(payload.get("level_label") or "").strip() or "Interview loop"

    try:
        default_duration = int(payload.get("default_duration") or 30)
    except (TypeError, ValueError):
        default_duration = 30
    default_duration = max(5, min(default_duration, 240))

    raw_durations = payload.get("available_durations") or [15, 30, 60]
    if isinstance(raw_durations, str):
        raw_durations = [value.strip() for value in raw_durations.split(",") if value.strip()]

    available_durations = []
    for value in raw_durations:
        try:
            available_durations.append(int(value))
        except (TypeError, ValueError):
            continue
    available_durations = sorted({max(5, min(duration, 240)) for duration in available_durations}) or [15, 30, 60]

    raw_topic_weights = payload.get("topic_weights") or {}
    if isinstance(raw_topic_weights, str):
        raw_topic_weights = parse_json_field(raw_topic_weights, {})

    topic_weights = {}
    if isinstance(raw_topic_weights, dict):
        for topic_key, weight_value in raw_topic_weights.items():
            try:
                numeric_weight = int(weight_value)
            except (TypeError, ValueError):
                continue
            if numeric_weight > 0:
                topic_weights[str(topic_key).strip()] = numeric_weight

    if not topic_weights:
        return {"success": False, "error": "Add at least one topic weight greater than zero"}

    invalid_topic_ids = [
        topic_key for topic_key in topic_weights
        if not get_topic_by_id(topic_key, include_inactive=True)
    ]
    if invalid_topic_ids:
        invalid_label = ", ".join(invalid_topic_ids[:4])
        suffix = "" if len(invalid_topic_ids) <= 4 else ", ..."
        return {
            "success": False,
            "error": "One or more selected topics do not exist",
            "detail": f"Unknown topic IDs: {invalid_label}{suffix}",
        }

    primary_topic_id = str(payload.get("primary_topic_id") or "").strip()
    if not primary_topic_id or primary_topic_id not in topic_weights:
        primary_topic_id = max(topic_weights.items(), key=lambda item: item[1])[0]

    connection = create_database_connection()
    if connection is None:
        return {
            "success": False,
            "error": "Database connection failed",
            "detail": "The role could not be saved because the database is unavailable.",
        }

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            INSERT INTO job_roles (
                role_id, title, subtitle, description, level_label, default_duration, available_durations, topic_weights, primary_topic_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            subtitle = VALUES(subtitle),
            description = VALUES(description),
            level_label = VALUES(level_label),
            default_duration = VALUES(default_duration),
            available_durations = VALUES(available_durations),
            topic_weights = VALUES(topic_weights),
            primary_topic_id = VALUES(primary_topic_id),
            updated_at = CURRENT_TIMESTAMP
            """,
            (
                resolved_role_id,
                title,
                subtitle,
                description,
                level_label,
                default_duration,
                json.dumps(available_durations),
                json.dumps(topic_weights),
                primary_topic_id,
            ),
        )
        connection.commit()
        role = get_role_by_id(resolved_role_id, include_inactive=True)
        return {"success": True, "role": role}
    except Error as exc:
        return database_failure(
            "Failed to save role",
            exc,
            detail="The role record could not be written to the database.",
            role_id=resolved_role_id,
        )
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def find_role_dependencies_for_topic(topic_id):
    dependent_roles = []
    for role in list_all_roles():
        if topic_id in (role.get("topic_weights") or {}):
            dependent_roles.append(
                {
                    "role_id": role["role_id"],
                    "title": role["title"],
                    "is_active": bool(role.get("is_active", True)),
                }
            )
    return dependent_roles


def archive_topic_record(topic_id, is_active):
    resolved_topic_id = str(topic_id or "").strip()
    if not resolved_topic_id:
        return {"success": False, "error": "Topic ID is required"}

    if not is_active:
        dependent_roles = [role for role in find_role_dependencies_for_topic(resolved_topic_id) if role.get("is_active")]
        if dependent_roles:
            role_titles = ", ".join(role["title"] for role in dependent_roles[:3])
            suffix = "" if len(dependent_roles) <= 3 else ", ..."
            return {
                "success": False,
                "error": f"Remove this topic from active role weights before archiving it. Used by: {role_titles}{suffix}",
            }

    connection = create_database_connection()
    if connection is None:
        return {
            "success": False,
            "error": "Database connection failed",
            "detail": "The topic status could not be updated because the database is unavailable.",
        }

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE topics SET is_active = %s WHERE topic_id = %s", (bool(is_active), resolved_topic_id))
        connection.commit()
        if cursor.rowcount <= 0:
            return {"success": False, "error": "Topic not found"}
        topic = get_topic_by_id(resolved_topic_id, include_inactive=True)
        return {"success": True, "topic": topic}
    except Error as exc:
        return database_failure(
            "Failed to update topic status",
            exc,
            detail="The topic archive state could not be updated.",
            topic_id=resolved_topic_id,
            is_active=is_active,
        )
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def delete_topic_record(topic_id):
    resolved_topic_id = str(topic_id or "").strip()
    if not resolved_topic_id:
        return {"success": False, "error": "Topic ID is required"}

    dependent_roles = [role for role in find_role_dependencies_for_topic(resolved_topic_id) if role.get("is_active")]
    if dependent_roles:
        role_titles = ", ".join(role["title"] for role in dependent_roles[:3])
        suffix = "" if len(dependent_roles) <= 3 else ", ..."
        return {
            "success": False,
            "error": f"Remove this topic from active role weights before deleting it. Used by: {role_titles}{suffix}",
        }

    connection = create_database_connection()
    if connection is None:
        return {
            "success": False,
            "error": "Database connection failed",
            "detail": "The topic could not be deleted because the database is unavailable.",
        }

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM topics WHERE topic_id = %s", (resolved_topic_id,))
        connection.commit()
        if cursor.rowcount <= 0:
            return {"success": False, "error": "Topic not found"}
        return {"success": True}
    except Error as exc:
        return database_failure(
            "Failed to delete topic",
            exc,
            detail="The topic record could not be deleted from the database.",
            topic_id=resolved_topic_id,
        )
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def archive_question_record(question_id, is_active):
    resolved_question_id = str(question_id or "").strip()
    if not resolved_question_id:
        return {"success": False, "error": "Question ID is required"}

    connection = create_database_connection()
    if connection is None:
        return {
            "success": False,
            "error": "Database connection failed",
            "detail": "The question status could not be updated because the database is unavailable.",
        }

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT topic_id FROM questions WHERE question_id = %s", (resolved_question_id,))
        row = cursor.fetchone()
        if not row:
            return {"success": False, "error": "Question not found"}
        topic_id = row["topic_id"]
        cursor.execute("UPDATE questions SET is_active = %s WHERE question_id = %s", (bool(is_active), resolved_question_id))
        refresh_topic_question_counts(cursor, [topic_id])
        connection.commit()
        question = next((item for item in list_all_questions() if item["question_id"] == resolved_question_id), None)
        return {"success": True, "question": question}
    except Error as exc:
        return database_failure(
            "Failed to update question status",
            exc,
            detail="The question archive state could not be updated.",
            question_id=resolved_question_id,
            is_active=is_active,
        )
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def delete_question_record(question_id):
    resolved_question_id = str(question_id or "").strip()
    if not resolved_question_id:
        return {"success": False, "error": "Question ID is required"}

    connection = create_database_connection()
    if connection is None:
        return {
            "success": False,
            "error": "Database connection failed",
            "detail": "The question could not be deleted because the database is unavailable.",
        }

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT topic_id FROM questions WHERE question_id = %s", (resolved_question_id,))
        row = cursor.fetchone()
        if not row:
            return {"success": False, "error": "Question not found"}
        topic_id = row["topic_id"]
        cursor.execute("DELETE FROM questions WHERE question_id = %s", (resolved_question_id,))
        refresh_topic_question_counts(cursor, [topic_id])
        connection.commit()
        return {"success": True}
    except Error as exc:
        return database_failure(
            "Failed to delete question",
            exc,
            detail="The question record could not be deleted from the database.",
            question_id=resolved_question_id,
        )
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def archive_role_record(role_id, is_active):
    resolved_role_id = str(role_id or "").strip()
    if not resolved_role_id:
        return {"success": False, "error": "Role ID is required"}

    connection = create_database_connection()
    if connection is None:
        return {
            "success": False,
            "error": "Database connection failed",
            "detail": "The role status could not be updated because the database is unavailable.",
        }

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE job_roles SET is_active = %s WHERE role_id = %s", (bool(is_active), resolved_role_id))
        connection.commit()
        if cursor.rowcount <= 0:
            return {"success": False, "error": "Role not found"}
        role = get_role_by_id(resolved_role_id, include_inactive=True)
        return {"success": True, "role": role}
    except Error as exc:
        return database_failure(
            "Failed to update role status",
            exc,
            detail="The role archive state could not be updated.",
            role_id=resolved_role_id,
            is_active=is_active,
        )
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def delete_role_record(role_id):
    resolved_role_id = str(role_id or "").strip()
    if not resolved_role_id:
        return {"success": False, "error": "Role ID is required"}

    connection = create_database_connection()
    if connection is None:
        return {
            "success": False,
            "error": "Database connection failed",
            "detail": "The role could not be deleted because the database is unavailable.",
        }

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM job_roles WHERE role_id = %s", (resolved_role_id,))
        connection.commit()
        if cursor.rowcount <= 0:
            return {"success": False, "error": "Role not found"}
        return {"success": True}
    except Error as exc:
        return database_failure(
            "Failed to delete role",
            exc,
            detail="The role record could not be deleted from the database.",
            role_id=resolved_role_id,
        )
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def list_custom_interviews(user_id):
    connection = create_database_connection()
    if connection is None:
        return []

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT template_id, user_id, title, description, total_duration_minutes, questions_json, created_at, updated_at
            FROM custom_interviews
            WHERE user_id = %s
            ORDER BY updated_at DESC, created_at DESC
            """,
            (user_id,),
        )
        rows = cursor.fetchall() or []
        return [normalize_custom_interview_row(row) for row in rows]
    except Error as exc:
        print(f"Database error loading custom interviews: {exc}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def get_custom_interview(template_id, user_id=None):
    connection = create_database_connection()
    if connection is None:
        return None

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        if user_id:
            cursor.execute(
                """
                SELECT template_id, user_id, title, description, total_duration_minutes, questions_json, created_at, updated_at
                FROM custom_interviews
                WHERE template_id = %s AND user_id = %s
                LIMIT 1
                """,
                (template_id, user_id),
            )
        else:
            cursor.execute(
                """
                SELECT template_id, user_id, title, description, total_duration_minutes, questions_json, created_at, updated_at
                FROM custom_interviews
                WHERE template_id = %s
                LIMIT 1
                """,
                (template_id,),
            )

        row = cursor.fetchone()
        return normalize_custom_interview_row(row) if row else None
    except Error as exc:
        print(f"Database error loading custom interview {template_id}: {exc}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def save_custom_interview(user_id, payload, template_id=None):
    if not user_id:
        return {"success": False, "error": "Authentication required"}

    title = str((payload or {}).get("title") or "").strip()
    if not title:
        return {"success": False, "error": "Interview title is required"}

    normalized_questions = normalize_custom_questions((payload or {}).get("questions") or [])
    if not normalized_questions:
        return {"success": False, "error": "Add at least one valid question"}

    duration_minutes = normalize_custom_duration_minutes(
        (payload or {}).get("total_duration_minutes"),
        fallback=max(15, round(sum(question["target_seconds"] for question in normalized_questions) / 60)),
    )
    description = str((payload or {}).get("description") or "").strip()
    resolved_template_id = template_id or str(uuid.uuid4())

    connection = create_database_connection()
    if connection is None:
        return {"success": False, "error": "Database connection failed"}

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)

        if template_id:
            cursor.execute(
                "SELECT template_id FROM custom_interviews WHERE template_id = %s AND user_id = %s",
                (template_id, user_id),
            )
            if cursor.fetchone() is None:
                return {"success": False, "error": "Custom interview not found"}

        cursor.execute(
            """
            INSERT INTO custom_interviews (
                template_id, user_id, title, description, total_duration_minutes, questions_json
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            description = VALUES(description),
            total_duration_minutes = VALUES(total_duration_minutes),
            questions_json = VALUES(questions_json),
            updated_at = CURRENT_TIMESTAMP
            """,
            (
                resolved_template_id,
                user_id,
                title,
                description,
                duration_minutes,
                json.dumps(normalized_questions),
            ),
        )
        connection.commit()

        template = get_custom_interview(resolved_template_id, user_id=user_id)
        return {"success": True, "template": template}
    except Error as exc:
        print(f"Database error saving custom interview: {exc}")
        return {"success": False, "error": "Failed to save custom interview"}
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def delete_custom_interview(user_id, template_id):
    connection = create_database_connection()
    if connection is None:
        return {"success": False, "error": "Database connection failed"}

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM custom_interviews WHERE template_id = %s AND user_id = %s",
            (template_id, user_id),
        )
        connection.commit()
        if cursor.rowcount <= 0:
            return {"success": False, "error": "Custom interview not found"}
        return {"success": True}
    except Error as exc:
        print(f"Database error deleting custom interview {template_id}: {exc}")
        return {"success": False, "error": "Failed to delete custom interview"}
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def get_custom_interview_session_plan(template_id, user_id):
    template = get_custom_interview(template_id, user_id=user_id)
    if not template:
        return None
    return build_custom_interview_plan(template)


def save_topic_rating(session_id, topic_id, rating, user_id=None):
    """Create or update a rating for an interview session."""
    connection = create_database_connection()
    if connection is None:
        return {"success": False, "error": "Database connection failed"}

    cursor = None
    try:
        numeric_rating = int(rating)
    except (TypeError, ValueError):
        return {"success": False, "error": "Rating must be a number from 1 to 5"}

    if numeric_rating < 1 or numeric_rating > 5:
        return {"success": False, "error": "Rating must be between 1 and 5"}

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT session_id, topic, user_id FROM interviews WHERE session_id = %s",
            (session_id,),
        )
        interview = cursor.fetchone()

        if not interview:
            return {"success": False, "error": "Interview session not found"}

        resolved_topic = topic_id or interview["topic"]
        resolved_user_id = user_id or interview.get("user_id")

        cursor.execute(
            """
            INSERT INTO topic_ratings (session_id, user_id, topic_id, rating)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            user_id = VALUES(user_id),
            topic_id = VALUES(topic_id),
            rating = VALUES(rating)
            """,
            (session_id, resolved_user_id, resolved_topic, numeric_rating),
        )
        connection.commit()

        summary = get_topic_rating_summary(resolved_topic)
        return {"success": True, "summary": summary}
    except Error as exc:
        print(f"Database error saving topic rating: {exc}")
        return {"success": False, "error": "Failed to save rating"}
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def get_topic_rating_summary(topic_id=None):
    """Return aggregate topic ratings."""
    connection = create_database_connection()
    if connection is None:
        return {} if topic_id else []

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)

        if topic_id:
            cursor.execute(
                """
                SELECT topic_id, ROUND(AVG(rating), 1) AS average_rating, COUNT(*) AS rating_count
                FROM topic_ratings
                WHERE topic_id = %s
                GROUP BY topic_id
                """,
                (topic_id,),
            )
            row = cursor.fetchone()
            if not row:
                return {"topic_id": topic_id, "average_rating": None, "rating_count": 0}

            return {
                "topic_id": row["topic_id"],
                "average_rating": float(row["average_rating"]) if row["average_rating"] is not None else None,
                "rating_count": int(row["rating_count"] or 0),
            }

        cursor.execute(
            """
            SELECT topic_id, ROUND(AVG(rating), 1) AS average_rating, COUNT(*) AS rating_count
            FROM topic_ratings
            GROUP BY topic_id
            """
        )
        rows = cursor.fetchall() or []
        return [
            {
                "topic_id": row["topic_id"],
                "average_rating": float(row["average_rating"]) if row["average_rating"] is not None else None,
                "rating_count": int(row["rating_count"] or 0),
            }
            for row in rows
        ]
    except Error as exc:
        print(f"Database error loading topic ratings: {exc}")
        return {} if topic_id else []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def sync_topic_activity(session_id, topic_id, user_id=None):
    """Track completed signed-in interviews per topic."""
    connection = create_database_connection()
    if connection is None:
        return False

    cursor = None
    try:
        cursor = connection.cursor()

        if not user_id:
            cursor.execute("DELETE FROM topic_activity WHERE session_id = %s", (session_id,))
            connection.commit()
            return True

        cursor.execute(
            """
            INSERT INTO topic_activity (session_id, user_id, topic_id)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
            user_id = VALUES(user_id),
            topic_id = VALUES(topic_id)
            """,
            (session_id, user_id, topic_id),
        )
        connection.commit()
        return True
    except Error as exc:
        print(f"Database error syncing topic activity: {exc}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def get_topic_activity_summary(topic_id=None):
    """Return signed-in interview counts per topic."""
    connection = create_database_connection()
    if connection is None:
        return {} if topic_id else []

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)

        if topic_id:
            cursor.execute(
                """
                SELECT topic_id, COUNT(*) AS interview_count
                FROM topic_activity
                WHERE topic_id = %s
                GROUP BY topic_id
                """,
                (topic_id,),
            )
            row = cursor.fetchone()
            if not row:
                return {"topic_id": topic_id, "interview_count": 0}

            return {
                "topic_id": row["topic_id"],
                "interview_count": int(row["interview_count"] or 0),
            }

        cursor.execute(
            """
            SELECT topic_id, COUNT(*) AS interview_count
            FROM topic_activity
            GROUP BY topic_id
            """
        )
        rows = cursor.fetchall() or []
        return [
            {
                "topic_id": row["topic_id"],
                "interview_count": int(row["interview_count"] or 0),
            }
            for row in rows
        ]
    except Error as exc:
        print(f"Database error loading topic activity: {exc}")
        return {} if topic_id else []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def get_topic_catalog():
    connection = create_database_connection()
    if connection is None:
        return build_default_topic_catalog()

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT topic_id, category, title, subtitle, description, level_label, accent, question_count, is_active
            FROM topics
            WHERE is_active = TRUE
            ORDER BY title ASC
            """
        )
        rows = cursor.fetchall() or []
        return [normalize_topic_row(row) for row in rows]
    except Error as exc:
        print(f"Database error loading topic catalog: {exc}")
        return build_default_topic_catalog()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def get_role_catalog():
    connection = create_database_connection()
    if connection is None:
        return build_default_role_catalog()

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM job_roles WHERE is_active = TRUE ORDER BY title ASC")
        rows = cursor.fetchall() or []
        if not rows:
            return []
        weights_by_role = load_role_topic_weights(connection, [row["role_id"] for row in rows])
        return [normalize_role_row(row, weights_by_role.get(row["role_id"])) for row in rows]
    except Error as exc:
        print(f"Database error loading role catalog: {exc}")
        return build_default_role_catalog()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def get_questions_for_topic(topic_id):
    connection = create_database_connection()
    if connection is None:
        return build_default_question_rows(topic_id)

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT question_id, topic_id, question_text, difficulty, sample_answer, ideal_answer, display_order, is_active
            FROM questions
            WHERE topic_id = %s AND is_active = TRUE
            ORDER BY display_order ASC
            """,
            (topic_id,),
        )
        rows = cursor.fetchall() or []
        return [normalize_question_row(row) for row in rows]
    except Error as exc:
        print(f"Database error loading questions for topic {topic_id}: {exc}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def get_role_by_id(role_id, include_inactive=False):
    connection = create_database_connection()
    if connection is None:
        fallback_role = get_role_catalog_lookup().get(role_id)
        return normalize_role_row(
            {
                "role_id": fallback_role["role_id"],
                "title": fallback_role["title"],
                "subtitle": fallback_role["subtitle"],
                "description": fallback_role["description"],
                "level_label": fallback_role["level_label"],
                "default_duration": fallback_role["default_duration"],
                "available_durations": fallback_role["available_durations"],
                "primary_topic_id": max(fallback_role["topic_weights"].items(), key=lambda entry: entry[1])[0],
            },
            fallback_role["topic_weights"],
        ) if fallback_role else None

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        if include_inactive:
            cursor.execute("SELECT * FROM job_roles WHERE role_id = %s", (role_id,))
        else:
            cursor.execute("SELECT * FROM job_roles WHERE role_id = %s AND is_active = TRUE", (role_id,))
        row = cursor.fetchone()
        if not row:
            return None
        weights_by_role = load_role_topic_weights(connection, [role_id])
        return normalize_role_row(row, weights_by_role.get(role_id))
    except Error as exc:
        print(f"Database error loading role {role_id}: {exc}")
        fallback_role = get_role_catalog_lookup().get(role_id)
        return normalize_role_row(
            {
                "role_id": fallback_role["role_id"],
                "title": fallback_role["title"],
                "subtitle": fallback_role["subtitle"],
                "description": fallback_role["description"],
                "level_label": fallback_role["level_label"],
                "default_duration": fallback_role["default_duration"],
                "available_durations": fallback_role["available_durations"],
                "primary_topic_id": max(fallback_role["topic_weights"].items(), key=lambda entry: entry[1])[0],
            },
            fallback_role["topic_weights"],
        ) if fallback_role else None
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def get_topic_by_id(topic_id, include_inactive=False):
    connection = create_database_connection()
    if connection is None:
        return None

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT topic_id, category, title, subtitle, description, level_label, accent, question_count, is_active
            FROM topics
            WHERE topic_id = %s
            """ + ("" if include_inactive else " AND is_active = TRUE"),
            (topic_id,),
        )
        row = cursor.fetchone()
        return normalize_topic_row(row) if row else None
    except Error as exc:
        print(f"Database error loading topic {topic_id}: {exc}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def build_difficulty_plan(question_count):
    blueprint = DURATION_BLUEPRINTS.get(normalize_duration_minutes(question_count))
    if blueprint:
        return blueprint["difficulty_plan"][:]

    if question_count <= 4:
        return ["easy", "easy", "medium", "medium"][:question_count]
    if question_count <= 6:
        return ["easy", "easy", "medium", "medium", "medium", "hard"][:question_count]
    return ["easy", "easy", "medium", "medium", "medium", "medium", "hard", "hard", "hard", "hard"][:question_count]


def build_topic_session_questions(all_questions, duration_minutes):
    if not all_questions:
        return []

    blueprint = DURATION_BLUEPRINTS[normalize_duration_minutes(duration_minutes)]
    remaining_by_difficulty = {"easy": [], "medium": [], "hard": []}

    for question in all_questions:
        remaining_by_difficulty.setdefault(question["difficulty"], []).append(question)

    for items in remaining_by_difficulty.values():
        random.shuffle(items)

    selected = []
    seen_ids = set()
    for difficulty in blueprint["difficulty_plan"]:
        pool = remaining_by_difficulty.get(difficulty, [])
        while pool:
            candidate = pool.pop()
            if candidate["question_id"] in seen_ids:
                continue
            selected.append(candidate)
            seen_ids.add(candidate["question_id"])
            break

    if len(selected) < blueprint["question_count"]:
        remaining = [question for question in all_questions if question["question_id"] not in seen_ids]
        random.shuffle(remaining)
        selected.extend(remaining[: blueprint["question_count"] - len(selected)])

    return selected[: blueprint["question_count"]]


def build_role_session_questions(role, duration_minutes):
    topic_weights = role.get("topic_weights") or {}
    topic_ids = list(topic_weights.keys())
    if not topic_ids:
        return []

    connection = create_database_connection()
    if connection is None:
        return []

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        placeholders = ", ".join(["%s"] * len(topic_ids))
        cursor.execute(
            f"""
            SELECT question_id, topic_id, question_text, difficulty, sample_answer, ideal_answer, display_order
            FROM questions
            WHERE topic_id IN ({placeholders}) AND is_active = TRUE
            ORDER BY topic_id ASC, display_order ASC
            """,
            tuple(topic_ids),
        )
        rows = cursor.fetchall() or []
    except Error as exc:
        print(f"Database error building role session questions: {exc}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

    normalized_rows = [normalize_question_row(row) for row in rows]
    by_topic = {}
    for row in normalized_rows:
        by_topic.setdefault(row["topic_id"], []).append(row)

    for questions in by_topic.values():
        random.shuffle(questions)

    blueprint = DURATION_BLUEPRINTS[normalize_duration_minutes(duration_minutes)]
    available_topic_ids = [topic_id for topic_id in topic_ids if by_topic.get(topic_id)]
    weights = [topic_weights[topic_id] for topic_id in available_topic_ids]
    selected = []
    used_question_ids = set()

    for slot_index, difficulty in enumerate(blueprint["difficulty_plan"]):
        picked_question = None
        candidate_topics = random.choices(available_topic_ids, weights=weights, k=max(3, len(available_topic_ids)))

        for topic_id in candidate_topics:
            pool = [
                question for question in by_topic.get(topic_id, [])
                if question["question_id"] not in used_question_ids and question["difficulty"] == difficulty
            ]
            if pool:
                picked_question = pool[0]
                break

        if picked_question is None:
            for topic_id in candidate_topics:
                pool = [
                    question for question in by_topic.get(topic_id, [])
                    if question["question_id"] not in used_question_ids
                ]
                if pool:
                    picked_question = pool[0]
                    break

        if picked_question is None:
            remaining = [question for question in normalized_rows if question["question_id"] not in used_question_ids]
            if not remaining:
                break
            picked_question = remaining[0]

        picked_question = {
            **picked_question,
            "section_label": blueprint["sections"][slot_index],
        }
        selected.append(picked_question)
        used_question_ids.add(picked_question["question_id"])

    return selected


def get_interview_session_plan(topic_id=None, role_id=None, duration_minutes=30):
    duration_minutes = normalize_duration_minutes(duration_minutes)

    if role_id:
        role = get_role_by_id(role_id)
        if not role:
            return None

        questions = build_role_session_questions(role, duration_minutes)
        if not questions:
            return None

        primary_topic = role.get("primary_topic_id")
        return {
            "mode": "role",
            "role_id": role["role_id"],
            "role_title": role["title"],
            "title": role["title"],
            "subtitle": role["subtitle"],
            "duration_minutes": duration_minutes,
            "blueprint_label": DURATION_BLUEPRINTS[duration_minutes]["summary_label"],
            "primary_topic_id": primary_topic,
            "questions": [
                {
                    "question_id": question["question_id"],
                    "topic_id": question["topic_id"],
                    "q": question["question_text"],
                    "difficulty": question["difficulty"],
                    "sample_answer": question.get("sample_answer") or "",
                    "ideal_answer": question.get("ideal_answer") or "",
                    "section_label": question.get("section_label", ""),
                }
                for question in questions
            ],
        }

    resolved_topic_id = topic_id or "graphs"
    topic = get_topic_by_id(resolved_topic_id)
    if not topic:
        topic = get_topic_by_id("graphs")
        resolved_topic_id = "graphs"
    if not topic:
        return None

    questions = build_topic_session_questions(get_questions_for_topic(resolved_topic_id), duration_minutes)
    if not questions:
        return None

    return {
        "mode": "topic",
        "topic_id": resolved_topic_id,
        "title": topic["title"],
        "subtitle": topic["subtitle"],
        "duration_minutes": duration_minutes,
        "blueprint_label": DURATION_BLUEPRINTS[duration_minutes]["summary_label"],
        "questions": [
            {
                "question_id": question["question_id"],
                "topic_id": question["topic_id"],
                "q": question["question_text"],
                "difficulty": question["difficulty"],
                "sample_answer": question.get("sample_answer") or "",
                "ideal_answer": question.get("ideal_answer") or "",
            }
            for question in questions
        ],
    }


def get_study_materials_for_topics(topic_ids):
    resolved_topic_ids = [str(topic_id).strip() for topic_id in (topic_ids or []) if str(topic_id).strip()]
    if not resolved_topic_ids:
        return []

    connection = create_database_connection()
    if connection is None:
        materials = []
        for topic_id in resolved_topic_ids:
            topic = get_topic_by_id(topic_id)
            if not topic:
                continue
            materials.append(
                normalize_study_material_row(
                    build_default_study_material(topic, get_questions_for_topic(topic_id)[:4])
                )
            )
        return materials

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        placeholders = ", ".join(["%s"] * len(resolved_topic_ids))
        cursor.execute(
            f"""
            SELECT topic_id, topic_title, overview, revision_notes, common_mistakes, rapid_fire_points, practice_prompts, estimated_minutes, updated_at
            FROM topic_study_materials
            WHERE topic_id IN ({placeholders})
            """,
            tuple(resolved_topic_ids),
        )
        rows = cursor.fetchall() or []
        materials_by_topic = {row["topic_id"]: normalize_study_material_row(row) for row in rows}
    except Error:
        logger.exception("Database error loading study materials")
        materials_by_topic = {}
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

    materials = []
    for topic_id in resolved_topic_ids:
        material = materials_by_topic.get(topic_id)
        if material:
            materials.append(material)
            continue

        topic = get_topic_by_id(topic_id)
        if not topic:
            continue
        materials.append(
            normalize_study_material_row(
                build_default_study_material(topic, get_questions_for_topic(topic_id)[:4])
            )
        )

    return materials


def build_study_material_brief(topic_id, material):
    topic = get_topic_by_id(topic_id) or {"title": material.get("topic_title") or topic_id.replace("_", " ").title()}
    topic_questions = get_questions_for_topic(topic_id)
    prompt_examples = topic_questions[:3]
    answer_examples = []
    for question in prompt_examples[:2]:
        answer_examples.append(
            {
                "question": question["question_text"],
                "sample_answer": question.get("sample_answer") or "",
                "ideal_answer": question.get("ideal_answer") or "",
            }
        )

    return {
        **material,
        "knowledge_card": {
            "title": topic.get("title") or material.get("topic_title") or "Topic revision",
            "summary": material.get("overview") or "",
            "rows": [
                {"label": "Revision block", "value": f"{int(material.get('estimated_minutes') or 20)} min"},
                {"label": "Interview lens", "value": topic.get("subtitle") or "Definitions, trade-offs, and practical use"},
                {
                    "label": "Checkpoint shape",
                    "value": "Round 1 builds basics first. Round 2 pushes trade-offs, edge cases, and applied reasoning.",
                },
                {
                    "label": "Common slip",
                    "value": material.get("common_mistakes") or "Candidates often stay generic instead of answering with structure.",
                },
            ],
        },
        "answer_examples": answer_examples,
        "interview_checks": [
            "Lead with the direct answer before adding detail.",
            "Use one concrete example or trade-off whenever possible.",
            "Keep the first 30 seconds clean and confident.",
        ],
        "prompt_examples": [question["question_text"] for question in prompt_examples],
    }


def build_study_plan_progress(plan, steps):
    total_steps = len(steps)
    completed_steps = len([step for step in steps if step["status"] == "done"])
    scored_steps = [step for step in steps if step.get("snapshot", {}).get("last_score") not in (None, "")]
    score_values = [step["snapshot"].get("last_score") for step in scored_steps]
    phase_lookup = {
        "foundation": "Foundation",
        "reinforcement": "Reinforcement",
        "simulation": "Simulation",
    }

    phase_breakdown = []
    for phase_key in ["foundation", "reinforcement", "simulation"]:
        phase_steps = [step for step in steps if step["phase_key"] == phase_key]
        if not phase_steps:
            continue
        phase_breakdown.append(
            {
                "phase_key": phase_key,
                "title": phase_lookup.get(phase_key, phase_key.title()),
                "total_steps": len(phase_steps),
                "completed_steps": len([step for step in phase_steps if step["status"] == "done"]),
                "average_score": average_numbers(
                    [step.get("snapshot", {}).get("last_score") for step in phase_steps if step.get("snapshot", {}).get("last_score") not in (None, "")]
                ),
            }
        )

    topic_progress = []
    seen_topics = []
    for step in steps:
        topic_id = step.get("topic_id")
        if not topic_id or topic_id in seen_topics:
            continue
        seen_topics.append(topic_id)
        topic_steps = [item for item in steps if item.get("topic_id") == topic_id and item["step_type"] != "revise"]
        if not topic_steps:
            continue
        topic_progress.append(
            {
                "topic_id": topic_id,
                "topic_title": step.get("topic_title") or topic_id.replace("_", " ").title(),
                "completed_rounds": len([item for item in topic_steps if item["status"] == "done"]),
                "total_rounds": len(topic_steps),
                "average_score": average_numbers(
                    [item.get("snapshot", {}).get("last_score") for item in topic_steps if item.get("snapshot", {}).get("last_score") not in (None, "")]
                ),
            }
        )

    next_steps = [
        {
            "step_id": step["step_id"],
            "scheduled_label": step["scheduled_label"],
            "headline": step.get("snapshot", {}).get("headline") or step["step_type"].replace("_", " ").title(),
            "step_type": step["step_type"],
        }
        for step in steps
        if step["status"] != "done"
    ][:3]

    return {
        "completion_percent": round((completed_steps / total_steps) * 100) if total_steps else 0,
        "average_score": average_numbers(score_values),
        "completed_steps": completed_steps,
        "total_steps": total_steps,
        "phase_breakdown": phase_breakdown,
        "topic_progress": topic_progress,
        "score_history": [int(value) for value in score_values if value not in (None, "")][-8:],
        "next_steps": next_steps,
        "current_focus": next_steps[0] if next_steps else None,
        "target_days": int(plan.get("target_days") or 40),
    }


def build_spaced_days(start_day, end_day, count):
    if count <= 0:
        return []

    start_day = max(1, int(start_day))
    end_day = max(start_day, int(end_day))
    if count == 1 or start_day == end_day:
        return [start_day for _ in range(count)]

    span = end_day - start_day
    days = []
    for index in range(count):
        day = start_day + round((span * index) / (count - 1))
        if days and day < days[-1]:
            day = days[-1]
        days.append(min(end_day, max(start_day, day)))
    return days


def build_study_plan_outline(role, target_days):
    focus_topics = (role or {}).get("focus_topics") or []
    selected_topics = focus_topics[: min(6, max(3, len(focus_topics)))] if focus_topics else []
    if not selected_topics and role and role.get("primary_topic_id"):
        fallback_topic = get_topic_by_id(role["primary_topic_id"])
        if fallback_topic:
            selected_topics = [{"topic_id": fallback_topic["topic_id"], "title": fallback_topic["title"], "weight": 100}]

    if not selected_topics:
        return {"summary": {}, "steps": [], "focus_topics": [], "materials": []}

    target_days = normalize_study_plan_days(target_days, fallback=40)
    phase_one_end = max(6, min(target_days - 4, round(target_days * 0.45)))
    phase_two_end = max(phase_one_end + 3, min(target_days - 1, round(target_days * 0.75)))
    mixed_count = 5 if target_days >= 34 else 4 if target_days >= 24 else 3 if target_days >= 14 else 2
    mock_count = 3 if target_days >= 35 else 2 if target_days >= 18 else 1
    phase_two_round_end = max(
        phase_one_end + 1,
        min(
            phase_two_end - 1,
            phase_one_end + round(max(2, phase_two_end - phase_one_end) * 0.58),
        ),
    )

    materials = get_study_materials_for_topics([topic["topic_id"] for topic in selected_topics])
    materials_by_topic = {material["topic_id"]: material for material in materials}
    question_bank = {
        topic["topic_id"]: get_questions_for_topic(topic["topic_id"])
        for topic in selected_topics
    }

    revise_days = build_spaced_days(1, max(1, phase_one_end - 2), len(selected_topics))
    round_one_days = [min(phase_one_end, day + 1) for day in revise_days]
    round_two_days = build_spaced_days(phase_one_end + 1, max(phase_one_end + 1, phase_two_round_end), len(selected_topics))
    mixed_days = build_spaced_days(phase_two_round_end + 1, phase_two_end, mixed_count)
    mock_days = build_spaced_days(phase_two_end + 1, target_days, mock_count)

    steps = []
    sequence_no = 1

    for index, topic in enumerate(selected_topics):
        topic_id = topic["topic_id"]
        topic_title = topic.get("title") or topic_id.replace("_", " ").title()
        material = materials_by_topic.get(topic_id) or normalize_study_material_row(
            build_default_study_material(
                get_topic_by_id(topic_id) or {"topic_id": topic_id, "title": topic_title},
                question_bank.get(topic_id) or [],
            )
        )
        material_brief = build_study_material_brief(topic_id, material)
        topic_questions = question_bank.get(topic_id) or []
        round_one_questions = build_topic_round_questions(topic_id, 1)
        round_two_questions = build_topic_round_questions(topic_id, 2)
        round_one_ids = [question["question_id"] for question in round_one_questions]
        round_two_ids = [question["question_id"] for question in round_two_questions]

        steps.append(
            {
                "step_id": build_study_step_id(),
                "sequence_no": sequence_no,
                "phase_key": "foundation",
                "step_type": "revise",
                "scheduled_day": revise_days[index],
                "scheduled_label": f"Day {revise_days[index]}",
                "topic_id": topic_id,
                "topic_title": topic_title,
                "role_id": role["role_id"],
                "role_title": role["title"],
                "question_ids": [],
                "status": "planned",
                "snapshot": {
                    "headline": f"Revise {topic_title}",
                    "description": material["revision_notes"] or material["overview"],
                    "estimated_minutes": material["estimated_minutes"],
                    "rapid_fire_points": material["rapid_fire_points"],
                    "practice_prompts": material_brief["prompt_examples"][:2] or material["practice_prompts"][:2],
                    "knowledge_card": material_brief["knowledge_card"],
                    "answer_examples": material_brief["answer_examples"],
                    "interview_checks": material_brief["interview_checks"],
                    "action_kind": "review",
                    "action_label": "Review notes",
                    "material_topic_id": topic_id,
                },
            }
        )
        sequence_no += 1

        steps.append(
            {
                "step_id": build_study_step_id(),
                "sequence_no": sequence_no,
                "phase_key": "foundation",
                "step_type": "topic_round",
                "scheduled_day": round_one_days[index],
                "scheduled_label": f"Day {round_one_days[index]}",
                "topic_id": topic_id,
                "topic_title": topic_title,
                "role_id": role["role_id"],
                "role_title": role["title"],
                "question_ids": round_one_ids,
                "status": "planned",
                "snapshot": {
                    "headline": f"{topic_title} round 1",
                    "description": f"Start with the core interview questions for {topic_title} and answer them with clean structure.",
                    "question_count": len(round_one_ids),
                    "round_stage": 1,
                    "stage_label": "Round 1",
                    "difficulty_focus": "Foundation to medium",
                    "difficulty_plan": [question["difficulty"] for question in round_one_questions],
                    "practice_prompts": [question["question_text"] for question in round_one_questions[:3]],
                    "recommended_duration": 20,
                    "launch_mode": "topic_round",
                    "can_launch_interview": True,
                    "score_target": 72,
                    "answer_examples": material_brief["answer_examples"],
                },
            }
        )
        sequence_no += 1

        steps.append(
            {
                "step_id": build_study_step_id(),
                "sequence_no": sequence_no,
                "phase_key": "reinforcement",
                "step_type": "topic_round",
                "scheduled_day": round_two_days[index],
                "scheduled_label": f"Day {round_two_days[index]}",
                "topic_id": topic_id,
                "topic_title": topic_title,
                "role_id": role["role_id"],
                "role_title": role["title"],
                "question_ids": round_two_ids,
                "status": "planned",
                "snapshot": {
                    "headline": f"{topic_title} round 2",
                    "description": f"Push {topic_title} into higher-pressure follow-ups, trade-offs, and applied interview reasoning.",
                    "question_count": len(round_two_ids),
                    "round_stage": 2,
                    "stage_label": "Round 2",
                    "difficulty_focus": "Applied medium to hard",
                    "difficulty_plan": [question["difficulty"] for question in round_two_questions],
                    "practice_prompts": [question["question_text"] for question in round_two_questions[:3]],
                    "recommended_duration": 25,
                    "launch_mode": "topic_round",
                    "can_launch_interview": True,
                    "score_target": 78,
                },
            }
        )
        sequence_no += 1

    for index, scheduled_day in enumerate(mixed_days, start=1):
        mix_topic_window = [
            selected_topics[(index + offset - 1) % len(selected_topics)]
            for offset in range(min(4, len(selected_topics)))
        ]
        mix_topic_ids = [topic["topic_id"] for topic in mix_topic_window]
        mixed_questions = build_mixed_round_questions(
            mix_topic_ids,
            build_question_selection_plan("easy", "medium", "medium", "hard", "medium", fallback_count=5),
            rotation_seed=index - 1,
        )
        steps.append(
            {
                "step_id": build_study_step_id(),
                "sequence_no": sequence_no,
                "phase_key": "reinforcement",
                "step_type": "mixed_quiz",
                "scheduled_day": scheduled_day,
                "scheduled_label": f"Day {scheduled_day}",
                "topic_id": None,
                "topic_title": None,
                "role_id": role["role_id"],
                "role_title": role["title"],
                "question_ids": [question["question_id"] for question in mixed_questions],
                "status": "planned",
                "snapshot": {
                    "headline": f"Mixed quiz {index}",
                    "description": "Blend multiple topic lanes in one sitting so recall starts to feel closer to a real interview jump.",
                    "focus_topics": [topic["title"] for topic in mix_topic_window],
                    "focus_topic_ids": mix_topic_ids,
                    "difficulty_plan": [question["difficulty"] for question in mixed_questions],
                    "practice_prompts": [question["question_text"] for question in mixed_questions[:3]],
                    "recommended_duration": 25,
                    "difficulty_focus": "Mixed easy to hard",
                    "launch_mode": "mixed_quiz",
                    "can_launch_interview": True,
                    "score_target": 76,
                },
            }
        )
        sequence_no += 1

    for index, scheduled_day in enumerate(mock_days, start=1):
        steps.append(
            {
                "step_id": build_study_step_id(),
                "sequence_no": sequence_no,
                "phase_key": "simulation",
                "step_type": "mock_interview",
                "scheduled_day": scheduled_day,
                "scheduled_label": f"Day {scheduled_day}",
                "topic_id": role.get("primary_topic_id"),
                "topic_title": next((topic["title"] for topic in selected_topics if topic["topic_id"] == role.get("primary_topic_id")), None),
                "role_id": role["role_id"],
                "role_title": role["title"],
                "question_ids": [],
                "status": "planned",
                "snapshot": {
                    "headline": f"{role['title']} mock round {index}",
                    "description": "Run a fuller role simulation and review how well the mixed topics now hold together under pressure.",
                    "recommended_duration": role.get("default_duration") or 30,
                    "focus_topics": [topic["title"] for topic in selected_topics[:4]],
                    "launch_mode": "mock_interview",
                    "can_launch_interview": True,
                    "score_target": 80,
                },
            }
        )
        sequence_no += 1

    summary = {
        "target_days": target_days,
        "step_count": len(steps),
        "topic_count": len(selected_topics),
        "mixed_quiz_count": mixed_count,
        "mock_count": mock_count,
        "phases": [
            {
                "phase_key": "foundation",
                "title": "Topic foundation",
                "day_range": f"Day 1-{phase_one_end}",
                "description": "Revise one topic lane at a time, then clear Round 1 so the basics feel stable before you scale difficulty.",
            },
            {
                "phase_key": "reinforcement",
                "title": "Round 2 and mixed pressure",
                "day_range": f"Day {phase_one_end + 1}-{phase_two_end}",
                "description": "Return for Round 2 on each topic, then start mixed sessions where topics switch mid-stream.",
            },
            {
                "phase_key": "simulation",
                "title": "Role simulation",
                "day_range": f"Day {phase_two_end + 1}-{target_days}",
                "description": "Finish with fuller role-style rounds that behave like the interview you are training for.",
            },
        ],
    }
    return {"summary": summary, "steps": steps, "focus_topics": selected_topics, "materials": materials}


def create_study_plan(user_id, role_id, target_days=40):
    resolved_user_id = str(user_id or "").strip()
    resolved_role_id = str(role_id or "").strip()
    if not resolved_user_id:
        return {"success": False, "error": "Authentication required"}
    if not resolved_role_id:
        return {"success": False, "error": "Role ID is required"}

    role = get_role_by_id(resolved_role_id)
    if not role:
        return {"success": False, "error": "Selected role does not exist"}

    outline = build_study_plan_outline(role, target_days)
    steps = outline.get("steps") or []
    if not steps:
        return {"success": False, "error": "A prep path could not be generated for this role yet"}

    focus_topics = outline.get("focus_topics") or []
    plan_id = build_study_plan_id()
    normalized_days = normalize_study_plan_days(target_days, fallback=40)
    title = f"{role['title']} {normalized_days}-day prep path"

    connection = create_database_connection()
    if connection is None:
        return {
            "success": False,
            "error": "Database connection failed",
            "detail": "The prep path could not be saved because the database is unavailable.",
        }

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO study_plans (
                plan_id,
                user_id,
                role_id,
                role_title,
                title,
                target_days,
                focus_topic_ids,
                role_snapshot,
                plan_summary,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                plan_id,
                resolved_user_id,
                role["role_id"],
                role["title"],
                title,
                normalized_days,
                json.dumps([topic["topic_id"] for topic in focus_topics]),
                json.dumps(role, default=str),
                json.dumps(outline["summary"], default=str),
                "active",
            ),
        )

        for step in steps:
            cursor.execute(
                """
                INSERT INTO study_plan_steps (
                    step_id,
                    plan_id,
                    sequence_no,
                    phase_key,
                    step_type,
                    scheduled_day,
                    scheduled_label,
                    topic_id,
                    topic_title,
                    role_id,
                    role_title,
                    question_ids,
                    snapshot_json,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    step["step_id"],
                    plan_id,
                    step["sequence_no"],
                    step["phase_key"],
                    step["step_type"],
                    step["scheduled_day"],
                    step["scheduled_label"],
                    step.get("topic_id"),
                    step.get("topic_title"),
                    step.get("role_id"),
                    step.get("role_title"),
                    json.dumps(step.get("question_ids") or []),
                    json.dumps(step.get("snapshot") or {}, default=str),
                    normalize_study_step_status(step.get("status")),
                ),
            )

        connection.commit()
        result = get_study_plan(plan_id, resolved_user_id)
        if result.get("success"):
            return result
        return {"success": True, "plan": {"plan_id": plan_id}, "steps": steps, "materials": outline.get("materials") or []}
    except Error as exc:
        connection.rollback()
        return database_failure(
            "Failed to save prep path",
            exc,
            detail="The study planner tables could not be written right now.",
            role_id=resolved_role_id,
            user_id=resolved_user_id,
        )
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def list_study_plans(user_id, limit=8):
    resolved_user_id = str(user_id or "").strip()
    if not resolved_user_id:
        return []

    connection = create_database_connection()
    if connection is None:
        return []

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        safe_limit = max(1, min(int(limit or 8), 20))
        cursor.execute(
            """
            SELECT
                study_plans.plan_id,
                study_plans.user_id,
                study_plans.role_id,
                study_plans.role_title,
                study_plans.title,
                study_plans.target_days,
                study_plans.focus_topic_ids,
                study_plans.plan_summary,
                study_plans.status,
                study_plans.created_at,
                study_plans.updated_at,
                COALESCE(step_totals.step_count, 0) AS step_count,
                COALESCE(step_totals.completed_steps, 0) AS completed_steps
            FROM study_plans
            LEFT JOIN (
                SELECT
                    plan_id,
                    COUNT(*) AS step_count,
                    SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) AS completed_steps
                FROM study_plan_steps
                GROUP BY plan_id
            ) AS step_totals ON step_totals.plan_id = study_plans.plan_id
            WHERE study_plans.user_id = %s
            ORDER BY study_plans.updated_at DESC, study_plans.created_at DESC
            LIMIT %s
            """,
            (resolved_user_id, safe_limit),
        )
        rows = cursor.fetchall() or []
        return [normalize_study_plan_row(row) for row in rows]
    except Error:
        logger.exception("Database error loading study plans")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def get_study_plan(plan_id, user_id):
    resolved_plan_id = str(plan_id or "").strip()
    resolved_user_id = str(user_id or "").strip()
    if not resolved_plan_id or not resolved_user_id:
        return {"success": False, "error": "Study plan not found"}

    connection = create_database_connection()
    if connection is None:
        return {"success": False, "error": "Database connection failed"}

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                study_plans.plan_id,
                study_plans.user_id,
                study_plans.role_id,
                study_plans.role_title,
                study_plans.title,
                study_plans.target_days,
                study_plans.focus_topic_ids,
                study_plans.plan_summary,
                study_plans.status,
                study_plans.created_at,
                study_plans.updated_at,
                COALESCE(step_totals.step_count, 0) AS step_count,
                COALESCE(step_totals.completed_steps, 0) AS completed_steps
            FROM study_plans
            LEFT JOIN (
                SELECT
                    plan_id,
                    COUNT(*) AS step_count,
                    SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) AS completed_steps
                FROM study_plan_steps
                GROUP BY plan_id
            ) AS step_totals ON step_totals.plan_id = study_plans.plan_id
            WHERE study_plans.plan_id = %s AND study_plans.user_id = %s
            """,
            (resolved_plan_id, resolved_user_id),
        )
        plan_row = cursor.fetchone()
        if not plan_row:
            return {"success": False, "error": "Study plan not found"}

        cursor.execute(
            """
            SELECT
                step_id,
                plan_id,
                sequence_no,
                phase_key,
                step_type,
                scheduled_day,
                scheduled_label,
                topic_id,
                topic_title,
                role_id,
                role_title,
                question_ids,
                snapshot_json,
                status,
                updated_at
            FROM study_plan_steps
            WHERE plan_id = %s
            ORDER BY sequence_no ASC, scheduled_day ASC
            """,
            (resolved_plan_id,),
        )
        step_rows = cursor.fetchall() or []
        plan = normalize_study_plan_row(plan_row)
        steps = [normalize_study_plan_step_row(row) for row in step_rows]
        materials = [
            build_study_material_brief(material["topic_id"], material)
            for material in get_study_materials_for_topics(plan["focus_topic_ids"])
        ]
        progress = build_study_plan_progress(plan, steps)
        return {
            "success": True,
            "plan": plan,
            "steps": steps,
            "materials": materials,
            "progress": progress,
        }
    except Error:
        logger.exception("Database error loading study plan")
        return {"success": False, "error": "Study plan could not be loaded"}
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def get_study_plan_step_session_plan(user_id, plan_id, step_id):
    result = get_study_plan(plan_id, user_id)
    if not result.get("success"):
        return result

    plan = result.get("plan") or {}
    steps = result.get("steps") or []
    step = next((item for item in steps if item["step_id"] == step_id), None)
    if not step:
        return {"success": False, "error": "Study step not found"}

    snapshot = step.get("snapshot") or {}
    if step["step_type"] == "revise":
        return {"success": False, "error": "This step is a revision block, not a runnable interview."}

    duration_minutes = normalize_custom_duration_minutes(snapshot.get("recommended_duration"), fallback=30)
    plan_payload = None

    if step["step_type"] == "topic_round":
        questions = get_questions_by_ids(step.get("question_ids") or [])
        if not questions:
            questions = build_topic_round_questions(step.get("topic_id"), snapshot.get("round_stage") or 1)
        topic = get_topic_by_id(step.get("topic_id")) or {"title": step.get("topic_title") or "Topic practice", "subtitle": ""}
        plan_payload = {
            "mode": "topic",
            "topic_id": step.get("topic_id"),
            "title": snapshot.get("headline") or f"{topic['title']} round",
            "subtitle": snapshot.get("description") or topic.get("subtitle") or "",
            "duration_minutes": duration_minutes,
            "blueprint_label": snapshot.get("stage_label") or "Prep round",
            "primary_topic_id": step.get("topic_id"),
            "questions": [
                {
                    "question_id": question["question_id"],
                    "topic_id": question["topic_id"],
                    "q": question["question_text"],
                    "difficulty": question["difficulty"],
                    "sample_answer": question.get("sample_answer") or "",
                    "ideal_answer": question.get("ideal_answer") or "",
                    "section_label": snapshot.get("stage_label") or f"Round {snapshot.get('round_stage') or 1}",
                }
                for question in questions
            ],
        }
    elif step["step_type"] == "mixed_quiz":
        focus_topic_ids = snapshot.get("focus_topic_ids") or (plan.get("focus_topic_ids") or [])
        questions = get_questions_by_ids(step.get("question_ids") or [])
        if not questions:
            questions = build_mixed_round_questions(
                focus_topic_ids or plan.get("focus_topic_ids") or [],
                snapshot.get("difficulty_plan") or build_question_selection_plan("easy", "medium", "medium", "hard", "medium", fallback_count=5),
                rotation_seed=step.get("sequence_no") or 0,
            )
        plan_payload = {
            "mode": "role",
            "role_id": step.get("role_id"),
            "role_title": step.get("role_title"),
            "title": snapshot.get("headline") or f"{plan.get('role_title') or 'Role'} mixed round",
            "subtitle": snapshot.get("description") or "A mixed prep-path round across multiple topics.",
            "duration_minutes": duration_minutes,
            "blueprint_label": "Mixed round",
            "primary_topic_id": focus_topic_ids[0] if focus_topic_ids else None,
            "questions": [
                {
                    "question_id": question["question_id"],
                    "topic_id": question["topic_id"],
                    "q": question["question_text"],
                    "difficulty": question["difficulty"],
                    "sample_answer": question.get("sample_answer") or "",
                    "ideal_answer": question.get("ideal_answer") or "",
                    "section_label": "Mixed round",
                }
                for question in questions
            ],
        }
    elif step["step_type"] == "mock_interview":
        role_payload = get_role_by_id(step.get("role_id"))
        if not role_payload:
            return {"success": False, "error": "Linked role is unavailable"}
        questions = build_role_session_questions(role_payload, duration_minutes)
        plan_payload = {
            "mode": "role",
            "role_id": role_payload["role_id"],
            "role_title": role_payload["title"],
            "title": snapshot.get("headline") or role_payload["title"],
            "subtitle": snapshot.get("description") or role_payload.get("subtitle") or "",
            "duration_minutes": duration_minutes,
            "blueprint_label": "Role simulation",
            "primary_topic_id": role_payload.get("primary_topic_id"),
            "questions": [
                {
                    "question_id": question["question_id"],
                    "topic_id": question["topic_id"],
                    "q": question["question_text"],
                    "difficulty": question["difficulty"],
                    "sample_answer": question.get("sample_answer") or "",
                    "ideal_answer": question.get("ideal_answer") or "",
                    "section_label": question.get("section_label", ""),
                }
                for question in questions
            ],
        }

    if not plan_payload or not plan_payload.get("questions"):
        return {"success": False, "error": "A study-step interview could not be generated right now."}

    plan_payload["study_context"] = {
        "study_plan_id": plan.get("plan_id"),
        "study_step_id": step.get("step_id"),
        "step_type": step.get("step_type"),
        "round_stage": snapshot.get("round_stage"),
        "phase_key": step.get("phase_key"),
        "scheduled_day": step.get("scheduled_day"),
        "scheduled_label": step.get("scheduled_label"),
        "plan_title": plan.get("title"),
        "role_title": plan.get("role_title"),
    }
    return {"success": True, "plan": plan_payload, "step": step, "progress": result.get("progress") or {}}


def delete_study_plan(user_id, plan_id):
    resolved_user_id = str(user_id or "").strip()
    resolved_plan_id = str(plan_id or "").strip()
    if not resolved_user_id or not resolved_plan_id:
        return {"success": False, "error": "Study plan not found"}

    connection = create_database_connection()
    if connection is None:
        return {"success": False, "error": "Database connection failed"}

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM study_plans WHERE plan_id = %s AND user_id = %s",
            (resolved_plan_id, resolved_user_id),
        )
        connection.commit()
        if cursor.rowcount <= 0:
            return {"success": False, "error": "Study plan not found"}
        return {"success": True, "plan_id": resolved_plan_id}
    except Error as exc:
        connection.rollback()
        return database_failure(
            "Failed to delete study plan",
            exc,
            detail="The saved prep path could not be removed right now.",
            user_id=resolved_user_id,
            plan_id=resolved_plan_id,
        )
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def update_study_plan_step_status(user_id, plan_id, step_id, status):
    resolved_user_id = str(user_id or "").strip()
    resolved_plan_id = str(plan_id or "").strip()
    resolved_step_id = str(step_id or "").strip()
    if not resolved_user_id or not resolved_plan_id or not resolved_step_id:
        return {"success": False, "error": "Study step not found"}

    connection = create_database_connection()
    if connection is None:
        return {"success": False, "error": "Database connection failed"}

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        normalized_status = normalize_study_step_status(status)
        cursor.execute(
            """
            UPDATE study_plan_steps
            INNER JOIN study_plans ON study_plans.plan_id = study_plan_steps.plan_id
            SET
                study_plan_steps.status = %s,
                study_plan_steps.updated_at = CURRENT_TIMESTAMP,
                study_plans.updated_at = CURRENT_TIMESTAMP
            WHERE study_plan_steps.step_id = %s
              AND study_plan_steps.plan_id = %s
              AND study_plans.user_id = %s
            """,
            (normalized_status, resolved_step_id, resolved_plan_id, resolved_user_id),
        )
        if cursor.rowcount == 0:
            connection.rollback()
            return {"success": False, "error": "Study step not found"}

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_steps,
                SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) AS completed_steps
            FROM study_plan_steps
            WHERE plan_id = %s
            """,
            (resolved_plan_id,),
        )
        progress_row = cursor.fetchone() or {}
        total_steps = int(progress_row.get("total_steps") or 0)
        completed_steps = int(progress_row.get("completed_steps") or 0)
        plan_status = "completed" if total_steps > 0 and total_steps == completed_steps else "active"
        cursor.execute(
            """
            UPDATE study_plans
            SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE plan_id = %s AND user_id = %s
            """,
            (plan_status, resolved_plan_id, resolved_user_id),
        )
        connection.commit()
        return get_study_plan(resolved_plan_id, resolved_user_id)
    except Error as exc:
        connection.rollback()
        return database_failure(
            "Failed to update study step",
            exc,
            detail="The prep path progress could not be updated right now.",
            plan_id=resolved_plan_id,
            step_id=resolved_step_id,
        )
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def sync_study_step_result(connection, session_data):
    study_plan_id = str((session_data or {}).get("study_plan_id") or "").strip()
    study_step_id = str((session_data or {}).get("study_step_id") or "").strip()
    user_id = str((session_data or {}).get("user_id") or "").strip()
    if not study_plan_id or not study_step_id or not user_id:
        return

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT study_plan_steps.snapshot_json
            FROM study_plan_steps
            INNER JOIN study_plans ON study_plans.plan_id = study_plan_steps.plan_id
            WHERE study_plan_steps.step_id = %s
              AND study_plan_steps.plan_id = %s
              AND study_plans.user_id = %s
            """,
            (study_step_id, study_plan_id, user_id),
        )
        row = cursor.fetchone()
        if not row:
            return

        snapshot = parse_json_field(row.get("snapshot_json"), {})
        final_score = int(round(float((session_data or {}).get("final_score") or 0)))
        attempt_count = int(snapshot.get("attempt_count") or 0) + 1
        score_total = float(snapshot.get("score_total") or 0) + final_score
        snapshot.update(
            {
                "last_score": final_score,
                "best_score": max(int(snapshot.get("best_score") or 0), final_score),
                "attempt_count": attempt_count,
                "score_total": round(score_total, 1),
                "average_score": round(score_total / attempt_count, 1),
                "last_session_id": session_data.get("session_id"),
                "last_completed_at": session_data.get("interview_date") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "last_confidence": average_numbers(session_data.get("confidence_history") or [], digits=1),
                "last_content_score": average_numbers(session_data.get("content_score_history") or [], digits=1),
                "last_delivery_score": average_numbers(session_data.get("delivery_score_history") or [], digits=1),
            }
        )

        cursor.execute(
            """
            UPDATE study_plan_steps
            INNER JOIN study_plans ON study_plans.plan_id = study_plan_steps.plan_id
            SET
                study_plan_steps.status = 'done',
                study_plan_steps.snapshot_json = %s,
                study_plan_steps.updated_at = CURRENT_TIMESTAMP,
                study_plans.updated_at = CURRENT_TIMESTAMP
            WHERE study_plan_steps.step_id = %s
              AND study_plan_steps.plan_id = %s
              AND study_plans.user_id = %s
            """,
            (json.dumps(snapshot, default=str), study_step_id, study_plan_id, user_id),
        )

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_steps,
                SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) AS completed_steps
            FROM study_plan_steps
            WHERE plan_id = %s
            """,
            (study_plan_id,),
        )
        progress_row = cursor.fetchone() or {}
        total_steps = int(progress_row.get("total_steps") or 0)
        completed_steps = int(progress_row.get("completed_steps") or 0)
        plan_status = "completed" if total_steps > 0 and total_steps == completed_steps else "active"
        cursor.execute(
            """
            UPDATE study_plans
            SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE plan_id = %s AND user_id = %s
            """,
            (plan_status, study_plan_id, user_id),
        )
    except Error:
        logger.exception("Database error syncing study-step result", extra={"study_plan_id": study_plan_id, "study_step_id": study_step_id})
    finally:
        if cursor:
            cursor.close()


def save_interview_session(session_data):
    """Save complete interview session to database."""
    session_id = (session_data or {}).get("session_id", "unknown") if isinstance(session_data, dict) else "unknown"
    logger.info("Attempting to save interview session | session_id=%s", session_id)

    connection = create_database_connection()
    if connection is None:
        return {
            "success": False,
            "error": "Database connection failed",
            "detail": "The interview session could not be saved because the database is unavailable.",
        }

    cursor = None
    try:
        cursor = connection.cursor()

        if not isinstance(session_data, dict):
            return {
                "success": False,
                "error": "Invalid session payload",
                "detail": "Expected a JSON object for the interview session data.",
            }

        if "session_id" not in session_data or not session_data["session_id"]:
            session_data["session_id"] = str(uuid.uuid4())
            logger.info("Generated new session_id=%s for interview save", session_data["session_id"])

        required_fields = ["session_id", "topic", "final_score"]
        for field in required_fields:
            if field not in session_data:
                return {
                    "success": False,
                    "error": "Missing required interview field",
                    "detail": f"The '{field}' field is required before the session can be saved.",
                }

        insert_query = """
        INSERT INTO interviews (session_id, user_id, topic, session_mode, role_id, final_score, complete_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        user_id = VALUES(user_id),
        topic = VALUES(topic),
        session_mode = VALUES(session_mode),
        role_id = VALUES(role_id),
        final_score = VALUES(final_score),
        complete_data = VALUES(complete_data)
        """

        session_mode = session_data.get("session_mode", "topic")
        resolved_topic = session_data.get("topic") or session_data.get("primary_topic_id") or session_data.get("role_id") or "general"

        cursor.execute(
            insert_query,
            (
                session_data.get("session_id", ""),
                session_data.get("user_id"),
                resolved_topic,
                session_mode,
                session_data.get("role_id"),
                session_data.get("final_score", 0),
                json.dumps(session_data, default=str),
            ),
        )

        sync_study_step_result(connection, session_data)
        connection.commit()
        session_id = session_data.get("session_id")
        if session_mode == "topic":
            sync_topic_activity(
                session_id=session_id,
                topic_id=resolved_topic,
                user_id=session_data.get("user_id"),
            )
        logger.info("Successfully saved interview session | session_id=%s", session_id)
        return {"success": True, "session_id": session_id}
    except Error as exc:
        if connection:
            try:
                connection.rollback()
            except Exception:
                pass
        return database_failure(
            "Failed to save interview session",
            exc,
            detail="The session data could not be written to the database.",
            session_id=session_id,
        )
    except Exception:
        if connection:
            try:
                connection.rollback()
            except Exception:
                pass
        logger.exception("Unexpected error saving interview session | session_id=%s", session_id)
        return {
            "success": False,
            "error": "Failed to save interview session",
            "detail": "An unexpected server error occurred while saving the interview.",
        }
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def get_interview_session(session_id):
    """Retrieve interview session from database."""
    logger.info("Attempting to retrieve session | session_id=%s", session_id)

    connection = create_database_connection()
    if connection is None:
        logger.warning("Database connection failed while retrieving session | session_id=%s", session_id)
        return None

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM interviews WHERE session_id = %s", (session_id,))
        result = cursor.fetchone()

        if result:
            if "complete_data" in result and result["complete_data"]:
                if isinstance(result["complete_data"], dict):
                    logger.info("Successfully retrieved session | session_id=%s", session_id)
                else:
                    try:
                        result["complete_data"] = json.loads(result["complete_data"])
                        logger.info("Successfully retrieved session | session_id=%s", session_id)
                    except (TypeError, json.JSONDecodeError) as exc:
                        logger.exception("JSON decode error while reading session | session_id=%s", session_id)
                        return None
            else:
                result["complete_data"] = {}
        else:
            logger.info("Session not found | session_id=%s", session_id)

        return result
    except Error as exc:
        logger.exception("Database error retrieving interview | session_id=%s", session_id)
        return None
    except Exception:
        logger.exception("Unexpected error retrieving interview | session_id=%s", session_id)
        return None
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def update_interview_session(session_id, update_data):
    """Update existing interview session."""
    connection = create_database_connection()
    if connection is None:
        return False

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE interviews
            SET user_id = %s, topic = %s, session_mode = %s, role_id = %s, complete_data = %s, final_score = %s
            WHERE session_id = %s
            """,
            (
                update_data.get("user_id"),
                update_data.get("topic") or update_data.get("primary_topic_id") or update_data.get("role_id") or "general",
                update_data.get("session_mode", "topic"),
                update_data.get("role_id"),
                json.dumps(update_data, default=str),
                update_data.get("final_score", 0),
                session_id,
            ),
        )
        connection.commit()
        return True
    except Error as exc:
        logger.exception("Error updating interview | session_id=%s", session_id)
        return False
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
