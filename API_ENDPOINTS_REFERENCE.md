# API Endpoints Reference

## Authentication Endpoints

### POST /api/auth/signup
**Purpose:** Register new user  
**File:** main.py → signup()  
**Database:** database.create_user()

**Request:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password_8_chars_min"
}
```

**Response (Success):**
```json
{
  "success": true,
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "is_admin": false
  },
  "token": "encoded_payload.signature"
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Password must be at least 8 characters"
}
```

---

### POST /api/auth/login
**Purpose:** Authenticate user, get JWT token  
**File:** main.py → login()  
**Database:** database.authenticate_user()

**Request:**
```json
{
  "identifier": "john_doe",  // username OR email
  "password": "secure_password"
}
```

**Response (Success):**
```json
{
  "success": true,
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "is_admin": false
  },
  "token": "encoded_payload.signature"
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "User not found"
}
```

**Usage:**
```javascript
// Frontend
const token = response.token;
localStorage.setItem('auth_token', token);

// All future requests include:
// Header: Authorization: Bearer <token>
```

---

### GET /api/auth/users/{user_id}
**Purpose:** Get authenticated user's profile  
**File:** main.py → get_user_profile()  
**Database:** database.get_user_by_id()  
**Auth Required:** Yes (same user or admin)

**Request Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "is_admin": false,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

---

### GET /api/auth/users/{user_id}/history
**Purpose:** Get user's interview session history  
**File:** main.py → get_user_interview_history()  
**Database:** database.get_user_interview_history()  
**Auth Required:** Yes (same user or admin)

**Response:**
```json
{
  "success": true,
  "history": [
    {
      "session_id": "session-123",
      "topic_id": "algorithms",
      "average_score": 75,
      "completed_at": "2024-02-15T14:30:00Z"
    },
    {
      "session_id": "session-122",
      "topic_id": "systemdesign",
      "average_score": 68,
      "completed_at": "2024-02-14T11:00:00Z"
    }
  ]
}
```

---

## Interview Catalog Endpoints

### GET /api/interview/catalog
**Purpose:** Get all available topics, roles, questions  
**File:** main.py → get_interview_catalog()  
**Database:** database.list_all_topics(), list_all_roles(), list_all_questions()

**Response:**
```json
{
  "success": true,
  "topics": [
    {
      "topic_id": "algorithms",
      "title": "Algorithms",
      "category": "coding",
      "description": "Sorting, searching, dynamic programming, graphs",
      "level_label": "Intermediate",
      "estimated_minutes": 22
    }
  ],
  "roles": [
    {
      "role_id": "senior_backend",
      "title": "Senior Backend Engineer",
      "description": "...",
      "topic_weights": {"algorithms": 2, "systemdesign": 3}
    }
  ],
  "questions": [
    {
      "question_id": "algo_bfs_101",
      "question_text": "Explain breadth-first search",
      "topic_id": "algorithms",
      "difficulty": "medium"
    }
  ]
}
```

---

## Interview Session Endpoints

### POST /api/interview/session
**Purpose:** Start new interview session  
**File:** main.py → start_interview_session()  
**Database:** database.get_interview_session_plan()  
**Auth Required:** Optional (no user = anonymous)

**Request:**
```json
{
  "topic_id": "algorithms",  // OR role_id OR custom_interview_id
  "duration_minutes": 30
}
```

**Response:**
```json
{
  "success": true,
  "session": {
    "session_id": "session-550e8400-e29b-41d4",
    "interview_plan": {
      "session_type": "topic",
      "topic_name": "Algorithms",
      "questions": [
        {
          "question_id": "algo_bfs_101",
          "question_text": "Explain BFS algorithm",
          "duration_seconds": 90
        },
        {
          "question_id": "algo_dfs_102",
          "question_text": "Compare DFS vs BFS",
          "duration_seconds": 120
        }
      ]
    }
  }
}
```

---

### POST /api/upload-audio/{question_id}
**Purpose:** Upload audio answer, transcribe, score  
**File:** main.py → upload_audio()  
**Process:**
1. Validate audio file
2. Transcribe with Whisper
3. Score via analytics.analyze_transcript()
4. Save to database
**Database:** database.save_question_record()

**Request (multipart/form-data):**
```
- audio_file: <audio blob>
- session_id: session-123
```

**Response:**
```json
{
  "success": true,
  "question_id": "algo_bfs_101",
  "transcript": "BFS is a tree traversal algorithm that uses a queue. It visits all nodes at the current depth before moving to the next depth.",
  "score": 72,
  "feedback": "✓ Good: You mentioned BFS, queue, tree traversal | → Consider: time complexity, space complexity | → Tip: Expand with comparison to DFS",
  "matched_terms": ["BFS", "queue", "traversal"]
}
```

---

### POST /api/interview/session/{session_id}/submit
**Purpose:** Submit completed interview session  
**File:** main.py → submit_interview_session()  
**Database:** database.save_interview_session()

**Request:**
```json
{
  "finish": true
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "session-123",
  "average_score": 70,
  "submission_time": 1708084200
}
```

**What happens:**
1. Calculates average score from all answers
2. Saves session to interview_sessions table
3. Updates leaderboard ranking
4. Returns results for display

---

## Rating & Feedback Endpoints

### GET /api/ratings/topics
**Purpose:** Get user's topic difficulty/usefulness ratings  
**File:** main.py → get_topic_ratings()  
**Database:** database.get_topic_rating_summary()  
**Auth Required:** Yes

**Response:**
```json
{
  "success": true,
  "ratings": [
    {
      "topic_id": "algorithms",
      "topic_title": "Algorithms",
      "user_rating": 4,
      "total_ratings": 1250,
      "average_rating": 3.8
    },
    {
      "topic_id": "systemdesign",
      "topic_title": "System Design",
      "user_rating": 5,
      "total_ratings": 890,
      "average_rating": 4.2
    }
  ]
}
```

---

### POST /api/ratings/topics
**Purpose:** Rate a topic after interview  
**File:** main.py → save_topic_rating()  
**Database:** database.save_topic_rating()  
**Auth Required:** Yes

**Request:**
```json
{
  "session_id": "session-123",
  "topic_id": "algorithms",
  "rating": 4,
  "user_id": "550e8400-e29b-41d4-a716"
}
```

**Response:**
```json
{
  "success": true
}
```

---

## Leaderboard Endpoints

### GET /api/leaderboards
**Purpose:** Get user rankings by score  
**File:** main.py → get_leaderboards()  
**Database:** database.get_score_leaderboard()

**Query Parameters:**
- `role_id` (optional) - Filter by role
- `limit` (optional, default: 50) - Top N users

**Request:**
```
GET /api/leaderboards?role_id=senior_backend&limit=50
```

**Response:**
```json
{
  "success": true,
  "leaderboard": [
    {
      "rank": 1,
      "user_id": "user-111",
      "username": "alex_pro",
      "avg_score": 85,
      "interview_count": 12,
      "last_interview": "2024-02-20T10:00:00Z"
    },
    {
      "rank": 2,
      "user_id": "user-222",
      "username": "sarah_expert",
      "avg_score": 82,
      "interview_count": 15,
      "last_interview": "2024-02-19T15:30:00Z"
    }
  ]
}
```

---

## Study Plans (Prep Paths) Endpoints

### POST /api/study-plans
**Purpose:** Create new study plan for a role  
**File:** main.py → create_study_plan_endpoint()  
**Database:** database.create_study_plan()  
**Auth Required:** Yes

**Request:**
```json
{
  "role_id": "senior_backend",
  "target_days": 40
}
```

**Response:**
```json
{
  "success": true,
  "plan_id": "plan-550e8400",
  "role_id": "senior_backend",
  "created_at": 1708084200
}
```

**What happens:**
1. Fetches role's topic curriculum from interview_catalog.py
2. Creates study_plans record
3. Creates step for each topic
4. Returns plan structure

---

### GET /api/study-plans
**Purpose:** List user's study plans with progress  
**File:** main.py → list_study_plans_endpoint()  
**Database:** database.list_study_plans()  
**Auth Required:** Yes

**Response:**
```json
{
  "success": true,
  "plans": [
    {
      "plan_id": "plan-123",
      "role_id": "senior_backend",
      "role_title": "Senior Backend Engineer",
      "total_steps": 5,
      "completed_steps": 2,
      "progress_percent": 40
    }
  ]
}
```

---

### GET /api/study-plans/{plan_id}
**Purpose:** Get study plan details with all steps  
**File:** main.py → get_study_plan_endpoint()  
**Database:** database.get_study_plan()

**Response:**
```json
{
  "success": true,
  "plan": {
    "plan_id": "plan-123",
    "user_id": "user-123",
    "role_id": "senior_backend",
    "created_at": "2024-02-01T00:00:00Z",
    "steps": [
      {
        "step_id": "step-1",
        "topic_id": "datastructures",
        "topic_title": "Data Structures",
        "step_order": 1,
        "status": "completed",
        "completed_at": "2024-02-05T10:00:00Z"
      },
      {
        "step_id": "step-2",
        "topic_id": "algorithms",
        "topic_title": "Algorithms",
        "step_order": 2,
        "status": "in_progress",
        "completed_at": null
      },
      {
        "step_id": "step-3",
        "topic_id": "systemdesign",
        "topic_title": "System Design",
        "step_order": 3,
        "status": "pending",
        "completed_at": null
      }
    ]
  }
}
```

---

### GET /api/study-plans/{plan_id}/step/{step_id}
**Purpose:** Get quiz/interview for a study plan step  
**File:** main.py → get_plan_step_session()  
**Database:** database.get_study_plan_step_session_plan()

**Response:**
```json
{
  "success": true,
  "session_plan": {
    "step_id": "step-1",
    "topic_id": "datastructures",
    "topic_title": "Data Structures",
    "questions": [
      {
        "question_id": "ds_array_101",
        "question_text": "What is a dynamic array?",
        "difficulty": "easy"
      }
    ],
    "required_score_percent": 70,
    "estimated_minutes": 20
  }
}
```

---

### PUT /api/study-plans/{plan_id}/step/{step_id}
**Purpose:** Mark study plan step as completed  
**File:** main.py → update_study_plan_step()  
**Database:** database.update_study_plan_step_status()

**Request:**
```json
{
  "status": "completed"
}
```

**Response:**
```json
{
  "success": true
}
```

**Validation:**
- Only allowed if user's quiz score ≥ required_score_percent (usually 70%)

---

## HTML Page Routes (Server-Rendered)

### GET /
**Returns:** index.html - Home/dashboard page

### GET /interview
**Returns:** interview.html - Interview conduct page

### GET /results
**Returns:** results.html - Results & feedback page

### GET /leaderboards
**Returns:** leaderboards.html - User rankings page

### GET /profile
**Returns:** profile.html - User profile & history

### GET /prep-paths
**Returns:** prep_paths.html - Study plan builder

### GET /admin
**Returns:** admin.html - Admin dashboard  
**Auth Required:** Admin user only

### GET /custom-interviews
**Returns:** custom_interviews.html - Custom interview builder

### GET /tracks
**Returns:** tracks.html - Topic tracks page

### GET /roles
**Returns:** roles.html - Available roles page

### GET /auth
**Returns:** auth.html - Login/signup page

---

## Admin Endpoints

### GET /api/admin/dashboard
**Purpose:** Get admin dashboard snapshot  
**File:** main.py → get_admin_dashboard()  
**Database:** database.get_admin_dashboard_snapshot()  
**Auth Required:** Admin only

**Response:**
```json
{
  "success": true,
  "dashboard": {
    "total_users": 1250,
    "total_interviews": 5680,
    "average_score": 72,
    "trending_topics": [
      {"topic": "Algorithms", "interview_count": 450},
      {"topic": "System Design", "interview_count": 380}
    ]
  }
}
```

---

### POST /api/admin/topics
**Purpose:** Create/update interview topic  
**File:** main.py → create_admin_topic()  
**Database:** database.save_topic_record()  
**Auth Required:** Admin only

**Request:**
```json
{
  "topic_id": "algorithms",
  "category": "coding",
  "title": "Algorithms",
  "subtitle": "Patterns and techniques",
  "description": "Sorting, searching, dynamic programming",
  "level_label": "Intermediate",
  "accent": "#FF5733"
}
```

**Response:**
```json
{
  "success": true,
  "topic_id": "algorithms"
}
```

---

### POST /api/admin/questions
**Purpose:** Create/update interview question  
**File:** main.py → create_admin_question()  
**Database:** database.save_question_record()  
**Auth Required:** Admin only

**Request:**
```json
{
  "question_id": "algo_bfs_101",
  "topic_id": "algorithms",
  "question_text": "Explain breadth-first search algorithm",
  "difficulty": "medium",
  "sample_answer": "BFS uses a queue to traverse...",
  "ideal_answer": "BFS explores level-by-level..."
}
```

**Response:**
```json
{
  "success": true,
  "question_id": "algo_bfs_101"
}
```

---

### POST /api/admin/roles
**Purpose:** Create/update role definition  
**File:** main.py → create_admin_role()  
**Database:** database.save_role_record()  
**Auth Required:** Admin only

**Request:**
```json
{
  "role_id": "senior_backend",
  "title": "Senior Backend Engineer",
  "subtitle": "Expert backend development",
  "description": "...",
  "level_label": "Advanced",
  "default_duration": 30,
  "topic_weights": {
    "algorithms": 2,
    "systemdesign": 3,
    "backend": 3,
    "database": 2
  }
}
```

**Response:**
```json
{
  "success": true,
  "role_id": "senior_backend"
}
```

---

## Status Codes

```
200 OK                  - Request successful
400 Bad Request         - Invalid request format
401 Unauthorized        - Authentication required
403 Forbidden           - User not authorized
404 Not Found           - Resource doesn't exist
422 Unprocessable       - Validation error
500 Internal Server     - Backend error
```

---

## Authentication Pattern

All protected endpoints require:
```
Header: Authorization: Bearer <jwt_token>
```

The token is validated by:
```python
# In main.py
request_user = get_authenticated_user_payload(authorization)

# In auth.py
token = extract_bearer_token(authorization_header)  # "Bearer xyz" → "xyz"
user = verify_auth_token(token)  # Validate signature & expiration
```

If token is invalid/expired:
```json
{
  "success": false,
  "error": "Authentication required"
}
```

---

## Common Patterns

### Success Response
```json
{
  "success": true,
  "data": {...}
}
```

### Error Response
```json
{
  "success": false,
  "error": "Human-readable error message",
  "detail": "Optional technical details"
}
```

### Pagination (where applicable)
```json
{
  "success": true,
  "results": [...],
  "total": 100,
  "page": 1,
  "per_page": 50
}
```

