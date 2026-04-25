import copy
import importlib
import json
import shutil
import sys
import tempfile
import types
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import backend.database as database_module
from fastapi.testclient import TestClient


class _FakeWhisperModel:
    def transcribe(self, _file_path, **_kwargs):
        return {
            "text": "Breadth first search explores nodes level by level using a queue.",
            "segments": [{"end": 12.5}],
        }


database_module.init_database = lambda: True
sys.modules["whisper"] = types.SimpleNamespace(load_model=lambda _name: _FakeWhisperModel())
app_module = importlib.import_module("backend.main")
auth_module = importlib.import_module("backend.auth")


class FeatureConnectivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture_path = Path(__file__).resolve().parent / "fixtures" / "mock_app_data.json"
        with fixture_path.open(encoding="utf-8") as fixture_file:
            cls.fixture = json.load(fixture_file)
        cls.client = TestClient(app_module.app)

    def setUp(self):
        self.fixture = copy.deepcopy(self.__class__.fixture)
        self.signed_user = self.fixture["users"]["signed_in"]
        self.other_user = self.fixture["users"]["other_user"]
        self.signed_user["is_admin"] = True
        self.other_user["is_admin"] = False
        self.signed_token = auth_module.create_auth_token(self.signed_user)
        self.other_token = auth_module.create_auth_token(self.other_user)
        self.saved_sessions = {
            self.fixture["sessions"]["guest"]["session_id"]: self.fixture["sessions"]["guest"],
            self.fixture["sessions"]["signed"]["session_id"]: self.fixture["sessions"]["signed"],
        }
        self.admin_topics = [
            {
                "topic_id": "graphs",
                "category": "Algorithms",
                "title": "Graphs",
                "subtitle": "Traversal and graph modeling",
                "description": "Core graph interview questions.",
                "level_label": "Intermediate",
                "accent": "graphs",
                "question_count": 1,
                "is_active": True,
            },
            {
                "topic_id": "systemdesign",
                "category": "Architecture",
                "title": "System Design",
                "subtitle": "Scalable system thinking",
                "description": "Design round questions.",
                "level_label": "Advanced",
                "accent": "systemdesign",
                "question_count": 0,
                "is_active": False,
            },
        ]
        self.admin_questions = [
            {
                "question_id": "graphs_001",
                "topic_id": "graphs",
                "question_text": "Explain BFS.",
                "difficulty": "easy",
                "sample_answer": "Use a queue and explore level by level.",
                "ideal_answer": "Start from a source node, use a queue, and visit neighbors breadth first.",
                "display_order": 1,
                "is_active": True,
            }
        ]
        self.admin_roles = [
            {
                "role_id": "backend_engineer",
                "title": "Backend Engineer",
                "subtitle": "API and services",
                "description": "Backend interview loop",
                "level_label": "Mid-level",
                "default_duration": 30,
                "available_durations": [30, 45],
                "topic_weights": {"graphs": 100},
                "primary_topic_id": "graphs",
                "is_active": True,
            }
        ]
        self.admin_insights = {
            "overview": {
                "total_users": 2,
                "admin_users": 1,
                "total_sessions": 2,
                "active_users_7d": 1,
                "sessions_7d": 2,
                "custom_templates": 1,
                "average_score": 81.0,
            },
            "mode_breakdown": [
                {"session_mode": "topic", "session_count": 1, "average_score": 84.0},
                {"session_mode": "custom", "session_count": 1, "average_score": 78.0},
            ],
            "top_topics": [
                {"topic": "graphs", "session_count": 2, "average_score": 81.0, "latest_session_at": "2026-03-19 10:30:00"},
            ],
            "recent_sessions": [
                {
                    "session_id": "signed-session-001",
                    "user_id": self.signed_user["user_id"],
                    "username": self.signed_user["username"],
                    "email": self.signed_user["email"],
                    "topic": "graphs",
                    "session_mode": "topic",
                    "role_id": None,
                    "session_title": "Graphs practice",
                    "final_score": 84,
                    "questions_total": 6,
                    "created_at": "2026-03-19 10:30:00",
                }
            ],
            "users": [
                {
                    "user_id": self.signed_user["user_id"],
                    "username": self.signed_user["username"],
                    "email": self.signed_user["email"],
                    "is_admin": True,
                    "created_at": self.signed_user["created_at"],
                    "session_count": 1,
                    "sessions_7d": 1,
                    "average_score": 84.0,
                    "latest_session_at": "2026-03-19 10:30:00",
                }
            ],
        }
        self.study_plans = []
        self.temp_dir = tempfile.mkdtemp()
        self.stack = ExitStack()
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))
        self.addCleanup(self.stack.close)

        self.stack.enter_context(patch.object(app_module, "create_user", side_effect=self.mock_create_user))
        self.stack.enter_context(patch.object(app_module, "authenticate_user", side_effect=self.mock_authenticate_user))
        self.stack.enter_context(patch.object(app_module, "get_user_by_id", side_effect=self.mock_get_user_by_id))
        self.stack.enter_context(
            patch.object(app_module, "get_user_interview_history", side_effect=self.mock_get_user_interview_history)
        )
        self.stack.enter_context(
            patch.object(app_module, "get_topic_rating_summary", side_effect=self.mock_get_topic_rating_summary)
        )
        self.stack.enter_context(
            patch.object(app_module, "get_topic_activity_summary", side_effect=self.mock_get_topic_activity_summary)
        )
        self.stack.enter_context(
            patch.object(app_module, "get_score_leaderboard", side_effect=self.mock_get_score_leaderboard)
        )
        self.stack.enter_context(patch.object(app_module, "save_topic_rating", side_effect=self.mock_save_topic_rating))
        self.stack.enter_context(
            patch.object(app_module, "save_interview_session", side_effect=self.mock_save_interview_session)
        )
        self.stack.enter_context(
            patch.object(app_module, "get_interview_session", side_effect=self.mock_get_interview_session)
        )
        self.stack.enter_context(
            patch.object(app_module, "generate_interview_pdf", side_effect=self.mock_generate_interview_pdf)
        )
        self.stack.enter_context(
            patch.object(app_module, "analyze_transcript", return_value=self.fixture["transcribe_analysis"])
        )
        self.stack.enter_context(patch.object(app_module, "get_topic_catalog", side_effect=self.mock_get_topic_catalog))
        self.stack.enter_context(patch.object(app_module, "get_role_catalog", side_effect=self.mock_get_role_catalog))
        self.stack.enter_context(patch.object(app_module, "list_all_topics", side_effect=self.mock_list_all_topics))
        self.stack.enter_context(patch.object(app_module, "list_all_questions", side_effect=self.mock_list_all_questions))
        self.stack.enter_context(patch.object(app_module, "list_all_roles", side_effect=self.mock_list_all_roles))
        self.stack.enter_context(patch.object(app_module, "create_study_plan", side_effect=self.mock_create_study_plan))
        self.stack.enter_context(patch.object(app_module, "list_study_plans", side_effect=self.mock_list_study_plans))
        self.stack.enter_context(patch.object(app_module, "get_study_plan", side_effect=self.mock_get_study_plan))
        self.stack.enter_context(patch.object(app_module, "delete_study_plan", side_effect=self.mock_delete_study_plan))
        self.stack.enter_context(
            patch.object(app_module, "get_study_plan_step_session_plan", side_effect=self.mock_get_study_plan_step_session_plan)
        )
        self.stack.enter_context(
            patch.object(app_module, "save_study_plan_quiz_result", side_effect=self.mock_save_study_plan_quiz_result)
        )
        self.stack.enter_context(
            patch.object(app_module, "update_study_plan_step_status", side_effect=self.mock_update_study_plan_step_status)
        )
        self.stack.enter_context(
            patch.object(app_module, "get_admin_dashboard_snapshot", side_effect=self.mock_get_admin_dashboard_snapshot)
        )
        self.stack.enter_context(patch.object(app_module, "save_topic_record", side_effect=self.mock_save_topic_record))
        self.stack.enter_context(patch.object(app_module, "save_question_record", side_effect=self.mock_save_question_record))
        self.stack.enter_context(patch.object(app_module, "save_role_record", side_effect=self.mock_save_role_record))
        self.stack.enter_context(
            patch.object(app_module, "archive_topic_record", side_effect=self.mock_archive_topic_record)
        )
        self.stack.enter_context(
            patch.object(app_module, "archive_question_record", side_effect=self.mock_archive_question_record)
        )
        self.stack.enter_context(
            patch.object(app_module, "archive_role_record", side_effect=self.mock_archive_role_record)
        )
        self.stack.enter_context(patch.object(app_module, "delete_topic_record", side_effect=self.mock_delete_topic_record))
        self.stack.enter_context(
            patch.object(app_module, "delete_question_record", side_effect=self.mock_delete_question_record)
        )
        self.stack.enter_context(patch.object(app_module, "delete_role_record", side_effect=self.mock_delete_role_record))
        self.stack.enter_context(patch.object(app_module, "model", _FakeWhisperModel()))

    def auth_headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    def mock_create_user(self, username, email, _password):
        return {
            "success": True,
            "user": {
                "user_id": self.signed_user["user_id"],
                "username": username,
                "email": email,
                "created_at": self.signed_user["created_at"],
            },
        }

    def mock_authenticate_user(self, identifier, _password):
        if identifier in {self.signed_user["email"], self.signed_user["username"]}:
            return {"success": True, "user": self.signed_user}
        return {"success": False, "error": "Invalid credentials"}

    def mock_get_user_by_id(self, user_id):
        if user_id == self.signed_user["user_id"]:
            return self.signed_user
        if user_id == self.other_user["user_id"]:
            return self.other_user
        return None

    def mock_get_user_interview_history(self, user_id, limit=20):
        if user_id != self.signed_user["user_id"]:
            return []
        return self.fixture["history"][:limit]

    def mock_get_topic_rating_summary(self, topic_id=None):
        ratings = self.fixture["ratings"]
        if topic_id:
            for rating in ratings:
                if rating["topic_id"] == topic_id:
                    return rating
            return {"topic_id": topic_id, "average_rating": None, "rating_count": 0}
        return ratings

    def mock_get_topic_activity_summary(self, topic_id=None):
        activity = self.fixture["activity"]
        if topic_id:
            for item in activity:
                if item["topic_id"] == topic_id:
                    return item
            return {"topic_id": topic_id, "interview_count": 0}
        return activity

    def mock_get_score_leaderboard(self, board="overall", limit=10, topic_id=None, current_user_id=None):
        resolved_board = str(board or "overall").strip().lower()
        if resolved_board not in {"overall", "weekly", "topic"}:
            resolved_board = "overall"

        if resolved_board == "topic":
            resolved_topic_id = str(topic_id or "").strip()
            if not resolved_topic_id:
                return {"success": False, "error": "Topic ID is required", "detail": "Choose a topic before requesting the topic leaderboard."}
            topic = next((entry for entry in self.admin_topics if entry["topic_id"] == resolved_topic_id), None)
            if not topic:
                return {"success": False, "error": "Selected topic does not exist", "detail": "The requested topic leaderboard could not be found."}
            title = f"{topic['title']} leaderboard"
            topic_payload = {"topic_id": topic["topic_id"], "title": topic["title"]}
            minimum_interviews = 2
        else:
            title = "Weekly leaderboard" if resolved_board == "weekly" else "Overall leaderboard"
            topic_payload = None
            minimum_interviews = 2 if resolved_board == "weekly" else 3

        entries = [
            {
                "rank": 1,
                "user_id": self.signed_user["user_id"],
                "display_name": self.signed_user["username"] if current_user_id == self.signed_user["user_id"] else "User_A1B2",
                "average_score": 84.0,
                "interview_count": 4,
                "latest_session_at": "2026-03-19 10:30:00",
                "is_current_user": current_user_id == self.signed_user["user_id"],
            },
            {
                "rank": 2,
                "user_id": self.other_user["user_id"],
                "display_name": self.other_user["username"] if current_user_id == self.other_user["user_id"] else "User_C3D4",
                "average_score": 79.5,
                "interview_count": 3,
                "latest_session_at": "2026-03-18 09:15:00",
                "is_current_user": current_user_id == self.other_user["user_id"],
            },
        ][: max(1, min(int(limit or 10), 50))]

        current_user_entry = next((entry for entry in entries if entry["is_current_user"]), None)
        current_user_progress = None
        if current_user_id:
            current_user_progress = {
                "user_id": current_user_id,
                "interview_count": 4 if current_user_id == self.signed_user["user_id"] else 1,
                "minimum_interviews": minimum_interviews,
                "is_ranked": current_user_entry is not None,
            }

        return {
            "success": True,
            "board": resolved_board,
            "title": title,
            "entries": entries,
            "current_user_entry": current_user_entry,
            "current_user_progress": current_user_progress,
            "minimum_interviews": minimum_interviews,
            "timeframe_days": 7 if resolved_board == "weekly" else None,
            "total_ranked_users": len(entries),
            "topic": topic_payload,
        }

    def mock_save_topic_rating(self, session_id, topic_id, rating, user_id=None):
        return {
            "success": True,
            "summary": {
                "topic_id": topic_id,
                "average_rating": float(rating),
                "rating_count": 1,
                "session_id": session_id,
                "user_id": user_id,
            },
        }

    def mock_save_interview_session(self, session_data):
        stored = {
            "session_id": session_data["session_id"],
            "user_id": session_data.get("user_id"),
            "topic": session_data["topic"],
            "final_score": session_data["final_score"],
            "created_at": session_data.get("interview_date", "2026-03-19T12:00:00"),
            "complete_data": copy.deepcopy(session_data),
        }
        self.saved_sessions[stored["session_id"]] = stored
        return stored["session_id"]

    def mock_get_interview_session(self, session_id):
        session = self.saved_sessions.get(session_id)
        return copy.deepcopy(session) if session else None

    def mock_generate_interview_pdf(self, session_data):
        pdf_path = Path(self.temp_dir) / f"{session_data.get('session_id', 'report')}.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n% mock report\n")
        return str(pdf_path)

    def refresh_question_counts(self):
        for topic in self.admin_topics:
            topic["question_count"] = sum(
                1
                for question in self.admin_questions
                if question["topic_id"] == topic["topic_id"] and question.get("is_active", True)
            )

    def mock_get_topic_catalog(self):
        return [copy.deepcopy(topic) for topic in self.admin_topics if topic.get("is_active", True)]

    def mock_get_role_catalog(self):
        return [copy.deepcopy(role) for role in self.admin_roles if role.get("is_active", True)]

    def mock_list_all_topics(self):
        self.refresh_question_counts()
        return copy.deepcopy(self.admin_topics)

    def mock_list_all_questions(self):
        return copy.deepcopy(self.admin_questions)

    def mock_list_all_roles(self):
        return copy.deepcopy(self.admin_roles)

    def mock_get_admin_dashboard_snapshot(self):
        return copy.deepcopy(self.admin_insights)

    def build_mock_study_plan(self, user_id, role_id, target_days):
        role = next((role for role in self.admin_roles if role["role_id"] == role_id), None)
        if not role:
            return {"success": False, "error": "Selected role does not exist"}

        topic = next((topic for topic in self.admin_topics if topic["topic_id"] == role["primary_topic_id"]), self.admin_topics[0])
        plan_id = f"plan-{len(self.study_plans) + 1:03d}"
        step_id = f"step-{len(self.study_plans) + 1:03d}"
        quiz_step_id = f"{step_id}-quiz"
        round_step_id = f"{step_id}-round"
        return {
            "success": True,
            "plan": {
                "plan_id": plan_id,
                "user_id": user_id,
                "role_id": role["role_id"],
                "role_title": role["title"],
                "title": f"{role['title']} {target_days}-day prep path",
                "target_days": int(target_days),
                "status": "active",
                "focus_topic_ids": [topic["topic_id"]],
                "step_count": 3,
                "completed_steps": 0,
                "plan_summary": {
                    "target_days": int(target_days),
                    "step_count": 3,
                    "topic_count": 1,
                    "mcq_quiz_count": 1,
                    "mixed_quiz_count": 0,
                    "mock_count": 1,
                    "phases": [
                        {
                            "phase_key": "foundation",
                            "title": "Topic foundation",
                            "day_range": "Day 1-5",
                            "description": "Revise and checkpoint one topic lane.",
                        }
                    ],
                },
                "created_at": "2026-03-19 10:30:00",
                "updated_at": "2026-03-19 10:30:00",
            },
            "steps": [
                {
                    "step_id": step_id,
                    "plan_id": plan_id,
                    "sequence_no": 1,
                    "phase_key": "foundation",
                    "step_type": "revise",
                    "scheduled_day": 1,
                    "scheduled_label": "Day 1",
                    "topic_id": topic["topic_id"],
                    "topic_title": topic["title"],
                    "role_id": role["role_id"],
                    "role_title": role["title"],
                    "question_ids": ["graphs_001"],
                    "status": "planned",
                    "snapshot": {
                        "headline": f"Revise {topic['title']}",
                        "description": "Practice fundamentals, examples, and trade-offs.",
                        "practice_prompts": ["Explain BFS."],
                        "material_topic_id": topic["topic_id"],
                    },
                    "updated_at": "2026-03-19 10:30:00",
                },
                {
                    "step_id": quiz_step_id,
                    "plan_id": plan_id,
                    "sequence_no": 2,
                    "phase_key": "reinforcement",
                    "step_type": "mcq_quiz",
                    "scheduled_day": 2,
                    "scheduled_label": "Day 2",
                    "topic_id": topic["topic_id"],
                    "topic_title": topic["title"],
                    "role_id": role["role_id"],
                    "role_title": role["title"],
                    "question_ids": ["graphs_001"],
                    "status": "planned",
                    "snapshot": {
                        "headline": f"{topic['title']} checkpoint quiz",
                        "description": "Run the quick checkpoint before the next harder round.",
                        "practice_prompts": ["Explain BFS."],
                        "stage_label": "Checkpoint quiz",
                        "question_count": 2,
                        "can_launch_quiz": True,
                        "recommended_duration": 8,
                        "quiz_items": [
                            {
                                "quiz_item_id": "graphs_001_quiz_1",
                                "prompt": "Which answer best fits this checkpoint prompt: Explain BFS.?",
                                "choices": [
                                    "Use recursion only and avoid mentioning the traversal order.",
                                    "Use a queue and explore nodes level by level from the source.",
                                    "Talk about general graph terms without answering the question.",
                                    "Focus only on space complexity and skip the main idea.",
                                ],
                                "correct_choice_index": 1,
                            },
                            {
                                "quiz_item_id": "graphs_001_quiz_2",
                                "prompt": "Which answer best fits this checkpoint prompt: When is BFS a good choice?",
                                "choices": [
                                    "BFS is useful when you need the shortest path in an unweighted graph.",
                                    "BFS should only be used for weighted shortest path problems.",
                                    "BFS is mainly for sorting arrays in place.",
                                    "BFS is the same as hashing and memoization.",
                                ],
                                "correct_choice_index": 0,
                            },
                        ],
                    },
                    "updated_at": "2026-03-19 10:30:00",
                },
                {
                    "step_id": round_step_id,
                    "plan_id": plan_id,
                    "sequence_no": 3,
                    "phase_key": "reinforcement",
                    "step_type": "topic_round",
                    "scheduled_day": 3,
                    "scheduled_label": "Day 3",
                    "topic_id": topic["topic_id"],
                    "topic_title": topic["title"],
                    "role_id": role["role_id"],
                    "role_title": role["title"],
                    "question_ids": ["graphs_001"],
                    "status": "planned",
                    "snapshot": {
                        "headline": f"{topic['title']} round 1",
                        "description": "Run the first topic round with direct answers and examples.",
                        "practice_prompts": ["Explain BFS."],
                        "stage_label": "Round 1",
                        "round_stage": 1,
                        "can_launch_interview": True,
                        "recommended_duration": 20,
                    },
                    "updated_at": "2026-03-19 10:30:00",
                }
            ],
            "materials": [
                {
                    "topic_id": topic["topic_id"],
                    "topic_title": topic["title"],
                    "overview": "Core fundamentals for role prep.",
                    "revision_notes": "Revise the pattern, use cases, and trade-offs.",
                    "common_mistakes": "Staying too abstract.",
                    "rapid_fire_points": ["Define it cleanly", "Use one example"],
                    "practice_prompts": ["Explain BFS."],
                    "estimated_minutes": 20,
                    "knowledge_card": {
                        "title": topic["title"],
                        "summary": "Core fundamentals for role prep.",
                        "rows": [{"label": "Revision block", "value": "20 min"}],
                    },
                    "answer_examples": [
                        {
                            "question": "Explain BFS.",
                            "sample_answer": "Use a queue and explore level by level.",
                            "ideal_answer": "Use a queue, mark nodes visited, and expand neighbors breadth first.",
                        }
                    ],
                    "interview_checks": ["Lead with the direct answer."],
                    "prompt_examples": ["Explain BFS."],
                    "updated_at": "2026-03-19 10:30:00",
                }
            ],
            "progress": {
                "completion_percent": 0,
                "average_score": 0,
                "completed_steps": 0,
                "total_steps": 3,
                "phase_breakdown": [
                    {"phase_key": "foundation", "title": "Foundation", "completed_steps": 0, "total_steps": 1, "average_score": 0},
                    {"phase_key": "reinforcement", "title": "Reinforcement", "completed_steps": 0, "total_steps": 2, "average_score": 0},
                ],
                "topic_progress": [
                    {"topic_id": topic["topic_id"], "topic_title": topic["title"], "completed_rounds": 0, "total_rounds": 2, "average_score": 0}
                ],
                "score_history": [],
                "next_steps": [{"step_id": step_id, "scheduled_label": "Day 1", "headline": f"Revise {topic['title']}", "step_type": "revise"}],
                "current_focus": {"step_id": step_id, "scheduled_label": "Day 1", "headline": f"Revise {topic['title']}", "step_type": "revise"},
                "target_days": int(target_days),
            },
        }

    def mock_create_study_plan(self, user_id, role_id, target_days):
        result = self.build_mock_study_plan(user_id, role_id, target_days)
        if result.get("success"):
            self.study_plans.insert(0, copy.deepcopy(result))
        return result

    def mock_list_study_plans(self, user_id, limit=8):
        return [copy.deepcopy(item["plan"]) for item in self.study_plans if item["plan"]["user_id"] == user_id][:limit]

    def mock_get_study_plan(self, plan_id, user_id):
        for item in self.study_plans:
            if item["plan"]["plan_id"] == plan_id and item["plan"]["user_id"] == user_id:
                return copy.deepcopy(item)
        return {"success": False, "error": "Study plan not found"}

    def mock_delete_study_plan(self, user_id, plan_id):
        for index, item in enumerate(self.study_plans):
            if item["plan"]["plan_id"] == plan_id and item["plan"]["user_id"] == user_id:
                self.study_plans.pop(index)
                return {"success": True, "plan_id": plan_id}
        return {"success": False, "error": "Study plan not found"}

    def mock_get_study_plan_step_session_plan(self, user_id, plan_id, step_id):
        plan = self.mock_get_study_plan(plan_id, user_id)
        if not plan.get("success"):
            return plan
        step = next((entry for entry in plan["steps"] if entry["step_id"] == step_id), None)
        if not step:
            return {"success": False, "error": "Study step not found"}
        if step["step_type"] == "revise":
            return {"success": False, "error": "This step is a revision block, not a runnable interview."}
        if step["step_type"] == "mcq_quiz":
            return {"success": False, "error": "This step is an MCQ checkpoint, not a runnable interview."}
        return {
            "success": True,
            "plan": {
                "mode": "topic",
                "topic_id": step["topic_id"],
                "title": step["snapshot"]["headline"],
                "subtitle": step["snapshot"]["description"],
                "duration_minutes": 20,
                "blueprint_label": "Round 1",
                "primary_topic_id": step["topic_id"],
                "study_context": {
                    "study_plan_id": plan_id,
                    "study_step_id": step_id,
                    "step_type": step["step_type"],
                    "round_stage": 1,
                    "scheduled_label": step["scheduled_label"],
                },
                "questions": [
                    {
                        "question_id": "graphs_001",
                        "topic_id": step["topic_id"],
                        "q": "Explain BFS.",
                        "difficulty": "easy",
                        "sample_answer": "Use a queue and explore level by level.",
                        "ideal_answer": "Use a queue, mark nodes visited, and expand neighbors breadth first.",
                        "section_label": "Round 1",
                    }
                ],
            },
            "step": copy.deepcopy(step),
            "progress": copy.deepcopy(plan["progress"]),
        }

    def mock_save_study_plan_quiz_result(self, user_id, plan_id, step_id, answers):
        for item in self.study_plans:
            if item["plan"]["plan_id"] != plan_id or item["plan"]["user_id"] != user_id:
                continue

            step = next((entry for entry in item["steps"] if entry["step_id"] == step_id), None)
            if not step:
                return {"success": False, "error": "Study step not found"}
            if step["step_type"] != "mcq_quiz":
                return {"success": False, "error": "This step is not an MCQ checkpoint."}

            quiz_items = step["snapshot"].get("quiz_items") or []
            if len(answers) != len(quiz_items):
                return {"success": False, "error": "Answer every checkpoint question before submitting."}

            review_items = []
            correct_answers = 0
            for index, quiz_item in enumerate(quiz_items):
                selected_index = int(answers[index])
                correct_index = int(quiz_item["correct_choice_index"])
                is_correct = selected_index == correct_index
                if is_correct:
                    correct_answers += 1
                review_items.append(
                    {
                        "quiz_item_id": quiz_item["quiz_item_id"],
                        "prompt": quiz_item["prompt"],
                        "selected_index": selected_index,
                        "selected_choice": quiz_item["choices"][selected_index],
                        "correct_index": correct_index,
                        "correct_choice": quiz_item["choices"][correct_index],
                        "is_correct": is_correct,
                        "explanation": quiz_item["choices"][correct_index],
                    }
                )

            score = round((correct_answers / len(quiz_items)) * 100) if quiz_items else 0
            step["status"] = "done"
            step["snapshot"]["last_score"] = score
            step["snapshot"]["best_score"] = score
            step["snapshot"]["attempt_count"] = int(step["snapshot"].get("attempt_count") or 0) + 1
            step["snapshot"]["average_score"] = score
            step["snapshot"]["last_quiz_result"] = {
                "score": score,
                "correct_answers": correct_answers,
                "total_questions": len(quiz_items),
            }
            step["snapshot"]["last_quiz_review"] = review_items
            item["plan"]["completed_steps"] = sum(1 for entry in item["steps"] if entry["status"] == "done")
            item["plan"]["status"] = "completed" if item["plan"]["completed_steps"] == item["plan"]["step_count"] else "active"
            if item.get("progress"):
                item["progress"]["completed_steps"] = item["plan"]["completed_steps"]
                item["progress"]["completion_percent"] = round(
                    (item["plan"]["completed_steps"] / item["plan"]["step_count"]) * 100
                ) if item["plan"]["step_count"] else 0
                item["progress"]["average_score"] = score
                item["progress"]["score_history"] = [score]
            return copy.deepcopy(item)

        return {"success": False, "error": "Study step not found"}

    def mock_update_study_plan_step_status(self, user_id, plan_id, step_id, status):
        for item in self.study_plans:
            if item["plan"]["plan_id"] != plan_id or item["plan"]["user_id"] != user_id:
                continue
            for step in item["steps"]:
                if step["step_id"] == step_id:
                    step["status"] = status
                    if status == "planned":
                        for key in [
                            "last_score",
                            "last_completed_at",
                            "last_quiz_result",
                            "last_quiz_review",
                            "last_session_id",
                            "last_confidence",
                            "last_content_score",
                            "last_delivery_score",
                            "last_wpm",
                            "last_fillers",
                        ]:
                            step["snapshot"].pop(key, None)
                    item["plan"]["completed_steps"] = sum(1 for entry in item["steps"] if entry["status"] == "done")
                    item["plan"]["status"] = "completed" if item["plan"]["completed_steps"] == item["plan"]["step_count"] else "active"
                    if item.get("progress"):
                        item["progress"]["completed_steps"] = item["plan"]["completed_steps"]
                        item["progress"]["completion_percent"] = round(
                            (item["plan"]["completed_steps"] / item["plan"]["step_count"]) * 100
                        ) if item["plan"]["step_count"] else 0
                        score_values = [
                            entry["snapshot"].get("last_score")
                            for entry in item["steps"]
                            if entry["status"] == "done" and entry["snapshot"].get("last_score") not in (None, "")
                        ]
                        item["progress"]["average_score"] = round(sum(score_values) / len(score_values)) if score_values else 0
                        item["progress"]["score_history"] = score_values[-8:]
                    return copy.deepcopy(item)
        return {"success": False, "error": "Study step not found"}

    def mock_save_topic_record(self, payload, topic_id=None):
        resolved_topic_id = str(topic_id or payload.get("topic_id") or "").strip()
        title = str(payload.get("title") or "").strip()
        if not resolved_topic_id:
            return {"success": False, "error": "Topic ID is required"}
        if not title:
            return {"success": False, "error": "Topic title is required"}

        existing = next((topic for topic in self.admin_topics if topic["topic_id"] == resolved_topic_id), None)
        topic_record = {
            "topic_id": resolved_topic_id,
            "category": payload.get("category") or "General",
            "title": title,
            "subtitle": payload.get("subtitle") or title,
            "description": payload.get("description") or title,
            "level_label": payload.get("level_label") or "Intermediate",
            "accent": payload.get("accent") or resolved_topic_id,
            "question_count": existing["question_count"] if existing else 0,
            "is_active": existing["is_active"] if existing else True,
        }
        if existing:
            existing.update(topic_record)
        else:
            self.admin_topics.append(topic_record)
        return {"success": True, "topic": copy.deepcopy(topic_record)}

    def mock_save_question_record(self, payload, question_id=None):
        resolved_question_id = str(question_id or payload.get("question_id") or "").strip() or f"generated_{len(self.admin_questions)+1}"
        topic_id = str(payload.get("topic_id") or "").strip()
        if not any(topic["topic_id"] == topic_id for topic in self.admin_topics):
            return {"success": False, "error": "Selected topic does not exist"}

        existing = next((question for question in self.admin_questions if question["question_id"] == resolved_question_id), None)
        question_record = {
            "question_id": resolved_question_id,
            "topic_id": topic_id,
            "question_text": payload.get("question_text") or "",
            "difficulty": payload.get("difficulty") or "medium",
            "sample_answer": payload.get("sample_answer") or "",
            "ideal_answer": payload.get("ideal_answer") or "",
            "display_order": int(payload.get("display_order") or 1),
            "is_active": existing["is_active"] if existing else True,
        }
        if existing:
            existing.update(question_record)
        else:
            self.admin_questions.append(question_record)
        self.refresh_question_counts()
        return {"success": True, "question": copy.deepcopy(question_record)}

    def mock_save_role_record(self, payload, role_id=None):
        resolved_role_id = str(role_id or payload.get("role_id") or "").strip()
        if not resolved_role_id:
            return {"success": False, "error": "Role ID is required"}

        existing = next((role for role in self.admin_roles if role["role_id"] == resolved_role_id), None)
        role_record = {
            "role_id": resolved_role_id,
            "title": payload.get("title") or "",
            "subtitle": payload.get("subtitle") or "",
            "description": payload.get("description") or "",
            "level_label": payload.get("level_label") or "Interview loop",
            "default_duration": int(payload.get("default_duration") or 30),
            "available_durations": list(payload.get("available_durations") or [30]),
            "topic_weights": dict(payload.get("topic_weights") or {}),
            "primary_topic_id": payload.get("primary_topic_id") or "graphs",
            "is_active": existing["is_active"] if existing else True,
        }
        if existing:
            existing.update(role_record)
        else:
            self.admin_roles.append(role_record)
        return {"success": True, "role": copy.deepcopy(role_record)}

    def update_record_active_state(self, records, record_key, record_id, is_active, label):
        record = next((item for item in records if item[record_key] == record_id), None)
        if not record:
            return {"success": False, "error": f"{label} not found"}
        record["is_active"] = bool(is_active)
        if label == "Question":
            self.refresh_question_counts()
            return {"success": True, "question": copy.deepcopy(record)}
        if label == "Topic":
            return {"success": True, "topic": copy.deepcopy(record)}
        return {"success": True, "role": copy.deepcopy(record)}

    def delete_record(self, records, record_key, record_id, label):
        index = next((idx for idx, item in enumerate(records) if item[record_key] == record_id), None)
        if index is None:
            return {"success": False, "error": f"{label} not found"}
        records.pop(index)
        if label == "Question":
            self.refresh_question_counts()
        return {"success": True}

    def mock_archive_topic_record(self, topic_id, is_active):
        return self.update_record_active_state(self.admin_topics, "topic_id", topic_id, is_active, "Topic")

    def mock_archive_question_record(self, question_id, is_active):
        return self.update_record_active_state(self.admin_questions, "question_id", question_id, is_active, "Question")

    def mock_archive_role_record(self, role_id, is_active):
        return self.update_record_active_state(self.admin_roles, "role_id", role_id, is_active, "Role")

    def mock_delete_topic_record(self, topic_id):
        return self.delete_record(self.admin_topics, "topic_id", topic_id, "Topic")

    def mock_delete_question_record(self, question_id):
        return self.delete_record(self.admin_questions, "question_id", question_id, "Question")

    def mock_delete_role_record(self, role_id):
        return self.delete_record(self.admin_roles, "role_id", role_id, "Role")

    def test_page_routes_render(self):
        for route in ["/", "/auth", "/profile", "/prep-paths", "/leaderboards", "/interview", "/results"]:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200, route)
            self.assertIn("<!DOCTYPE html>", response.text)

    def test_auth_signup_and_login_return_token(self):
        signup_response = self.client.post(
            "/api/auth/signup",
            json={"username": "mockuser", "email": "mockuser@example.com", "password": "password123"},
        )
        login_response = self.client.post(
            "/api/auth/login",
            json={"identifier": "mockuser@example.com", "password": "password123"},
        )

        self.assertEqual(signup_response.status_code, 200)
        self.assertTrue(signup_response.json()["success"])
        self.assertIn("token", signup_response.json())

        self.assertEqual(login_response.status_code, 200)
        self.assertTrue(login_response.json()["success"])
        self.assertIn("token", login_response.json())

    def test_profile_routes_require_and_accept_token(self):
        unauthorized = self.client.get(f"/api/auth/users/{self.signed_user['user_id']}")
        self.assertEqual(unauthorized.status_code, 401)

        authorized = self.client.get(
            f"/api/auth/users/{self.signed_user['user_id']}",
            headers=self.auth_headers(self.signed_token),
        )
        history = self.client.get(
            f"/api/auth/users/{self.signed_user['user_id']}/history",
            headers=self.auth_headers(self.signed_token),
        )

        self.assertEqual(authorized.status_code, 200)
        self.assertEqual(authorized.json()["user"]["email"], self.signed_user["email"])
        self.assertEqual(history.status_code, 200)
        self.assertEqual(len(history.json()["history"]), 1)

    def test_topic_summary_routes_are_connected(self):
        ratings_response = self.client.get("/api/ratings/topics")
        summary_response = self.client.get("/api/topics/summary")

        self.assertEqual(ratings_response.status_code, 200)
        self.assertTrue(ratings_response.json()["success"])
        self.assertEqual(len(ratings_response.json()["ratings"]), 2)

        self.assertEqual(summary_response.status_code, 200)
        self.assertTrue(summary_response.json()["success"])
        self.assertEqual(len(summary_response.json()["activity"]), 2)

    def test_leaderboard_endpoint_supports_board_modes_and_topic_validation(self):
        overall_response = self.client.get("/api/leaderboards", headers=self.auth_headers(self.signed_token))
        weekly_response = self.client.get("/api/leaderboards?board=weekly", headers=self.auth_headers(self.signed_token))
        topic_response = self.client.get("/api/leaderboards?board=topic&topic_id=graphs", headers=self.auth_headers(self.signed_token))
        missing_topic_response = self.client.get("/api/leaderboards?board=topic", headers=self.auth_headers(self.signed_token))

        self.assertEqual(overall_response.status_code, 200)
        self.assertTrue(overall_response.json()["success"])
        self.assertEqual(overall_response.json()["board"], "overall")
        self.assertEqual(overall_response.json()["entries"][0]["display_name"], self.signed_user["username"])

        self.assertEqual(weekly_response.status_code, 200)
        self.assertTrue(weekly_response.json()["success"])
        self.assertEqual(weekly_response.json()["timeframe_days"], 7)

        self.assertEqual(topic_response.status_code, 200)
        self.assertTrue(topic_response.json()["success"])
        self.assertEqual(topic_response.json()["topic"]["topic_id"], "graphs")
        self.assertEqual(topic_response.json()["minimum_interviews"], 2)

        self.assertEqual(missing_topic_response.status_code, 200)
        self.assertFalse(missing_topic_response.json()["success"])
        self.assertEqual(missing_topic_response.json()["error"], "Topic ID is required")

    def test_catalog_and_admin_access_require_correct_permissions(self):
        catalog_response = self.client.get("/api/interview/catalog")
        admin_access_response = self.client.get("/api/admin/access", headers=self.auth_headers(self.signed_token))
        non_admin_access_response = self.client.get("/api/admin/access", headers=self.auth_headers(self.other_token))
        admin_bootstrap = self.client.get("/api/admin/bootstrap", headers=self.auth_headers(self.signed_token))
        blocked_bootstrap = self.client.get("/api/admin/bootstrap", headers=self.auth_headers(self.other_token))

        self.assertEqual(catalog_response.status_code, 200)
        self.assertTrue(catalog_response.json()["success"])
        self.assertEqual(len(catalog_response.json()["topics"]), 1)
        self.assertEqual(len(catalog_response.json()["roles"]), 1)

        self.assertEqual(admin_access_response.status_code, 200)
        self.assertTrue(admin_access_response.json()["is_admin"])
        self.assertEqual(non_admin_access_response.status_code, 200)
        self.assertFalse(non_admin_access_response.json()["is_admin"])

        self.assertEqual(admin_bootstrap.status_code, 200)
        self.assertTrue(admin_bootstrap.json()["success"])
        self.assertEqual(len(admin_bootstrap.json()["topics"]), 2)
        self.assertEqual(admin_bootstrap.json()["insights"]["overview"]["total_users"], 2)
        self.assertEqual(blocked_bootstrap.status_code, 403)

    def test_admin_access_uses_strict_database_boolean_parsing(self):
        with patch.object(app_module, "get_user_by_id", return_value={"user_id": "user-123", "is_admin": "0"}):
            self.assertFalse(app_module.is_admin_user({"user_id": "user-123"}))

        with patch.object(app_module, "get_user_by_id", return_value={"user_id": "user-123", "is_admin": "1"}):
            self.assertTrue(app_module.is_admin_user({"user_id": "user-123"}))

    def test_study_plan_endpoints_require_auth_and_return_saved_plan(self):
        unauthorized = self.client.get("/api/study-plans")
        self.assertEqual(unauthorized.status_code, 401)

        create_response = self.client.post(
            "/api/study-plans",
            json={"role_id": "backend_engineer", "target_days": 40},
            headers=self.auth_headers(self.signed_token),
        )
        self.assertEqual(create_response.status_code, 200)
        self.assertTrue(create_response.json()["success"])
        plan_id = create_response.json()["plan"]["plan_id"]
        step_id = create_response.json()["steps"][0]["step_id"]
        quiz_step_id = create_response.json()["steps"][1]["step_id"]
        runnable_step_id = create_response.json()["steps"][2]["step_id"]

        list_response = self.client.get("/api/study-plans", headers=self.auth_headers(self.signed_token))
        detail_response = self.client.get(f"/api/study-plans/{plan_id}", headers=self.auth_headers(self.signed_token))
        session_plan_response = self.client.get(
            f"/api/study-plans/{plan_id}/steps/{runnable_step_id}/session-plan",
            headers=self.auth_headers(self.signed_token),
        )
        quiz_result_response = self.client.post(
            f"/api/study-plans/{plan_id}/steps/{quiz_step_id}/quiz-result",
            json={"answers": [1, 0]},
            headers=self.auth_headers(self.signed_token),
        )
        update_response = self.client.put(
            f"/api/study-plans/{plan_id}/steps/{step_id}",
            json={"status": "done"},
            headers=self.auth_headers(self.signed_token),
        )
        delete_response = self.client.delete(f"/api/study-plans/{plan_id}", headers=self.auth_headers(self.signed_token))
        list_after_delete = self.client.get("/api/study-plans", headers=self.auth_headers(self.signed_token))

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()["plans"]), 1)
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.json()["plan"]["role_id"], "backend_engineer")
        self.assertEqual(session_plan_response.status_code, 200)
        self.assertEqual(session_plan_response.json()["plan"]["study_context"]["study_step_id"], runnable_step_id)
        self.assertEqual(quiz_result_response.status_code, 200)
        self.assertEqual(quiz_result_response.json()["steps"][1]["snapshot"]["last_score"], 100)
        self.assertEqual(quiz_result_response.json()["plan"]["completed_steps"], 1)
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["plan"]["completed_steps"], 2)
        self.assertEqual(update_response.json()["plan"]["status"], "active")
        self.assertEqual(delete_response.status_code, 200)
        self.assertTrue(delete_response.json()["success"])
        self.assertEqual(list_after_delete.status_code, 200)
        self.assertEqual(len(list_after_delete.json()["plans"]), 0)

    def test_study_plan_quiz_step_can_be_reset_for_a_clean_retake(self):
        create_response = self.client.post(
            "/api/study-plans",
            json={"role_id": "backend_engineer", "target_days": 21},
            headers=self.auth_headers(self.signed_token),
        )
        self.assertEqual(create_response.status_code, 200)

        plan_id = create_response.json()["plan"]["plan_id"]
        quiz_step_id = create_response.json()["steps"][1]["step_id"]

        quiz_result_response = self.client.post(
            f"/api/study-plans/{plan_id}/steps/{quiz_step_id}/quiz-result",
            json={"answers": [1, 0]},
            headers=self.auth_headers(self.signed_token),
        )
        reset_response = self.client.put(
            f"/api/study-plans/{plan_id}/steps/{quiz_step_id}",
            json={"status": "planned"},
            headers=self.auth_headers(self.signed_token),
        )

        self.assertEqual(quiz_result_response.status_code, 200)
        self.assertEqual(reset_response.status_code, 200)
        quiz_step = next(step for step in reset_response.json()["steps"] if step["step_id"] == quiz_step_id)
        self.assertEqual(quiz_step["status"], "planned")
        self.assertNotIn("last_quiz_review", quiz_step["snapshot"])
        self.assertNotIn("last_quiz_result", quiz_step["snapshot"])
        self.assertNotIn("last_score", quiz_step["snapshot"])
        self.assertEqual(reset_response.json()["progress"]["completed_steps"], 0)
        self.assertEqual(reset_response.json()["progress"]["average_score"], 0)

    def test_admin_topic_crud_endpoints(self):
        headers = self.auth_headers(self.signed_token)
        create_payload = {
            "topic_id": "apis",
            "category": "Backend",
            "title": "API Design",
            "subtitle": "Contract and integration questions",
            "description": "API interview rounds",
            "level_label": "Intermediate",
            "accent": "apis",
        }

        create_response = self.client.post("/api/admin/topics", json=create_payload, headers=headers)
        update_response = self.client.put(
            "/api/admin/topics/apis",
            json={**create_payload, "title": "API Design Deep Dive"},
            headers=headers,
        )
        archive_response = self.client.post("/api/admin/topics/apis/archive", headers=headers)
        catalog_after_archive = self.client.get("/api/interview/catalog")
        restore_response = self.client.post("/api/admin/topics/apis/restore", headers=headers)
        delete_response = self.client.delete("/api/admin/topics/apis", headers=headers)

        self.assertEqual(create_response.status_code, 200)
        self.assertTrue(create_response.json()["success"])
        self.assertEqual(create_response.json()["topic"]["title"], "API Design")

        self.assertEqual(update_response.status_code, 200)
        self.assertTrue(update_response.json()["success"])
        self.assertEqual(update_response.json()["topic"]["title"], "API Design Deep Dive")

        self.assertEqual(archive_response.status_code, 200)
        self.assertTrue(archive_response.json()["success"])
        self.assertFalse(archive_response.json()["topic"]["is_active"])
        self.assertNotIn("apis", {topic["topic_id"] for topic in catalog_after_archive.json()["topics"]})

        self.assertEqual(restore_response.status_code, 200)
        self.assertTrue(restore_response.json()["success"])
        self.assertTrue(restore_response.json()["topic"]["is_active"])

        self.assertEqual(delete_response.status_code, 200)
        self.assertTrue(delete_response.json()["success"])
        self.assertNotIn("apis", {topic["topic_id"] for topic in self.admin_topics})

    def test_admin_question_and_role_crud_endpoints(self):
        headers = self.auth_headers(self.signed_token)
        question_payload = {
            "question_id": "graphs_010",
            "topic_id": "graphs",
            "question_text": "How would you detect a cycle in a graph?",
            "difficulty": "medium",
            "display_order": 10,
            "sample_answer": "Use DFS with visited states.",
            "ideal_answer": "Use DFS recursion stack for directed graphs or DSU for undirected graphs.",
        }
        role_payload = {
            "role_id": "platform_engineer",
            "title": "Platform Engineer",
            "subtitle": "Infra and reliability",
            "description": "Platform reliability interview loop",
            "level_label": "Senior",
            "default_duration": 45,
            "available_durations": [30, 45, 60],
            "topic_weights": {"graphs": 100},
            "primary_topic_id": "graphs",
        }

        create_question = self.client.post("/api/admin/questions", json=question_payload, headers=headers)
        update_question = self.client.put(
            "/api/admin/questions/graphs_010",
            json={**question_payload, "question_text": "How do you detect a graph cycle efficiently?"},
            headers=headers,
        )
        archive_question = self.client.post("/api/admin/questions/graphs_010/archive", headers=headers)
        restore_question = self.client.post("/api/admin/questions/graphs_010/restore", headers=headers)
        delete_question = self.client.delete("/api/admin/questions/graphs_010", headers=headers)

        create_role = self.client.post("/api/admin/roles", json=role_payload, headers=headers)
        update_role = self.client.put(
            "/api/admin/roles/platform_engineer",
            json={**role_payload, "title": "Platform Reliability Engineer"},
            headers=headers,
        )
        archive_role = self.client.post("/api/admin/roles/platform_engineer/archive", headers=headers)
        restore_role = self.client.post("/api/admin/roles/platform_engineer/restore", headers=headers)
        delete_role = self.client.delete("/api/admin/roles/platform_engineer", headers=headers)

        self.assertTrue(create_question.json()["success"])
        self.assertEqual(create_question.json()["question"]["question_id"], "graphs_010")
        self.assertTrue(update_question.json()["success"])
        self.assertIn("efficiently", update_question.json()["question"]["question_text"])
        self.assertTrue(archive_question.json()["success"])
        self.assertFalse(archive_question.json()["question"]["is_active"])
        self.assertTrue(restore_question.json()["success"])
        self.assertTrue(delete_question.json()["success"])
        self.assertNotIn("graphs_010", {question["question_id"] for question in self.admin_questions})

        self.assertTrue(create_role.json()["success"])
        self.assertEqual(create_role.json()["role"]["role_id"], "platform_engineer")
        self.assertTrue(update_role.json()["success"])
        self.assertEqual(update_role.json()["role"]["title"], "Platform Reliability Engineer")
        self.assertTrue(archive_role.json()["success"])
        self.assertFalse(archive_role.json()["role"]["is_active"])
        self.assertTrue(restore_role.json()["success"])
        self.assertTrue(delete_role.json()["success"])
        self.assertNotIn("platform_engineer", {role["role_id"] for role in self.admin_roles})

    def test_guest_save_get_and_pdf_routes_work(self):
        guest_payload = {
            "session_id": "guest-session-new",
            "topic": "graphs",
            "final_score": 81,
            "questions_total": 1,
            "questions": [
                {
                    "question": "Explain BFS.",
                    "answer": "It explores level by level.",
                    "confidence": 81,
                    "wpm": 138,
                    "duration": 22,
                    "filler_words": [],
                    "filler_count": 0,
                }
            ],
            "confidence_history": [81],
            "wpm_history": [138],
            "filler_history": [0],
            "interview_date": "2026-03-19T12:15:00",
        }

        save_response = self.client.post("/save-interview", json=guest_payload)
        get_response = self.client.get("/get-session/guest-session-new")
        pdf_response = self.client.get("/generate-pdf/guest-session-new")

        self.assertEqual(save_response.status_code, 200)
        self.assertTrue(save_response.json()["success"])
        self.assertEqual(get_response.status_code, 200)
        self.assertTrue(get_response.json()["success"])
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response.headers["content-type"], "application/pdf")

    def test_signed_session_routes_require_owner_token(self):
        session_id = self.fixture["sessions"]["signed"]["session_id"]
        signed_payload = self.fixture["sessions"]["signed"]["complete_data"]

        no_auth_response = self.client.get(f"/get-session/{session_id}")
        wrong_auth_response = self.client.get(
            f"/get-session/{session_id}",
            headers=self.auth_headers(self.other_token),
        )
        save_wrong_user = self.client.post(
            "/save-interview",
            json=signed_payload,
            headers=self.auth_headers(self.other_token),
        )
        save_right_user = self.client.post(
            "/save-interview",
            json=signed_payload,
            headers=self.auth_headers(self.signed_token),
        )
        pdf_right_user = self.client.get(
            f"/generate-pdf/{session_id}",
            headers=self.auth_headers(self.signed_token),
        )

        self.assertEqual(no_auth_response.status_code, 401)
        self.assertEqual(wrong_auth_response.status_code, 403)
        self.assertEqual(save_wrong_user.status_code, 403)
        self.assertEqual(save_right_user.status_code, 200)
        self.assertTrue(save_right_user.json()["success"])
        self.assertEqual(pdf_right_user.status_code, 200)

    def test_ratings_respect_authenticated_user(self):
        payload = {
            "session_id": self.fixture["sessions"]["signed"]["session_id"],
            "topic_id": "systemdesign",
            "rating": 5,
            "user_id": self.signed_user["user_id"],
        }

        no_auth_response = self.client.post("/api/ratings", json=payload)
        auth_response = self.client.post(
            "/api/ratings",
            json=payload,
            headers=self.auth_headers(self.signed_token),
        )

        self.assertEqual(no_auth_response.status_code, 401)
        self.assertEqual(auth_response.status_code, 200)
        self.assertTrue(auth_response.json()["success"])
        self.assertEqual(auth_response.json()["summary"]["average_rating"], 5.0)

    def test_save_interview_returns_clear_failure_payload(self):
        with patch.object(
            app_module,
            "save_interview_session",
            return_value={
                "success": False,
                "error": "Failed to save interview session",
                "detail": "The 'topic' field is required before the session can be saved.",
            },
        ):
            response = self.client.post("/save-interview", json={"session_id": "broken-save", "final_score": 82})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["success"])
        self.assertEqual(response.json()["error"], "Failed to save interview session")
        self.assertIn("topic", response.json()["detail"])

    def test_transcribe_returns_mock_analysis(self):
        response = self.client.post(
            "/transcribe",
            files={"file": ("answer.webm", b"fake-audio", "audio/webm")},
            data={"difficulty": "medium", "topic": "graphs", "question": "Explain BFS"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["overall_score"], 82)
        self.assertEqual(response.json()["transcript"], self.fixture["transcribe_analysis"]["transcript"])

    def test_transcribe_rejects_oversized_uploads(self):
        with patch.object(app_module, "MAX_AUDIO_UPLOAD_BYTES", 5):
            response = self.client.post(
                "/transcribe",
                files={"file": ("answer.webm", b"123456", "audio/webm")},
                data={"difficulty": "medium", "topic": "graphs", "question": "Explain BFS"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("too large", response.json()["error"].lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
