import re
from pathlib import Path

from backend.analytics import detect_question_type, extract_answer_subject, extract_comparison_subjects

QUESTION_BANK_PATH = Path(__file__).resolve().parent.parent / "static" / "js" / "questions.js"

TOPIC_CATALOG = [
    {
        "topic_id": "graphs",
        "category": "Algorithms",
        "title": "Graph Algorithms",
        "subtitle": "Traversal, shortest paths, and graph reasoning",
        "description": "Practice core graph interview questions spanning traversal, shortest path, connectivity, and graph optimization.",
        "level_label": "Intermediate to Advanced",
        "accent": "graphs",
    },
    {
        "topic_id": "datastructures",
        "category": "Core CS",
        "title": "Data Structures",
        "subtitle": "Trees, heaps, maps, queues, and caches",
        "description": "Sharpen the explanations interviewers expect around common data structures and practical tradeoffs.",
        "level_label": "Beginner to Advanced",
        "accent": "datastructures",
    },
    {
        "topic_id": "sorting",
        "category": "Algorithms",
        "title": "Sorting Algorithms",
        "subtitle": "Complexity, stability, and strategy selection",
        "description": "Build stronger answers about sorting internals, performance tradeoffs, and real-world use cases.",
        "level_label": "Intermediate",
        "accent": "sorting",
    },
    {
        "topic_id": "dp",
        "category": "Problem Solving",
        "title": "Dynamic Programming",
        "subtitle": "Memoization, states, and transitions",
        "description": "Train how to recognize dynamic programming patterns and explain them under interview pressure.",
        "level_label": "Intermediate to Advanced",
        "accent": "dp",
    },
    {
        "topic_id": "database",
        "category": "Backend",
        "title": "Databases",
        "subtitle": "SQL, indexing, replication, and schema design",
        "description": "Practice questions on storage systems, query optimization, transactions, and data modeling.",
        "level_label": "Intermediate",
        "accent": "database",
    },
    {
        "topic_id": "systemdesign",
        "category": "Architecture",
        "title": "System Design",
        "subtitle": "Scalability, APIs, queues, and caching",
        "description": "Prepare for senior interview rounds with system design prompts covering availability, scale, and tradeoffs.",
        "level_label": "Advanced",
        "accent": "systemdesign",
    },
    {
        "topic_id": "behavioral",
        "category": "Leadership",
        "title": "Behavioral",
        "subtitle": "Leadership, ownership, and teamwork",
        "description": "Practice structured storytelling for behavioral questions using outcomes, reflection, and impact.",
        "level_label": "All levels",
        "accent": "behavioral",
    },
    {
        "topic_id": "python",
        "category": "Language",
        "title": "Python Fundamentals",
        "subtitle": "Language behavior, memory, and idioms",
        "description": "Strengthen your explanations of Python features, runtime behavior, and engineering best practices.",
        "level_label": "Beginner to Advanced",
        "accent": "python",
    },
    {
        "topic_id": "os",
        "category": "Systems",
        "title": "OS and Concurrency",
        "subtitle": "Processes, threads, memory, and scheduling",
        "description": "Drill into the operating systems concepts that repeatedly show up in systems interviews.",
        "level_label": "Intermediate to Advanced",
        "accent": "os",
    },
    {
        "topic_id": "java",
        "category": "Language",
        "title": "Java",
        "subtitle": "JVM, collections, memory, and idioms",
        "description": "Practice the Java concepts most often discussed in backend and enterprise interview loops.",
        "level_label": "Beginner to Advanced",
        "accent": "java",
    },
    {
        "topic_id": "javascript",
        "category": "Frontend",
        "title": "JavaScript",
        "subtitle": "Closures, async flow, and browser fundamentals",
        "description": "Improve your explanations of the event loop, scope, memory, and real-world JavaScript behavior.",
        "level_label": "Beginner to Advanced",
        "accent": "javascript",
    },
    {
        "topic_id": "react",
        "category": "Frontend",
        "title": "React",
        "subtitle": "State, rendering, hooks, and architecture",
        "description": "Prepare for modern frontend interviews with a focused React practice track.",
        "level_label": "Intermediate",
        "accent": "react",
    },
    {
        "topic_id": "nodejs",
        "category": "Backend",
        "title": "Node.js",
        "subtitle": "Event loop, streams, and production APIs",
        "description": "Work through Node.js questions around concurrency, performance, and server design.",
        "level_label": "Intermediate",
        "accent": "nodejs",
    },
    {
        "topic_id": "machinelearning",
        "category": "AI/ML",
        "title": "Machine Learning",
        "subtitle": "Models, evaluation, and production tradeoffs",
        "description": "Practice explaining learning workflows, model performance, and deployment risks clearly.",
        "level_label": "Intermediate to Advanced",
        "accent": "machinelearning",
    },
    {
        "topic_id": "genai",
        "category": "AI/ML",
        "title": "Generative AI",
        "subtitle": "LLMs, RAG, prompting, and evaluation",
        "description": "Train for modern AI interviews with questions on LLM products, retrieval, safety, and cost tradeoffs.",
        "level_label": "Intermediate to Advanced",
        "accent": "genai",
    },
    {
        "topic_id": "cloud",
        "category": "Cloud",
        "title": "Cloud Architecture",
        "subtitle": "Scalability, resilience, and cloud operations",
        "description": "Practice the cloud concepts that show up in backend, platform, and infrastructure interviews.",
        "level_label": "Intermediate to Advanced",
        "accent": "cloud",
    },
    {
        "topic_id": "networking",
        "category": "Systems",
        "title": "Networking",
        "subtitle": "TCP/IP, DNS, TLS, and latency",
        "description": "Strengthen your ability to explain the network behavior behind distributed applications.",
        "level_label": "Intermediate",
        "accent": "networking",
    },
    {
        "topic_id": "security",
        "category": "Security",
        "title": "Application Security",
        "subtitle": "Auth, secrets, browser risk, and defense in depth",
        "description": "Build sharper answers on practical security topics that matter in engineering interviews.",
        "level_label": "Intermediate to Advanced",
        "accent": "security",
    },
    {
        "topic_id": "testing",
        "category": "Engineering",
        "title": "Testing Strategies",
        "subtitle": "Unit, integration, end-to-end, and reliability",
        "description": "Practice how to talk about software quality, confidence, and high-value test design.",
        "level_label": "Intermediate",
        "accent": "testing",
    },
    {
        "topic_id": "devops",
        "category": "Platform",
        "title": "DevOps",
        "subtitle": "CI/CD, observability, deployments, and operations",
        "description": "Prepare for platform and delivery questions around release safety, reliability, and scale.",
        "level_label": "Intermediate to Advanced",
        "accent": "devops",
    },
    {
        "topic_id": "apis",
        "category": "Backend",
        "title": "API Design",
        "subtitle": "Contracts, versioning, pagination, and resilience",
        "description": "Practice modern API interview questions spanning REST, GraphQL, idempotency, and reliability.",
        "level_label": "Intermediate",
        "accent": "apis",
    },
]

ROLE_CATALOG = [
    {
        "role_id": "frontend_engineer",
        "title": "Frontend Engineer",
        "subtitle": "JavaScript, React, browser behavior, and UI problem solving",
        "description": "A role-based interview focused on frontend architecture, component reasoning, browser behavior, and practical UI tradeoffs.",
        "level_label": "Intern to Mid-level",
        "default_duration": 30,
        "available_durations": [15, 30, 60],
        "topic_weights": {
            "javascript": 28,
            "react": 28,
            "apis": 10,
            "testing": 10,
            "systemdesign": 8,
            "security": 6,
            "behavioral": 10,
        },
    },
    {
        "role_id": "backend_engineer",
        "title": "Backend Engineer",
        "subtitle": "APIs, databases, systems, scaling, and runtime fundamentals",
        "description": "A realistic backend loop spanning API design, persistence, system design, reliability, and foundational systems concepts.",
        "level_label": "Intern to Mid-level",
        "default_duration": 30,
        "available_durations": [15, 30, 60],
        "topic_weights": {
            "database": 18,
            "apis": 16,
            "systemdesign": 16,
            "nodejs": 12,
            "os": 10,
            "networking": 8,
            "security": 8,
            "testing": 8,
            "behavioral": 4,
        },
    },
    {
        "role_id": "fullstack_engineer",
        "title": "Full Stack Engineer",
        "subtitle": "Frontend plus backend breadth with delivery and tradeoff reasoning",
        "description": "A mixed interview lane that checks how well you connect UI, APIs, persistence, and system-level tradeoffs.",
        "level_label": "Intern to Mid-level",
        "default_duration": 30,
        "available_durations": [15, 30, 60],
        "topic_weights": {
            "javascript": 16,
            "react": 16,
            "nodejs": 14,
            "apis": 12,
            "database": 12,
            "systemdesign": 10,
            "testing": 8,
            "security": 6,
            "behavioral": 6,
        },
    },
    {
        "role_id": "devops_engineer",
        "title": "DevOps Engineer",
        "subtitle": "CI/CD, observability, cloud, networking, and secure delivery",
        "description": "A role-wise round centered on operations, platform thinking, reliability, and production incident judgment.",
        "level_label": "Junior to Mid-level",
        "default_duration": 30,
        "available_durations": [15, 30, 60],
        "topic_weights": {
            "devops": 24,
            "cloud": 20,
            "networking": 14,
            "security": 14,
            "systemdesign": 10,
            "testing": 8,
            "os": 6,
            "behavioral": 4,
        },
    },
    {
        "role_id": "ai_ml_engineer",
        "title": "AI / ML Engineer",
        "subtitle": "ML fundamentals, GenAI, Python, evaluation, and product tradeoffs",
        "description": "A modern AI interview flow covering machine learning, generative AI systems, evaluation, and production reasoning.",
        "level_label": "Junior to Mid-level",
        "default_duration": 30,
        "available_durations": [15, 30, 60],
        "topic_weights": {
            "machinelearning": 24,
            "genai": 22,
            "python": 18,
            "systemdesign": 10,
            "cloud": 8,
            "database": 6,
            "apis": 6,
            "behavioral": 6,
        },
    },
    {
        "role_id": "sde_intern",
        "title": "SDE Intern",
        "subtitle": "Core CS, coding fundamentals, communication, and interview basics",
        "description": "A balanced early-career interview that checks clarity on data structures, algorithms, OS, databases, and communication.",
        "level_label": "Intern / Fresher",
        "default_duration": 30,
        "available_durations": [15, 30, 60],
        "topic_weights": {
            "datastructures": 18,
            "sorting": 10,
            "graphs": 10,
            "dp": 8,
            "os": 10,
            "database": 12,
            "apis": 8,
            "testing": 8,
            "behavioral": 16,
        },
    },
]

ADDITIONAL_TOPIC_SPECS = [
    {
        "topic_id": "algorithms",
        "category": "Algorithms",
        "title": "Algorithmic Thinking",
        "subtitle": "Problem decomposition, complexity, and choosing the right approach",
        "description": "Build stronger interview reasoning around breaking down problems, selecting strategies, and defending complexity tradeoffs.",
        "level_label": "Beginner to Advanced",
        "accent": "algorithms",
        "family": "core_cs",
        "compare_with": "a brute-force or ad hoc approach",
        "scenario": "an interview problem with tight time and memory limits",
        "signals": ["problem decomposition", "complexity tradeoffs", "correctness"],
    },
    {
        "topic_id": "recursion",
        "category": "Algorithms",
        "title": "Recursion and Backtracking",
        "subtitle": "Recursive thinking, state cleanup, and search spaces",
        "description": "Practice explaining recursive problem solving, backtracking patterns, and when recursion becomes risky in production code.",
        "level_label": "Intermediate",
        "accent": "recursion",
        "family": "core_cs",
        "compare_with": "an iterative or queue-based solution",
        "scenario": "a combinatorial search problem with many branches",
        "signals": ["base case", "call stack", "state cleanup"],
    },
    {
        "topic_id": "strings",
        "category": "Algorithms",
        "title": "String Algorithms",
        "subtitle": "Pattern matching, parsing, and substring reasoning",
        "description": "Cover common interview work on parsing, pattern search, tokenization, and efficient string manipulation.",
        "level_label": "Beginner to Advanced",
        "accent": "strings",
        "family": "core_cs",
        "compare_with": "naive character-by-character processing",
        "scenario": "a search, parsing, or log-processing feature",
        "signals": ["pattern matching", "memory use", "edge cases"],
    },
    {
        "topic_id": "sql",
        "category": "Backend",
        "title": "SQL",
        "subtitle": "Query writing, joins, grouping, and performance basics",
        "description": "Strengthen the SQL interview layer that sits between schema design and production query performance.",
        "level_label": "Beginner to Advanced",
        "accent": "sql",
        "family": "data",
        "compare_with": "an ORM-only or document-query approach",
        "scenario": "an analytics-heavy product with reporting and transactional queries",
        "signals": ["joins", "filtering", "query plans"],
    },
    {
        "topic_id": "mongodb",
        "category": "Backend",
        "title": "MongoDB",
        "subtitle": "Document modeling, indexing, and schema flexibility",
        "description": "Practice when document databases fit better than relational models, and how to keep them fast and maintainable.",
        "level_label": "Intermediate",
        "accent": "mongodb",
        "family": "data",
        "compare_with": "a relational database like PostgreSQL",
        "scenario": "a product with evolving schemas and nested data",
        "signals": ["document modeling", "indexing", "schema tradeoffs"],
    },
    {
        "topic_id": "redis",
        "category": "Backend",
        "title": "Redis",
        "subtitle": "In-memory data, caching, and real-time primitives",
        "description": "Train around how Redis helps with low-latency reads, counters, queues, locks, and short-lived state.",
        "level_label": "Intermediate",
        "accent": "redis",
        "family": "backend",
        "compare_with": "a primary database or a simpler cache like Memcached",
        "scenario": "a session-heavy or real-time backend API",
        "signals": ["latency", "memory growth", "eviction strategy"],
    },
    {
        "topic_id": "caching",
        "category": "Architecture",
        "title": "Caching Strategies",
        "subtitle": "Cache design, invalidation, and hit-rate tradeoffs",
        "description": "Focus on cache placement, invalidation, staleness control, and performance bottlenecks in real systems.",
        "level_label": "Intermediate to Advanced",
        "accent": "caching",
        "family": "systems",
        "compare_with": "always going directly to the source of truth",
        "scenario": "a read-heavy product under unpredictable traffic spikes",
        "signals": ["hit rate", "staleness", "cache invalidation"],
    },
    {
        "topic_id": "distributedsystems",
        "category": "Architecture",
        "title": "Distributed Systems",
        "subtitle": "Coordination, consistency, and failure across machines",
        "description": "Prepare for real interview questions around partial failure, replication, coordination, and data movement across services.",
        "level_label": "Advanced",
        "accent": "distributedsystems",
        "family": "systems",
        "compare_with": "a single-node or tightly coupled architecture",
        "scenario": "a globally used system with partial failures and replication delays",
        "signals": ["consistency", "fault tolerance", "coordination"],
    },
    {
        "topic_id": "microservices",
        "category": "Architecture",
        "title": "Microservices",
        "subtitle": "Service boundaries, contracts, and operational tradeoffs",
        "description": "Practice how to talk about splitting systems into services without ignoring data ownership and operational cost.",
        "level_label": "Advanced",
        "accent": "microservices",
        "family": "systems",
        "compare_with": "a modular monolith",
        "scenario": "a growing engineering org trying to split one large application",
        "signals": ["service boundaries", "data ownership", "operational complexity"],
    },
    {
        "topic_id": "docker",
        "category": "Platform",
        "title": "Docker and Containers",
        "subtitle": "Containerization, image hygiene, and runtime isolation",
        "description": "Build practical confidence around container images, build layers, isolation, and production container habits.",
        "level_label": "Intermediate",
        "accent": "docker",
        "family": "platform",
        "compare_with": "running directly on the host machine",
        "scenario": "a multi-service app that must be reproducible across environments",
        "signals": ["image layers", "runtime isolation", "build reproducibility"],
    },
    {
        "topic_id": "kubernetes",
        "category": "Platform",
        "title": "Kubernetes",
        "subtitle": "Workloads, orchestration, scaling, and cluster operations",
        "description": "Prepare for interview questions around container orchestration, deployment safety, and resilient platform operations.",
        "level_label": "Advanced",
        "accent": "kubernetes",
        "family": "platform",
        "compare_with": "manual VM deployment or simpler container orchestration",
        "scenario": "a platform running many services with frequent releases",
        "signals": ["scheduling", "service discovery", "rollout safety"],
    },
    {
        "topic_id": "linux",
        "category": "Systems",
        "title": "Linux Fundamentals",
        "subtitle": "Processes, files, permissions, and debugging in production",
        "description": "Sharpen the practical Linux knowledge interviewers expect for backend, SRE, and platform roles.",
        "level_label": "Beginner to Advanced",
        "accent": "linux",
        "family": "systems",
        "compare_with": "managed abstractions that hide the host system",
        "scenario": "a production incident on a service host",
        "signals": ["process inspection", "permissions", "system debugging"],
    },
    {
        "topic_id": "concurrency",
        "category": "Systems",
        "title": "Concurrency",
        "subtitle": "Synchronization, race conditions, and throughput tradeoffs",
        "description": "Practice the interview layer between OS concepts and real service concurrency bugs.",
        "level_label": "Intermediate to Advanced",
        "accent": "concurrency",
        "family": "systems",
        "compare_with": "purely sequential execution",
        "scenario": "a shared-state service under concurrent load",
        "signals": ["race conditions", "synchronization", "throughput"],
    },
    {
        "topic_id": "lowleveldesign",
        "category": "Architecture",
        "title": "Low-Level Design",
        "subtitle": "Class design, interfaces, and object collaboration",
        "description": "Prepare for interview rounds that ask you to model components, interfaces, entities, and interactions cleanly.",
        "level_label": "Intermediate to Advanced",
        "accent": "lowleveldesign",
        "family": "engineering",
        "compare_with": "high-level architecture discussion without object detail",
        "scenario": "a whiteboard design round for a real product feature",
        "signals": ["responsibility boundaries", "interfaces", "extensibility"],
    },
    {
        "topic_id": "oop",
        "category": "Language",
        "title": "Object-Oriented Programming",
        "subtitle": "Encapsulation, abstraction, and modeling behavior",
        "description": "Build stronger answers around modeling domain behavior with classes, interfaces, and clean boundaries.",
        "level_label": "Beginner to Advanced",
        "accent": "oop",
        "family": "engineering",
        "compare_with": "a procedural or purely data-centric design",
        "scenario": "a domain model that needs clear responsibilities and extension points",
        "signals": ["encapsulation", "abstraction", "polymorphism"],
    },
    {
        "topic_id": "designpatterns",
        "category": "Engineering",
        "title": "Design Patterns",
        "subtitle": "Reusable object interactions and maintainable structure",
        "description": "Practice talking about design patterns in terms of tradeoffs, maintainability, and when not to overuse them.",
        "level_label": "Intermediate",
        "accent": "designpatterns",
        "family": "engineering",
        "compare_with": "ad hoc object relationships without a clear structure",
        "scenario": "a growing codebase that needs extension without constant rewrites",
        "signals": ["coupling", "extensibility", "maintainability"],
    },
    {
        "topic_id": "typescript",
        "category": "Frontend",
        "title": "TypeScript",
        "subtitle": "Type safety, API contracts, and scalable frontend code",
        "description": "Train on how TypeScript changes developer feedback loops, component safety, and refactoring confidence.",
        "level_label": "Intermediate",
        "accent": "typescript",
        "family": "frontend",
        "compare_with": "plain JavaScript without static typing",
        "scenario": "a large frontend codebase shared across several teams",
        "signals": ["type safety", "contracts", "refactoring"],
    },
    {
        "topic_id": "htmlcss",
        "category": "Frontend",
        "title": "HTML and CSS",
        "subtitle": "Layout, semantics, accessibility, and responsive UI",
        "description": "Cover the practical HTML and CSS knowledge that still separates polished frontend engineers from framework-only developers.",
        "level_label": "Beginner to Intermediate",
        "accent": "htmlcss",
        "family": "frontend",
        "compare_with": "framework abstractions without knowing underlying browser layout",
        "scenario": "a responsive product surface that must stay accessible and fast",
        "signals": ["semantics", "layout", "accessibility"],
    },
    {
        "topic_id": "state_management",
        "category": "Frontend",
        "title": "State Management",
        "subtitle": "Local state, shared state, and predictable UI updates",
        "description": "Practice the tradeoffs between colocated state, global stores, caching layers, and UI consistency.",
        "level_label": "Intermediate",
        "accent": "statemanagement",
        "family": "frontend",
        "compare_with": "only using local component state everywhere",
        "scenario": "a complex frontend with shared filters, auth, and server data",
        "signals": ["state locality", "predictability", "render churn"],
    },
    {
        "topic_id": "frontend_performance",
        "category": "Frontend",
        "title": "Frontend Performance",
        "subtitle": "Rendering cost, bundle size, and user-perceived speed",
        "description": "Train on diagnosing slow UI behavior, bundle regressions, and measurable performance improvement work.",
        "level_label": "Advanced",
        "accent": "frontendperformance",
        "family": "frontend",
        "compare_with": "shipping default builds without profiling or measurement",
        "scenario": "a customer-facing page with poor Core Web Vitals",
        "signals": ["bundle size", "render cost", "web vitals"],
    },
    {
        "topic_id": "authentication",
        "category": "Security",
        "title": "Authentication and Authorization",
        "subtitle": "Identity, session flow, and permission boundaries",
        "description": "Practice the difference between knowing who the user is and what the user is allowed to do.",
        "level_label": "Intermediate to Advanced",
        "accent": "authentication",
        "family": "security",
        "compare_with": "simple session checks without a clear permission model",
        "scenario": "a multi-tenant product with role-based access control",
        "signals": ["identity", "session flow", "permission checks"],
    },
    {
        "topic_id": "graphql",
        "category": "Backend",
        "title": "GraphQL",
        "subtitle": "Schema design, resolvers, and client-driven data fetching",
        "description": "Cover when GraphQL improves developer velocity and when it complicates performance, caching, or access control.",
        "level_label": "Intermediate",
        "accent": "graphql",
        "family": "backend",
        "compare_with": "REST APIs with fixed endpoints",
        "scenario": "a product with several clients needing different data shapes",
        "signals": ["schema design", "resolver efficiency", "access control"],
    },
    {
        "topic_id": "terraform",
        "category": "Cloud",
        "title": "Terraform",
        "subtitle": "Infrastructure as code, state management, and repeatable cloud setup",
        "description": "Prepare for platform interviews where infrastructure changes must be reviewable, repeatable, and safe.",
        "level_label": "Intermediate",
        "accent": "terraform",
        "family": "platform",
        "compare_with": "click-ops or hand-maintained cloud configuration",
        "scenario": "a team managing shared infrastructure across multiple environments",
        "signals": ["state files", "drift control", "repeatability"],
    },
    {
        "topic_id": "observability",
        "category": "Platform",
        "title": "Observability",
        "subtitle": "Logs, metrics, traces, and faster incident diagnosis",
        "description": "Practice how to reason about system signals, SLOs, dashboards, and debugging distributed production failures.",
        "level_label": "Intermediate to Advanced",
        "accent": "observability",
        "family": "platform",
        "compare_with": "basic logging without end-to-end visibility",
        "scenario": "an incident where multiple services are involved and root cause is unclear",
        "signals": ["metrics", "traces", "incident diagnosis"],
    },
    {
        "topic_id": "dataengineering",
        "category": "Data",
        "title": "Data Engineering",
        "subtitle": "Pipelines, batch versus streaming, and data quality",
        "description": "Build confidence around data movement, transformation, quality controls, and dependable analytics pipelines.",
        "level_label": "Intermediate to Advanced",
        "accent": "dataengineering",
        "family": "data",
        "compare_with": "ad hoc scripts and manual data movement",
        "scenario": "a product organization relying on trustworthy analytics and ETL",
        "signals": ["data pipelines", "quality checks", "batch vs streaming"],
    },
    {
        "topic_id": "statistics",
        "category": "Data",
        "title": "Statistics for Interviews",
        "subtitle": "Distributions, significance, and evidence-driven decisions",
        "description": "Strengthen the statistical reasoning that supports ML, experimentation, and product decision making.",
        "level_label": "Intermediate",
        "accent": "statistics",
        "family": "data",
        "compare_with": "intuition-only decision making without quantitative validation",
        "scenario": "an experiment or model-evaluation workflow",
        "signals": ["variance", "significance", "sampling"],
    },
    {
        "topic_id": "mlops",
        "category": "AI/ML",
        "title": "MLOps",
        "subtitle": "Model deployment, monitoring, and repeatable ML delivery",
        "description": "Cover the production side of machine learning: versioning, reproducibility, rollout safety, and drift response.",
        "level_label": "Advanced",
        "accent": "mlops",
        "family": "ai",
        "compare_with": "notebook-only experimentation without production discipline",
        "scenario": "a model that must be retrained, deployed, and monitored continuously",
        "signals": ["reproducibility", "model monitoring", "deployment safety"],
    },
]

TOPIC_CATALOG.extend(
    [
        {
            "topic_id": spec["topic_id"],
            "category": spec["category"],
            "title": spec["title"],
            "subtitle": spec["subtitle"],
            "description": spec["description"],
            "level_label": spec["level_label"],
            "accent": spec["accent"],
        }
        for spec in ADDITIONAL_TOPIC_SPECS
    ]
)

ROLE_CATALOG.extend(
    [
        {
            "role_id": "java_backend_engineer",
            "title": "Java Backend Engineer",
            "subtitle": "Java services, SQL, microservices, and backend fundamentals",
            "description": "A role lane focused on backend service design with Java, data access, service boundaries, and reliable APIs.",
            "level_label": "Junior to Mid-level",
            "default_duration": 30,
            "available_durations": [15, 30, 60],
            "topic_weights": {
                "java": 20,
                "database": 12,
                "sql": 10,
                "apis": 10,
                "microservices": 10,
                "distributedsystems": 8,
                "testing": 8,
                "security": 6,
                "authentication": 6,
                "systemdesign": 10,
            },
        },
        {
            "role_id": "python_backend_engineer",
            "title": "Python Backend Engineer",
            "subtitle": "Python services, APIs, data access, and production debugging",
            "description": "A backend lane for Python-heavy services with strong emphasis on APIs, data handling, concurrency, and maintainability.",
            "level_label": "Junior to Mid-level",
            "default_duration": 30,
            "available_durations": [15, 30, 60],
            "topic_weights": {
                "python": 18,
                "database": 12,
                "sql": 10,
                "apis": 12,
                "caching": 8,
                "concurrency": 8,
                "authentication": 6,
                "testing": 8,
                "systemdesign": 10,
                "linux": 8,
            },
        },
        {
            "role_id": "data_engineer",
            "title": "Data Engineer",
            "subtitle": "Pipelines, SQL, cloud data systems, and reliability",
            "description": "A realistic data engineering lane around ETL, SQL, data quality, pipeline operations, and analytics infrastructure.",
            "level_label": "Junior to Mid-level",
            "default_duration": 30,
            "available_durations": [15, 30, 60],
            "topic_weights": {
                "dataengineering": 24,
                "sql": 18,
                "database": 10,
                "python": 10,
                "cloud": 8,
                "distributedsystems": 8,
                "observability": 8,
                "testing": 6,
                "devops": 4,
                "behavioral": 4,
            },
        },
        {
            "role_id": "data_scientist",
            "title": "Data Scientist",
            "subtitle": "Statistics, ML evaluation, Python, and experimentation",
            "description": "A data science lane focused on statistical reasoning, model evaluation, experimentation, and communicating tradeoffs clearly.",
            "level_label": "Junior to Mid-level",
            "default_duration": 30,
            "available_durations": [15, 30, 60],
            "topic_weights": {
                "statistics": 20,
                "machinelearning": 20,
                "python": 16,
                "sql": 10,
                "dataengineering": 8,
                "mlops": 8,
                "genai": 6,
                "behavioral": 6,
                "systemdesign": 6,
            },
        },
        {
            "role_id": "qa_automation_engineer",
            "title": "QA Automation Engineer",
            "subtitle": "Test strategy, APIs, automation reliability, and release confidence",
            "description": "A role-wise interview lane for engineers who build confidence systems through testing, automation, observability, and release checks.",
            "level_label": "Junior to Mid-level",
            "default_duration": 30,
            "available_durations": [15, 30, 60],
            "topic_weights": {
                "testing": 24,
                "apis": 12,
                "javascript": 8,
                "python": 8,
                "sql": 6,
                "observability": 8,
                "devops": 8,
                "linux": 6,
                "security": 6,
                "behavioral": 4,
            },
        },
        {
            "role_id": "security_engineer",
            "title": "Security Engineer",
            "subtitle": "Threat modeling, auth flows, network risk, and secure systems",
            "description": "A security lane that checks practical judgment around risks, mitigations, auth design, cloud posture, and incident impact.",
            "level_label": "Mid-level",
            "default_duration": 30,
            "available_durations": [15, 30, 60],
            "topic_weights": {
                "security": 22,
                "authentication": 18,
                "networking": 10,
                "cloud": 8,
                "apis": 8,
                "systemdesign": 8,
                "linux": 8,
                "observability": 6,
                "distributedsystems": 6,
                "behavioral": 4,
            },
        },
        {
            "role_id": "site_reliability_engineer",
            "title": "Site Reliability Engineer",
            "subtitle": "Reliability, observability, automation, and production response",
            "description": "A reliability-first lane focused on incidents, SLOs, platform safety, distributed systems, and debugging under pressure.",
            "level_label": "Mid-level",
            "default_duration": 30,
            "available_durations": [15, 30, 60],
            "topic_weights": {
                "observability": 20,
                "devops": 16,
                "cloud": 12,
                "kubernetes": 10,
                "linux": 10,
                "networking": 10,
                "distributedsystems": 8,
                "systemdesign": 6,
                "testing": 4,
                "behavioral": 4,
            },
        },
        {
            "role_id": "platform_engineer",
            "title": "Platform Engineer",
            "subtitle": "Internal platforms, orchestration, delivery safety, and developer enablement",
            "description": "A platform engineering lane around infrastructure automation, cluster operations, developer tooling, and stable service delivery.",
            "level_label": "Mid-level",
            "default_duration": 30,
            "available_durations": [15, 30, 60],
            "topic_weights": {
                "kubernetes": 18,
                "docker": 12,
                "terraform": 12,
                "cloud": 12,
                "devops": 10,
                "observability": 10,
                "distributedsystems": 8,
                "linux": 8,
                "security": 5,
                "testing": 5,
            },
        },
        {
            "role_id": "product_engineer",
            "title": "Product Engineer",
            "subtitle": "End-to-end shipping, frontend quality, and API-aware product development",
            "description": "A product-oriented full-stack lane for engineers who own UX, frontend correctness, APIs, and fast iteration tradeoffs.",
            "level_label": "Junior to Mid-level",
            "default_duration": 30,
            "available_durations": [15, 30, 60],
            "topic_weights": {
                "javascript": 12,
                "react": 12,
                "typescript": 10,
                "htmlcss": 8,
                "state_management": 8,
                "frontend_performance": 8,
                "apis": 10,
                "database": 8,
                "testing": 8,
                "behavioral": 8,
                "systemdesign": 6,
            },
        },
        {
            "role_id": "cloud_engineer",
            "title": "Cloud Engineer",
            "subtitle": "Cloud services, infrastructure as code, networking, and secure operations",
            "description": "A cloud-focused lane covering infrastructure automation, container platforms, reliability, cost, and secure service operation.",
            "level_label": "Junior to Mid-level",
            "default_duration": 30,
            "available_durations": [15, 30, 60],
            "topic_weights": {
                "cloud": 18,
                "terraform": 14,
                "kubernetes": 12,
                "docker": 10,
                "networking": 10,
                "security": 8,
                "observability": 8,
                "devops": 8,
                "linux": 6,
                "distributedsystems": 6,
            },
        },
    ]
)

ROLE_WEIGHT_OVERRIDES = {
    "frontend_engineer": {
        "javascript": 18,
        "react": 18,
        "typescript": 12,
        "htmlcss": 10,
        "state_management": 12,
        "frontend_performance": 8,
        "apis": 8,
        "testing": 8,
        "systemdesign": 4,
        "security": 2,
    },
    "backend_engineer": {
        "database": 14,
        "sql": 10,
        "apis": 12,
        "systemdesign": 12,
        "nodejs": 10,
        "os": 8,
        "networking": 6,
        "security": 6,
        "redis": 10,
        "authentication": 6,
        "testing": 2,
        "behavioral": 4,
    },
    "fullstack_engineer": {
        "javascript": 12,
        "react": 12,
        "typescript": 8,
        "state_management": 8,
        "nodejs": 12,
        "apis": 10,
        "graphql": 8,
        "database": 8,
        "systemdesign": 8,
        "testing": 6,
        "security": 4,
        "behavioral": 4,
    },
    "sde_intern": {
        "datastructures": 14,
        "sorting": 8,
        "graphs": 8,
        "dp": 8,
        "algorithms": 10,
        "recursion": 8,
        "strings": 8,
        "os": 8,
        "database": 8,
        "apis": 6,
        "testing": 6,
        "behavioral": 8,
    },
    "java_backend_engineer": {
        "java": 16,
        "oop": 10,
        "designpatterns": 8,
        "lowleveldesign": 6,
        "database": 10,
        "sql": 10,
        "apis": 8,
        "microservices": 10,
        "distributedsystems": 6,
        "testing": 6,
        "authentication": 5,
        "systemdesign": 5,
    },
    "python_backend_engineer": {
        "python": 16,
        "database": 8,
        "sql": 8,
        "apis": 10,
        "caching": 8,
        "redis": 8,
        "mongodb": 8,
        "concurrency": 8,
        "authentication": 6,
        "testing": 6,
        "systemdesign": 8,
        "linux": 6,
    },
    "product_engineer": {
        "javascript": 10,
        "react": 10,
        "typescript": 10,
        "htmlcss": 10,
        "state_management": 8,
        "frontend_performance": 8,
        "graphql": 8,
        "apis": 8,
        "database": 8,
        "testing": 8,
        "behavioral": 6,
        "systemdesign": 6,
    },
    "qa_automation_engineer": {
        "testing": 26,
        "apis": 12,
        "javascript": 8,
        "python": 8,
        "sql": 6,
        "observability": 10,
        "devops": 10,
        "linux": 6,
        "security": 8,
        "behavioral": 6,
    },
    "security_engineer": {
        "security": 22,
        "authentication": 18,
        "networking": 10,
        "cloud": 8,
        "apis": 8,
        "systemdesign": 8,
        "linux": 8,
        "observability": 8,
        "distributedsystems": 6,
        "behavioral": 4,
    },
}

for role in ROLE_CATALOG:
    override = ROLE_WEIGHT_OVERRIDES.get(role["role_id"])
    if override:
        role["topic_weights"] = override

DURATION_BLUEPRINTS = {
    15: {
        "question_count": 4,
        "difficulty_plan": ["easy", "easy", "medium", "medium"],
        "sections": ["warmup", "fundamentals", "applied", "wrapup"],
        "summary_label": "Quick interview sprint",
    },
    30: {
        "question_count": 6,
        "difficulty_plan": ["easy", "easy", "medium", "medium", "medium", "hard"],
        "sections": ["warmup", "fundamentals", "core", "core", "deep_dive", "wrapup"],
        "summary_label": "Balanced screening round",
    },
    60: {
        "question_count": 10,
        "difficulty_plan": ["easy", "easy", "medium", "medium", "medium", "medium", "hard", "hard", "hard", "hard"],
        "sections": ["warmup", "warmup", "fundamentals", "fundamentals", "applied", "applied", "deep_dive", "deep_dive", "deep_dive", "wrapup"],
        "summary_label": "Full mock interview hour",
    },
}

QUESTION_LINE_RE = re.compile(
    r'\{\s*q:\s*"(?P<question>(?:[^"\\]|\\.)+)",\s*difficulty:\s*"(?P<difficulty>easy|medium|hard)"\s*\}'
)
TOPIC_START_RE = re.compile(r"^\s*(?P<topic_id>[a-z0-9_]+)\s*:\s*\[$")
GENERATED_TOPIC_SPEC_BY_ID = {spec["topic_id"]: spec for spec in ADDITIONAL_TOPIC_SPECS}

QUESTION_TEMPLATE_FAMILIES = {
    "core_cs": [
        ("What problem does {title} solve and where is it most useful?", "easy"),
        ("Explain the core idea behind {title}.", "easy"),
        ("How does {title} work at a high level?", "medium"),
        ("When would you choose {title} in a real solution?", "medium"),
        ("Compare {title} with {compare_with}.", "medium"),
        ("What are the main tradeoffs in {title}?", "medium"),
        ("What common mistakes happen when using {title}?", "medium"),
        ("How would you test or validate a solution built around {title}?", "medium"),
        ("What failure modes or edge cases matter in {title}?", "hard"),
        ("How would you optimize {title} for {scenario}?", "hard"),
        ("How would you explain {title} in a real interview from intuition to complexity?", "hard"),
        ("When does {title} become the wrong fit, and what would you choose instead?", "hard"),
    ],
    "backend": [
        ("What problem does {title} solve in modern backend systems?", "easy"),
        ("Explain the core idea behind {title}.", "easy"),
        ("How does {title} work at a high level?", "medium"),
        ("When would you choose {title} in a real backend stack?", "medium"),
        ("Compare {title} with {compare_with}.", "medium"),
        ("What are the main tradeoffs in {title}?", "medium"),
        ("How would you monitor or debug {title} in production?", "medium"),
        ("What common implementation mistakes happen with {title}?", "medium"),
        ("What failure modes or reliability risks matter in {title}?", "hard"),
        ("How would you scale {title} for {scenario}?", "hard"),
        ("How would you design a robust service boundary around {title}?", "hard"),
        ("What security, latency, or data-consistency concerns matter most in {title}?", "hard"),
    ],
    "systems": [
        ("What problem does {title} help solve in real systems?", "easy"),
        ("Explain the core idea behind {title}.", "easy"),
        ("How does {title} work at a high level?", "medium"),
        ("When would you choose {title} in production?", "medium"),
        ("Compare {title} with {compare_with}.", "medium"),
        ("What are the main tradeoffs in {title}?", "medium"),
        ("How would you observe or debug {title} in a live system?", "medium"),
        ("What are the most common failure modes in {title}?", "hard"),
        ("How would you scale or harden {title} for {scenario}?", "hard"),
        ("How would you explain the operational risks of {title} to an engineering team?", "hard"),
        ("What consistency, latency, or coordination issues show up in {title}?", "hard"),
        ("When is {title} not worth the added complexity?", "hard"),
    ],
    "platform": [
        ("What problem does {title} solve for platform teams?", "easy"),
        ("Explain the core idea behind {title}.", "easy"),
        ("How does {title} work at a high level?", "medium"),
        ("When would you adopt {title} in a delivery platform?", "medium"),
        ("Compare {title} with {compare_with}.", "medium"),
        ("What are the main tradeoffs in {title}?", "medium"),
        ("How would you debug operational issues involving {title}?", "medium"),
        ("What common rollout or configuration mistakes happen with {title}?", "medium"),
        ("What failure modes matter in {title} at scale?", "hard"),
        ("How would you run {title} safely for {scenario}?", "hard"),
        ("How would you explain the blast-radius risks around {title}?", "hard"),
        ("What observability or recovery signals matter most for {title}?", "hard"),
    ],
    "engineering": [
        ("What problem does {title} solve in day-to-day engineering work?", "easy"),
        ("Explain the core idea behind {title}.", "easy"),
        ("How does {title} improve code quality or design clarity?", "medium"),
        ("When would you choose {title} in a real codebase?", "medium"),
        ("Compare {title} with {compare_with}.", "medium"),
        ("What are the main tradeoffs in {title}?", "medium"),
        ("What common design mistakes happen when teams use {title} poorly?", "medium"),
        ("How would you review or test a solution built around {title}?", "medium"),
        ("How would you scale {title} for {scenario}?", "hard"),
        ("How would you explain the maintainability risks in {title}?", "hard"),
        ("What follow-up design questions usually appear after {title} in interviews?", "hard"),
        ("When does {title} add more abstraction than value?", "hard"),
    ],
    "frontend": [
        ("What problem does {title} solve in frontend applications?", "easy"),
        ("Explain the core idea behind {title}.", "easy"),
        ("How does {title} work at a high level?", "medium"),
        ("When would you choose {title} in a real UI codebase?", "medium"),
        ("Compare {title} with {compare_with}.", "medium"),
        ("What are the main tradeoffs in {title}?", "medium"),
        ("How would you debug or profile {title} in production?", "medium"),
        ("What common mistakes make teams struggle with {title}?", "medium"),
        ("How would you scale {title} for {scenario}?", "hard"),
        ("What accessibility, performance, or maintainability risks matter in {title}?", "hard"),
        ("How would you design a frontend architecture that uses {title} well?", "hard"),
        ("When does {title} become the wrong abstraction for the UI problem?", "hard"),
    ],
    "data": [
        ("What problem does {title} solve in data-heavy systems?", "easy"),
        ("Explain the core idea behind {title}.", "easy"),
        ("How does {title} work at a high level?", "medium"),
        ("When would you choose {title} in a real data workflow?", "medium"),
        ("Compare {title} with {compare_with}.", "medium"),
        ("What are the main tradeoffs in {title}?", "medium"),
        ("How would you validate or debug {title} in production?", "medium"),
        ("What common mistakes reduce confidence in {title}?", "medium"),
        ("How would you scale {title} for {scenario}?", "hard"),
        ("What data-quality, latency, or cost risks matter in {title}?", "hard"),
        ("How would you explain the correctness guarantees behind {title}?", "hard"),
        ("When does {title} become too complex for the actual business need?", "hard"),
    ],
    "security": [
        ("What problem does {title} solve in secure application design?", "easy"),
        ("Explain the core idea behind {title}.", "easy"),
        ("How does {title} work at a high level?", "medium"),
        ("When would you choose {title} in a production security flow?", "medium"),
        ("Compare {title} with {compare_with}.", "medium"),
        ("What are the main tradeoffs in {title}?", "medium"),
        ("What common mistakes weaken {title} in real products?", "medium"),
        ("How would you test or audit {title} in production?", "medium"),
        ("What failure modes or abuse cases matter in {title}?", "hard"),
        ("How would you scale {title} for {scenario}?", "hard"),
        ("How would you explain the security versus usability tradeoff in {title}?", "hard"),
        ("What logging, alerting, or incident signals matter most for {title}?", "hard"),
    ],
    "ai": [
        ("What problem does {title} solve in production ML systems?", "easy"),
        ("Explain the core idea behind {title}.", "easy"),
        ("How does {title} work at a high level?", "medium"),
        ("When would you choose {title} in a real ML workflow?", "medium"),
        ("Compare {title} with {compare_with}.", "medium"),
        ("What are the main tradeoffs in {title}?", "medium"),
        ("How would you validate or monitor {title} after deployment?", "medium"),
        ("What common mistakes make {title} unreliable?", "medium"),
        ("How would you scale {title} for {scenario}?", "hard"),
        ("What drift, latency, or reproducibility risks matter in {title}?", "hard"),
        ("How would you explain the operational complexity behind {title}?", "hard"),
        ("When does {title} add process overhead without enough product value?", "hard"),
    ],
}


def build_topic_lookup():
    return {topic["topic_id"]: topic for topic in TOPIC_CATALOG}


def render_question_template(spec, template):
    return template.format(
        title=spec["title"],
        compare_with=spec.get("compare_with") or "a simpler alternative",
        scenario=spec.get("scenario") or "a production system with real traffic",
    )


def build_generated_question_items(spec):
    templates = QUESTION_TEMPLATE_FAMILIES.get(spec.get("family"), QUESTION_TEMPLATE_FAMILIES["engineering"])
    return [
        {"question_text": render_question_template(spec, template), "difficulty": difficulty}
        for template, difficulty in templates
    ]


def build_generated_question_bank():
    return {
        spec["topic_id"]: build_generated_question_items(spec)
        for spec in ADDITIONAL_TOPIC_SPECS
    }


def build_question_context(topic_id):
    topic = build_topic_lookup().get(topic_id, {})
    spec = GENERATED_TOPIC_SPEC_BY_ID.get(topic_id, {})
    return {
        "title": topic.get("title") or topic_id.replace("_", " ").title(),
        "subtitle": topic.get("subtitle") or spec.get("subtitle") or topic.get("category", "the topic"),
        "description": topic.get("description") or spec.get("description") or "",
        "compare_with": spec.get("compare_with") or "a simpler alternative",
        "scenario": spec.get("scenario") or "a production system with real traffic",
        "signals": spec.get("signals") or [topic.get("title") or topic_id.replace("_", " ").title()],
    }


def build_sample_answer(question_text, topic_id):
    context = build_question_context(topic_id)
    question_type = detect_question_type(str(question_text or "").lower())
    subject = extract_answer_subject(question_text)
    comparisons = extract_comparison_subjects(question_text)
    signal_text = ", ".join(context["signals"][:3])

    if question_type == "comparison":
        left = comparisons[0] if comparisons else context["title"]
        right = comparisons[1] if len(comparisons) > 1 else context["compare_with"]
        return (
            f"{left} and {right} solve related problems, but they optimize for different tradeoffs. "
            f"I would compare them in terms of {signal_text}, then explain when one is the better fit for the system."
        )

    if question_type in {"decision", "tradeoff"}:
        return (
            f"I would choose {context['title']} when the system needs stronger support for {context['subtitle'].lower()}. "
            f"The decision mainly depends on tradeoffs around {signal_text} and whether the real scenario matches {context['scenario']}."
        )

    if question_type in {"process", "design"}:
        return (
            f"At a high level, {context['title']} is about {context['subtitle'].lower()}. "
            f"I would explain the main flow, the key components involved, and how it behaves in {context['scenario']}."
        )

    if question_type == "complexity":
        return (
            f"I would answer this by describing how {context['title']} works first, then connect that to complexity, bottlenecks, and the main tradeoffs around {signal_text}."
        )

    return (
        f"{context['title']} matters because {context['description'].lower()} "
        f"In practice, I would explain the core idea, where it fits, and the tradeoffs around {signal_text}."
    ).strip()


def build_ideal_answer(question_text, topic_id):
    context = build_question_context(topic_id)
    question_type = detect_question_type(str(question_text or "").lower())
    subject = extract_answer_subject(question_text)
    comparisons = extract_comparison_subjects(question_text)
    signal_text = ", ".join(context["signals"][:3])

    if question_type == "comparison":
        left = comparisons[0] if comparisons else context["title"]
        right = comparisons[1] if len(comparisons) > 1 else context["compare_with"]
        return (
            f"{left} and {right} are related, but I would compare them by goals, operational model, and tradeoffs. "
            f"{left} is usually the better choice when the system needs strength in {context['subtitle'].lower()}, "
            f"while {right} is often preferable when the team wants a different balance around {signal_text}. "
            f"A strong answer should finish with when each option becomes the wrong fit."
        )

    if question_type in {"decision", "tradeoff"}:
        return (
            f"The right answer depends on the system constraints. I would choose {context['title']} when it improves {context['subtitle'].lower()} for {context['scenario']}, "
            f"but I would also call out the cost around {signal_text}. "
            f"The strongest answer explains not just the benefit, but the failure modes, operational cost, and what alternative would be simpler."
        )

    if question_type in {"process", "design"}:
        return (
            f"A strong answer should start with the goal of {context['title']}, then walk through the main components and flow, and finally connect it to a real production scenario like {context['scenario']}. "
            f"I would also mention how the design is validated, where it can fail, and the tradeoffs around {signal_text}."
        )

    if question_type == "complexity":
        return (
            f"I would define the approach behind {context['title']}, then explain why that behavior creates a specific cost profile. "
            f"The best answer ties complexity back to system constraints, edge cases, and practical tradeoffs around {signal_text}."
        )

    return (
        f"{context['title']} matters because {context['description'].lower()} "
        f"A complete interview answer should define the concept clearly, explain how it works at a high level, show where it fits in practice, and mention the tradeoffs around {signal_text}. "
        f"For stronger depth, I would also include one real production example connected to {context['scenario']}."
    ).strip()


def normalize_question_item(topic_id, item):
    question_text = str(item.get("question_text") or item.get("q") or "").strip()
    difficulty = str(item.get("difficulty") or "medium").strip().lower() or "medium"
    if difficulty not in {"easy", "medium", "hard"}:
        difficulty = "medium"
    return {
        "question_text": question_text,
        "difficulty": difficulty,
        "sample_answer": str(item.get("sample_answer") or "").strip() or build_sample_answer(question_text, topic_id),
        "ideal_answer": str(item.get("ideal_answer") or "").strip() or build_ideal_answer(question_text, topic_id),
    }


def parse_question_bank():
    question_bank = {}
    if QUESTION_BANK_PATH.exists():
        current_topic_id = None

        with QUESTION_BANK_PATH.open(encoding="utf-8") as source_file:
            for raw_line in source_file:
                line = raw_line.rstrip()
                topic_match = TOPIC_START_RE.match(line)
                if topic_match:
                    current_topic_id = topic_match.group("topic_id")
                    question_bank[current_topic_id] = []
                    continue

                if current_topic_id and line.strip() == "],":
                    current_topic_id = None
                    continue

                if not current_topic_id:
                    continue

                question_match = QUESTION_LINE_RE.search(line)
                if not question_match:
                    continue

                question_bank[current_topic_id].append(
                    {
                        "question_text": bytes(question_match.group("question"), "utf-8").decode("unicode_escape"),
                        "difficulty": question_match.group("difficulty"),
                    }
                )

    for topic_id, generated_items in build_generated_question_bank().items():
        question_bank.setdefault(topic_id, [])
        question_bank[topic_id].extend(generated_items)

    for topic_id, items in list(question_bank.items()):
        normalized_items = []
        seen = set()
        for item in items:
            normalized = normalize_question_item(topic_id, item)
            if not normalized["question_text"]:
                continue
            signature = normalized["question_text"].strip().lower()
            if signature in seen:
                continue
            seen.add(signature)
            normalized_items.append(normalized)
        question_bank[topic_id] = normalized_items
    return question_bank


def get_topic_catalog_lookup():
    return build_topic_lookup()


def get_role_catalog_lookup():
    return {role["role_id"]: role for role in ROLE_CATALOG}
