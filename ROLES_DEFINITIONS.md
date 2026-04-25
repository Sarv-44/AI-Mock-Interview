# Role Definitions - AI Mock Interview Platform

## Table of Contents
1. [Development Team Roles](#development-team-roles)
2. [System User Roles](#system-user-roles)
3. [Interview Job Roles](#interview-job-roles)

---

## Development Team Roles

### Backend Developer
**Primary Responsibility:** Build and maintain the FastAPI-based interview platform backend, ensure data persistence, and orchestrate business logic.

#### Key Responsibilities:
- **API Development:** Create and maintain RESTful endpoints for authentication, interview management, scoring, and leaderboards
- **Database Management:** Design and maintain MySQL schema, implement CRUD operations, manage database migrations and initialization
- **Business Logic:** Implement interview transcript scoring, feedback generation, PDF report generation, and study plan algorithms
- **Audio Processing:** Integrate Whisper transcription, manage audio file uploads, and ensure transcript quality
- **Authentication & Security:** Manage JWT tokens, password hashing, user authentication, and admin access control
- **Data Persistence:** Handle user profiles, interview histories, custom interview templates, study materials, and analytics
- **Performance & Reliability:** Optimize queries, ensure database indexing, handle edge cases, and maintain system uptime
- **API Documentation:** Maintain endpoint references and developer documentation
- **Testing & Debugging:** Write and maintain test suites, debug production issues, and verify system behavior

#### Technical Stack:
- **Framework:** FastAPI (Python)
- **Database:** MySQL with mysql-connector-python
- **Authentication:** JWT tokens with bcrypt for password hashing
- **Audio:** OpenAI Whisper (local transcription)
- **PDF Generation:** ReportLab
- **Server:** Uvicorn

#### Key Files & Modules:
- `backend/main.py` - FastAPI app, HTTP routes, orchestration
- `backend/database.py` - MySQL queries, CRUD operations, schema management
- `backend/auth.py` - JWT token generation, password verification, bearer token parsing
- `backend/analytics.py` - Transcript scoring, keyword extraction, feedback heuristics
- `backend/interview_catalog.py` - Question bank, topic definitions, role catalog
- `backend/pdf_generator.py` - Report generation using ReportLab

#### Daily Workflows:
- Writing and testing API endpoints
- Debugging database queries and optimizing performance
- Managing user authentication and authorization
- Processing interview data and generating analytics
- Handling uploaded audio files and transcription
- Maintaining data integrity and schema consistency
- Coordinating with frontend developers on API contracts

---

### Frontend Developer
**Primary Responsibility:** Build and maintain the server-rendered HTML/CSS/JavaScript frontend for the interview platform.

#### Key Responsibilities:
- **UI Implementation:** Create HTML templates using Jinja2 for rendering on backend
- **Styling:** Maintain CSS for responsive design, theming, and dark editorial UI system
- **Client-Side Logic:** Write JavaScript for interview interactions, audio recording, results display, and user navigation
- **Form Handling:** Implement form validation, data binding, and submission to backend APIs
- **Audio Recording:** Integrate browser audio recording APIs and manage file uploads
- **Session Management:** Handle user authentication state and session management on client
- **Performance:** Optimize page load times, minimize CSS/JS, and ensure smooth user interactions
- **Accessibility:** Ensure proper semantic HTML and keyboard navigation

#### Key Files:
- `templates/` - HTML pages (index, auth, interview, results, leaderboards, etc.)
- `static/css/` - Stylesheets for all pages
- `static/js/` - Client-side JavaScript (main.js, recording.js, results.js, etc.)

---

### DevOps / Infrastructure Engineer
**Primary Responsibility:** Deploy, monitor, and maintain the production environment and development infrastructure.

#### Key Responsibilities:
- **Deployment:** Set up and manage FastAPI application deployment using Uvicorn or similar
- **Database Setup:** Configure MySQL, manage backups, handle schema migrations
- **Environment Management:** Manage .env configuration, secrets, and environment variables across dev/staging/production
- **Monitoring & Logging:** Set up logging, monitoring, and alerting for system health
- **Security:** Manage SSL/TLS certificates, handle security patches, ensure secure database connections
- **Scaling:** Plan for horizontal scaling, caching layers, and load balancing as user base grows
- **CI/CD:** Set up automated testing and deployment pipelines

#### Key Considerations:
- Python/FastAPI application server configuration
- MySQL database backup and recovery procedures
- File management for uploaded audio files in `temp/` directory
- Model management for Whisper AI (primary + fallback models loaded at startup)
- Static file serving for CSS/JS/images

---

### QA / Test Engineer
**Primary Responsibility:** Ensure quality and reliability of the interview platform through comprehensive testing.

#### Key Responsibilities:
- **Test Plan Development:** Create test scenarios covering all features
- **API Testing:** Test all endpoints for correct responses, error handling, and edge cases
- **Integration Testing:** Test database operations, authentication flows, and end-to-end interview workflows
- **Audio Testing:** Verify transcript quality, Whisper transcription accuracy
- **Functionality Testing:** Test interview creation, scoring, leaderboards, custom interviews, and PDF generation
- **Performance Testing:** Load testing, stress testing, and performance benchmarking
- **Regression Testing:** Ensure new changes don't break existing functionality

#### Key Test Areas:
- Authentication (signup, login, JWT tokens)
- Interview creation and question delivery
- Audio recording and transcript processing
- Score calculation and analytics
- PDF report generation
- Leaderboard rankings
- Custom interview templates
- Study plan management

---

### Product Manager
**Primary Responsibility:** Define features, gather requirements, and ensure alignment with user needs.

#### Key Responsibilities:
- **Feature Design:** Define new interview roles, topics, and study features
- **User Research:** Gather feedback from users on interview quality and experience
- **Roadmap Planning:** Plan short-term and long-term feature releases
- **Success Metrics:** Define KPIs for engagement, learning outcomes, and platform adoption
- **Stakeholder Communication:** Communicate progress, blockers, and priorities to team and leadership

#### Focus Areas:
- Interview quality and question bank curation
- Role definitions and topic coverage
- User experience and onboarding flows
- Leaderboard and scoring mechanics
- Study plan effectiveness
- Admin features for catalog management

---

## System User Roles

### Regular User / Candidate
**Definition:** Individuals using the platform to practice for interviews.

#### Permissions:
- ✅ Create account and authenticate
- ✅ Take topic-based interviews
- ✅ Take role-based interviews
- ✅ Create custom interview templates
- ✅ Upload audio and receive transcripts
- ✅ View interview results and scores
- ✅ See personalized score leaderboards
- ✅ View study materials and prep paths
- ✅ Download PDF reports of interviews
- ✅ Track profile history and activity
- ❌ Modify catalog (topics, questions, roles)
- ❌ Access admin panel

#### Database Fields:
- `user_id` - Unique identifier
- `username` - Public display name
- `email` - Login credential
- `is_admin` - Boolean flag (False for regular users)
- `password_salt` and `password_hash` - Authentication
- `created_at`, `updated_at` - Timestamps

#### Associated Data:
- Interview sessions and scores
- Custom interview templates
- Topic ratings
- Study plans / prep paths
- Activity history
- Profile preferences

---

### Admin User
**Definition:** Platform administrators with elevated privileges for catalog and user management.

#### Permissions (all Regular User permissions plus):
- ✅ Access admin panel (`/admin`)
- ✅ View all users and their statistics
- ✅ View system health and analytics dashboard
- ✅ Manage topic catalog (add/edit topics)
- ✅ Manage question bank
- ✅ Manage interview roles and role configurations
- ✅ Moderate and review interviews
- ✅ Manage study materials
- ✅ Manage system announcements
- ✅ Generate reports across all users
- ✅ Audit user activity

#### Database Fields:
- Same as Regular User, but `is_admin` = True

#### Admin Features:
- Catalog management interface
- User statistics and analytics
- System health dashboard
- Question bank updates
- Role configuration updates

---

## Interview Job Roles

These are the **target interview scenarios** users practice for, not development team roles. Each role represents a realistic hiring loop with weighted question distribution.

### 1. Frontend Engineer
**Target Level:** Intern to Mid-level  
**Interview Duration:** 15, 30, or 60 minutes (default: 30)

**Focus Areas & Weights:**
- **JavaScript** (28%) - Language fundamentals, DOM, async/await, closures
- **React** (28%) - Component lifecycles, hooks, state management, performance
- **APIs** (10%) - REST design, CORS, fetch/axios, error handling
- **Testing** (10%) - Unit testing, component testing, mocking
- **System Design** (8%) - UI architecture, state flow, scalability
- **Security** (6%) - XSS, CSRF, secure API communication
- **Behavioral** (10%) - Teamwork, communication, problem-solving process

**Interview Modes:**
- Topic-based: Deep dive into single topics
- Role-based: Mixed questions across all focus areas
- Custom: User-defined questions

---

### 2. Backend Engineer
**Target Level:** Intern to Mid-level  
**Interview Duration:** 15, 30, or 60 minutes (default: 30)

**Focus Areas & Weights:**
- **Databases** (18%) - SQL, indexing, schema design, replication
- **APIs** (16%) - REST design, HTTP, versioning, rate limiting
- **System Design** (16%) - Scalability, caching, load balancing, architecture
- **Node.js** (12%) - Runtime concepts, async, event loop, npm ecosystem
- **Operating Systems** (10%) - Processes, threads, memory, scheduling
- **Networking** (8%) - TCP/IP, DNS, SSL/TLS, protocols
- **Security** (8%) - Authentication, authorization, data protection
- **Testing** (8%) - Unit tests, integration tests, CI/CD
- **Behavioral** (4%) - Communication and teamwork

**Key Concepts Covered:**
- RESTful API design and best practices
- Database normalization and query optimization
- Caching strategies (Redis, CDN)
- Microservices architecture
- Load balancing and horizontal scaling
- Data consistency and transactions
- Error handling and logging

---

### 3. Full Stack Engineer
**Target Level:** Intern to Mid-level  
**Interview Duration:** 15, 30, or 60 minutes (default: 30)

**Focus Areas & Weights:**
- **JavaScript** (16%) - Core language features
- **React** (16%) - Component architecture, state management
- **Node.js** (14%) - Backend runtime, async patterns
- **APIs** (12%) - Design and integration between frontend/backend
- **Databases** (12%) - Schema design, queries, persistence
- **System Design** (10%) - Full-stack architecture, scalability
- **Testing** (8%) - Unit, integration, and end-to-end testing
- **Security** (6%) - Frontend and backend security
- **Behavioral** (6%) - SDLC, communication, tradeoff analysis

**Interview Focus:**
- End-to-end feature implementation
- Frontend-to-backend data flow
- Database to UI interaction
- Performance considerations across stack
- Deployment and DevOps basics

---

### 4. DevOps Engineer
**Target Level:** Junior to Mid-level  
**Interview Duration:** 15, 30, or 60 minutes (default: 30)

**Focus Areas & Weights:**
- **DevOps Tools & CI/CD** (24%) - Jenkins, GitHub Actions, GitLab CI, Docker
- **Cloud Platforms** (20%) - AWS, Azure, GCP, infrastructure
- **Networking** (14%) - VPCs, DNS, load balancing, security groups
- **Security** (14%) - Secrets management, encryption, compliance, auditing
- **System Design** (10%) - Architecture for distributed systems, reliability
- **Testing** (8%) - Automated testing, deployment validation
- **Operating Systems** (6%) - Linux, process management, shell scripting
- **Behavioral** (4%) - Incident response, collaboration with engineering teams

**Key Topics:**
- Containerization (Docker) and orchestration (Kubernetes)
- Infrastructure as Code (Terraform, CloudFormation, Bicep)
- CI/CD pipeline design and implementation
- Monitoring and logging solutions
- Database backups and disaster recovery
- Security hardening and compliance
- Performance tuning and optimization

---

### 5. AI / ML Engineer
**Target Level:** Junior to Mid-level  
**Interview Duration:** 15, 30, or 60 minutes (default: 30)

**Focus Areas & Weights:**
- **Machine Learning Fundamentals** (24%) - Algorithms, model types, training/evaluation
- **Generative AI / LLMs** (22%) - Transformers, prompting, fine-tuning, RAG
- **Python** (18%) - Data structures, NumPy, Pandas, scikit-learn
- **System Design** (10%) - Model serving, batch/real-time inference, scalability
- **Cloud Platforms** (8%) - ML platforms, GPU management, model deployment
- **Databases** (6%) - Data pipelines, feature stores, time-series data
- **APIs** (6%) - Model serving APIs, ML platform integration
- **Behavioral** (6%) - Product sense, A/B testing, experimentation mindset

**Key Concepts:**
- Supervised and unsupervised learning
- Neural networks and deep learning
- LLMs and prompt engineering
- Model evaluation and metrics
- Data preprocessing and feature engineering
- Model deployment and monitoring
- Ethical AI and bias mitigation

---

### 6. SDE Intern
**Target Level:** Intern / Fresher  
**Interview Duration:** 15, 30, or 60 minutes (default: 30)

**Focus Areas & Weights:**
- **Data Structures** (18%) - Arrays, linked lists, trees, heaps, hash maps
- **Operating Systems** (10%) - Processes, threads, memory, concurrency
- **Databases** (12%) - SQL basics, schema design, queries
- **APIs** (8%) - REST concepts, HTTP methods, JSON/XML
- **Testing** (8%) - Basic testing concepts, debugging
- **Graphs** (10%) - Traversal, shortest paths, connectivity
- **Sorting Algorithms** (10%) - Algorithm selection, complexity analysis
- **Dynamic Programming** (8%) - State and transitions
- **Behavioral** (16%) - Communication, learning ability, enthusiasm

**Interview Focus:**
- Clear communication of problem-solving approach
- Understanding of fundamentals over complex optimization
- Ability to discuss tradeoffs
- Learning mindset and asking clarifying questions
- Clean code and naming conventions

---

## Role Mapping in Code

### Database Table
The `job_roles` table stores role definitions with:
- `role_id` - Unique identifier (e.g., "backend_engineer")
- `title` - Display name
- `subtitle` - Short description
- `description` - Full description
- `level_label` - Target seniority level
- `default_duration` - Interview minutes
- `available_durations` - JSON list of options [15, 30, 60]
- `topic_weights` - JSON object mapping topics to percentage weights

### API Integration
- **Get all roles:** `GET /api/roles/` - Returns `job_roles` catalog
- **Get role details:** `GET /api/roles/{role_id}` - Returns single role configuration
- **Create role interview:** `POST /api/interviews/start` - Accepts `role_id` parameter
- **View role leaderboard:** `GET /api/leaderboards/{role_id}` - Ranks users by role performance

---

## Summary Matrix

| Role Type | Level | Scope | Purpose |
|-----------|-------|-------|---------|
| **Backend Developer** (Dev Team) | Senior | Backend APIs, DB, Auth | Build platform |
| **Frontend Developer** (Dev Team) | Senior | HTML, CSS, JS | Build UI |
| **DevOps Engineer** (Dev Team) | Senior | Infra, Deployment | Deploy & operate |
| **QA Engineer** (Dev Team) | Mid+ | Testing, Quality | Ensure reliability |
| **Product Manager** (Dev Team) | Senior | Strategy, Features | Drive product |
| **Regular User** (System) | N/A | Public features | Practice interviews |
| **Admin User** (System) | N/A | Catalog, Analytics | Manage platform |
| **Frontend Engineer** (Interview) | Intern+ | React, JS, CSS | Practice frontend |
| **Backend Engineer** (Interview) | Intern+ | APIs, DB, Systems | Practice backend |
| **Full Stack Engineer** (Interview) | Intern+ | Full stack integration | Practice full stack |
| **DevOps Engineer** (Interview) | Junior+ | CI/CD, Infrastructure | Practice DevOps |
| **AI/ML Engineer** (Interview) | Junior+ | ML, LLMs, Python | Practice AI/ML |
| **SDE Intern** (Interview) | Fresher | Core CS, Fundamentals | Practice basics |

---

## Key Interactions

1. **Backend Developer** builds APIs that serve **Candidates (Regular Users)**
2. **Frontend Developer** creates UI that calls Backend APIs
3. **DevOps Engineer** deploys the system for all users
4. **QA Engineer** ensures **Candidates** get quality interview experiences
5. **Product Manager** defines content for interview roles
6. **Admin Users** manage the catalog using admin panel
7. **Candidates** practice for one of six **Interview Job Roles**
8. **Interview engines** score transcripts and provide feedback based on role-specific rubrics
