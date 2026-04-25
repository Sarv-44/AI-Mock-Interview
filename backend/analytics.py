import re

DIFFICULTY_WEIGHTS = {"easy": 18, "medium": 25, "hard": 32}

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "because", "between", "by",
    "can", "does", "do", "for", "from", "how", "i", "if", "in", "into",
    "is", "it", "of", "on", "or", "the", "their", "them", "this", "to",
    "using", "use", "used", "what", "when", "where", "which", "why", "with",
    "would", "you", "your", "we", "they", "than", "then", "that", "these",
}

QUESTION_NOISE_WORDS = {
    "explain", "difference", "compare", "design", "implement", "works",
    "working", "real", "system", "applications", "application", "example",
    "would", "could", "should", "find", "compute", "choose", "tell",
    "differ", "important", "key",
}

QUESTION_PREFIXES = {
    "what is",
    "what are",
    "explain",
    "how would you",
    "how do you",
    "how does",
    "when would you",
    "why is",
    "why are",
    "compare",
    "describe",
    "walk through",
    "tell me about",
}

TOPIC_HINTS = {
    "graphs": ["graph", "edge", "node", "path", "traversal", "cycle", "shortest", "bfs", "dfs"],
    "datastructures": ["array", "list", "tree", "stack", "queue", "hash", "heap", "memory"],
    "sorting": ["sort", "partition", "merge", "pivot", "stable", "comparison", "complexity"],
    "dbms": ["database", "index", "query", "join", "transaction", "normalization", "consistency"],
    "os": ["process", "thread", "memory", "scheduling", "deadlock", "paging", "kernel"],
    "oops": ["class", "object", "inheritance", "polymorphism", "encapsulation", "abstraction"],
    "systemdesign": ["scale", "latency", "cache", "replication", "queue", "database", "availability"],
    "java": ["jvm", "garbage", "class", "thread", "interface", "stream", "exception"],
    "javascript": ["event", "scope", "closure", "promise", "async", "prototype", "runtime"],
    "react": ["component", "state", "props", "render", "effect", "hook", "tree"],
    "nodejs": ["event", "loop", "server", "async", "stream", "middleware", "runtime"],
    "machinelearning": ["model", "training", "feature", "bias", "variance", "overfitting", "evaluation"],
    "genai": ["prompt", "token", "embedding", "hallucination", "retrieval", "context", "generation"],
    "cloud": ["service", "region", "autoscaling", "availability", "storage", "network", "cost"],
    "networking": ["packet", "tcp", "udp", "latency", "throughput", "routing", "protocol"],
    "security": ["auth", "encryption", "attack", "token", "access", "vulnerability", "audit"],
    "testing": ["test", "unit", "integration", "mock", "coverage", "assertion", "regression"],
    "devops": ["deploy", "pipeline", "container", "monitoring", "automation", "rollback", "ci"],
    "apis": ["request", "response", "rest", "endpoint", "versioning", "rate", "contract"],
    "frontend": ["ui", "state", "render", "layout", "component", "event", "browser"],
    "backend": ["service", "database", "queue", "latency", "scaling", "api", "worker"],
}

TOPIC_REFERENCE_TERMS = {
    "graphs": ["traversal", "shortest path", "cycle detection", "connectivity"],
    "datastructures": ["lookup cost", "insertion and deletion", "memory tradeoff", "ordering property"],
    "sorting": ["time complexity", "stability", "partitioning", "practical use case"],
    "dp": ["state definition", "transition", "base case", "overlapping subproblems"],
    "database": ["query performance", "read-write tradeoff", "schema design", "consistency"],
    "systemdesign": ["request flow", "scaling bottleneck", "data storage", "tradeoff"],
    "behavioral": ["situation", "action", "result", "reflection"],
    "python": ["language behavior", "use case", "tradeoff", "implementation detail"],
    "os": ["memory model", "scheduling", "concurrency risk", "system behavior"],
    "java": ["runtime behavior", "language feature", "use case", "tradeoff"],
    "javascript": ["scope", "runtime behavior", "async flow", "practical example"],
    "react": ["component model", "rendering behavior", "state flow", "practical use case"],
    "nodejs": ["event loop", "I/O behavior", "throughput", "production tradeoff"],
    "machinelearning": ["goal", "evaluation metric", "tradeoff", "practical failure mode"],
    "genai": ["model behavior", "retrieval", "latency-cost tradeoff", "risk control"],
    "cloud": ["resilience", "scaling", "cost", "operational tradeoff"],
    "networking": ["latency", "reliability", "protocol behavior", "use case"],
    "security": ["risk", "mitigation", "access control", "real-world example"],
    "testing": ["scope", "confidence", "cost", "failure mode"],
    "devops": ["deployment flow", "observability", "rollback strategy", "operational risk"],
    "apis": ["contract", "idempotency", "versioning", "error handling"],
}

KEYWORD_ALIASES = {
    "bfs": ["breadth first search"],
    "dfs": ["depth first search"],
    "dbms": ["database management system", "database systems"],
    "oops": ["object oriented programming", "oop", "object-oriented programming"],
    "genai": ["generative ai", "llm", "large language model"],
    "bst": ["binary search tree"],
    "api": ["application programming interface"],
    "read": ["lookup", "retrieve", "find rows", "find data", "reads"],
    "query": ["lookup", "read request", "database read"],
    "identity": ["who the user is", "who you are", "verify the user"],
    "permission": ["allowed to access", "allowed to do", "what you can do", "what the user can access"],
    "authorization": ["authz"],
    "authentication": ["authn"],
}

TECHNICAL_SIGNAL_TERMS = [
    "o(", "big o", "tradeoff", "latency", "throughput", "consistency", "availability",
    "memory", "space complexity", "time complexity", "queue", "stack", "tree", "graph",
    "hash", "index", "cache", "partition", "recursion", "iteration", "asynchronous",
    "synchronous", "locking", "retry", "timeout", "protocol", "database", "query",
    "join", "binary search tree", "heap", "load balancer",
]

COMPARISON_SIGNALS = [
    "whereas", "while", "compared", "instead", "on the other hand", "tradeoff",
    "better", "worse", "faster", "slower", "more memory", "less memory",
    "difference", "different", "unlike",
]
PROCESS_SIGNALS = [
    "first", "then", "next", "after that", "finally", "start with", "we maintain",
    "we update", "we traverse", "step", "repeat", "before that", "once",
]
EXAMPLE_SIGNALS = ["for example", "for instance", "imagine", "suppose", "let's say", "consider"]
DEFINITION_SIGNALS = [" is ", " are ", " means ", " refers to ", " can be defined as "]
TRADEOFF_SIGNALS = [
    "tradeoff", "advantage", "benefit", "pro", "disadvantage", "drawback",
    "con", "better", "worse", "cost", "risk", "limitation", "overhead",
]
DESIGN_SIGNALS = [
    "service", "api", "database", "cache", "queue", "worker", "replication",
    "partition", "shard", "load balancer", "read path", "write path",
]
DECISION_SIGNALS = [
    "depends", "when", "if", "choose", "prefer", "based on", "in that case",
    "best when", "good when", "use it when",
]
RESULT_SIGNALS = ["result", "therefore", "so that", "which means", "this helps", "this makes"]
HEDGING_TERMS = ["i think", "maybe", "probably", "kind of", "sort of", "not sure", "i guess"]
VAGUE_TERMS = ["something", "anything", "everything", "stuff", "things", "somehow", "whatever", "basically", "etc"]
ROMANIZED_HINDI_TERMS = {
    "acha", "accha", "agar", "aur", "bas", "fir", "haan", "haanji", "hai", "hota",
    "hoti", "hote", "isme", "ismein", "iska", "karna", "karte", "ki", "kyunki",
    "lekin", "matlab", "nahi", "samjho", "thoda", "toh", "waise", "wala", "wali",
    "yeh", "woh",
}

QUESTION_GUIDANCE = {
    "what is the difference between unit, integration, and end-to-end tests": {
        "points": [
            {
                "label": "unit tests cover one small unit in isolation",
                "groups": [["unit"], ["isolation", "isolated", "single function", "single class", "smallest testable unit"]],
            },
            {
                "label": "integration tests verify multiple components working together",
                "groups": [["integration"], ["work together", "interaction", "between modules", "components", "data flow"]],
            },
            {
                "label": "end-to-end tests validate the full user flow across the system",
                "groups": [["end-to-end", "e2e"], ["full user flow", "full system", "user journey", "end to end"]],
            },
            {
                "label": "the main tradeoff is speed versus confidence",
                "groups": [["fast", "faster", "slow", "slower", "brittle"], ["confidence", "coverage", "realistic"]],
            },
        ],
        "sample_answer": (
            "Unit tests check one small piece of logic in isolation, like a single function or class, usually with mocks for dependencies. "
            "Integration tests check that multiple parts work together correctly, for example an API, service, and database interaction. "
            "End-to-end tests validate the full user flow through the actual system, such as logging in and completing a checkout. "
            "The main difference is scope and confidence: unit tests are fastest and easiest to debug, integration tests verify boundaries, and end-to-end tests give the most realistic coverage but are slower and more brittle. "
            "In practice, I would use many unit tests, fewer integration tests, and a small set of critical end-to-end tests."
        ),
    },
    "how do you decide what should be tested at each level": {
        "points": [
            {"label": "unit tests should cover local business logic", "groups": [["unit"], ["logic", "small piece", "single function", "isolated"]]},
            {"label": "integration tests should cover boundaries between components", "groups": [["integration"], ["boundary", "service", "database", "api", "components"]]},
            {"label": "end-to-end tests should focus on critical user journeys", "groups": [["end-to-end", "e2e"], ["critical flow", "user flow", "journey"]]},
            {"label": "the test mix should balance speed, confidence, and maintenance cost", "groups": [["speed", "confidence", "cost", "maintenance", "tradeoff"]]},
        ],
        "sample_answer": (
            "I decide the test level based on what kind of risk I am trying to catch. "
            "If I want to validate pure business logic quickly, I use unit tests. "
            "If the risk is at the boundary between components, like a service calling a database or an external API, I use integration tests. "
            "If I need confidence that a critical user journey works in the real system, I add an end-to-end test. "
            "So the rule is to keep most tests low-level for speed, then add a smaller number of integration and end-to-end tests for high-value flows."
        ),
    },
    "what makes a test flaky and how would you fix it": {
        "points": [
            {"label": "flaky tests fail intermittently without real code changes", "groups": [["flaky"], ["intermittent", "sometimes fails", "non-deterministic"]]},
            {"label": "common causes include timing, shared state, or external dependency issues", "groups": [["timing", "race condition", "shared state", "external dependency", "network", "order dependent"]]},
            {"label": "fixes include removing nondeterminism and improving isolation", "groups": [["fix", "stabilize", "isolate"], ["deterministic", "mock", "reset state", "cleanup", "wait correctly"]]},
        ],
        "sample_answer": (
            "A flaky test is a test that passes and fails inconsistently even when the code has not meaningfully changed. "
            "That usually happens because of nondeterminism, like timing issues, shared state, order dependence, or unstable external dependencies. "
            "To fix it, I first reproduce it reliably, then remove the source of nondeterminism by isolating state, mocking unstable dependencies, using proper synchronization instead of arbitrary sleeps, and making test data deterministic. "
            "The goal is that the test only fails when the product behavior is actually broken."
        ),
    },
    "how would you test a feature that relies on third-party apis": {
        "points": [
            {"label": "mock or stub the third-party API in most automated tests", "groups": [["mock", "stub", "fake"], ["third-party", "external api", "dependency"]]},
            {"label": "add integration or contract tests for the real interface", "groups": [["integration", "contract"], ["real interface", "schema", "response format", "api contract"]]},
            {"label": "test failures such as timeouts, retries, and bad responses", "groups": [["timeout", "retry", "failure", "error", "rate limit", "bad response"]]},
        ],
        "sample_answer": (
            "For a feature that depends on a third-party API, I would not hit the real provider in most automated tests. "
            "I would use mocks or stubs for normal unit and integration coverage so the tests stay fast and deterministic. "
            "Then I would add a smaller set of integration or contract tests to verify that our assumptions about the real API, like request shape and response format, still hold. "
            "I would also test failure paths such as timeouts, retries, partial failures, and rate limits, because those are often where production issues happen."
        ),
    },
    "what is the difference between mocking and stubbing": {
        "points": [
            {"label": "a stub provides predefined data or behavior", "groups": [["stub"], ["predefined", "fixed response", "dummy data"]]},
            {"label": "a mock is used to verify interactions or expectations", "groups": [["mock"], ["verify", "expectation", "interaction", "called with"]]},
            {"label": "the difference is state versus behavior verification", "groups": [["difference", "verify"], ["behavior", "interaction", "returned data", "response"]]},
        ],
        "sample_answer": (
            "A stub is a test double that returns predefined data so the test can keep moving. "
            "A mock is a test double that is mainly used to verify interactions, like whether a method was called with the right arguments. "
            "So the practical difference is that stubs help control input, while mocks help assert behavior between components."
        ),
    },
    "how do you design tests for asynchronous workflows": {
        "points": [
            {"label": "the test should wait on real completion conditions, not arbitrary sleeps", "groups": [["wait", "await", "poll"], ["condition", "event", "completion", "sleep"]]},
            {"label": "the workflow should be broken into deterministic states or steps", "groups": [["state", "step", "event", "queue", "job"]]},
            {"label": "timeouts, retries, and failure cases should be covered", "groups": [["timeout", "retry", "failure", "dead letter", "error"]]},
        ],
        "sample_answer": (
            "For asynchronous workflows, I try to test against observable completion conditions instead of using arbitrary sleeps. "
            "For example, I wait for a job status change, an event, or a database update that proves the workflow finished. "
            "I also break the system into deterministic steps so I can test each stage in isolation where possible, then add a smaller number of integration tests for the full async path. "
            "Finally, I cover edge cases like retries, timeouts, duplicate events, and failure recovery."
        ),
    },
    "what should be covered in a regression test suite": {
        "points": [
            {"label": "critical business flows should be covered", "groups": [["critical", "important", "high-value"], ["flow", "journey", "path", "business"]]},
            {"label": "past bugs should be added to prevent reintroduction", "groups": [["past bug", "bug fix", "regression", "previous failure"]]},
            {"label": "high-risk integrations or edge cases should be included", "groups": [["integration", "edge case", "risk", "boundary"]]},
        ],
        "sample_answer": (
            "A regression suite should cover the parts of the system that are most expensive to break. "
            "That usually means critical business flows, important integrations, and bugs that have already happened once and must not come back. "
            "I would not try to put every test into the regression suite, because that makes it slow and noisy. "
            "Instead, I would keep it focused on high-value coverage that gives strong release confidence."
        ),
    },
    "how do you keep test suites fast as a codebase grows": {
        "points": [
            {"label": "most tests should stay at the unit level", "groups": [["unit"], ["fast", "cheap", "small"]]},
            {"label": "slow end-to-end coverage should stay focused on critical paths", "groups": [["end-to-end", "e2e"], ["critical", "small set", "few"]]},
            {"label": "parallelization and good test isolation help runtime", "groups": [["parallel", "parallelize", "shard"], ["isolation", "independent", "shared state"]]},
        ],
        "sample_answer": (
            "The main way to keep a test suite fast is to keep most coverage at the unit level and only use slower integration or end-to-end tests where they add real value. "
            "I also keep end-to-end coverage focused on a small number of critical flows instead of trying to test everything through the UI. "
            "On top of that, I parallelize test execution, remove shared-state coupling, and clean up flaky or redundant tests so the suite stays reliable as it grows."
        ),
    },
    "what is contract testing and where is it useful": {
        "points": [
            {"label": "contract testing verifies the agreement between systems", "groups": [["contract"], ["agreement", "interface", "schema", "api"]]},
            {"label": "it is useful between services or teams that integrate independently", "groups": [["service", "consumer", "provider", "team"], ["independent", "integration", "between systems"]]},
            {"label": "it helps catch breaking API changes early", "groups": [["breaking change", "compatibility", "early", "prevent"]]},
        ],
        "sample_answer": (
            "Contract testing checks that two systems still agree on the interface between them, such as request fields, response shape, or event schema. "
            "It is especially useful when a consumer and provider evolve independently, like separate microservices or partner integrations. "
            "The value is that it catches breaking interface changes earlier than full end-to-end testing, while staying faster and more focused."
        ),
    },
    "how would you test for race conditions or concurrency bugs": {
        "points": [
            {"label": "the test should force concurrent access or competing operations", "groups": [["concurrent", "parallel", "race", "simultaneous"]]},
            {"label": "shared state and ordering assumptions should be stressed", "groups": [["shared state", "ordering", "lock", "synchronization", "atomic"]]},
            {"label": "the test should look for nondeterministic failures or invariant violations", "groups": [["invariant", "data corruption", "duplicate", "non-deterministic", "intermittent"]]},
        ],
        "sample_answer": (
            "To test race conditions, I try to force the system into the risky state instead of waiting for it to happen by chance. "
            "That means running competing operations in parallel, increasing contention on shared state, and repeating the test enough times to expose nondeterministic failures. "
            "I would also assert invariants like no lost updates, no duplicate processing, and no corrupted state. "
            "If needed, I would add targeted instrumentation or deterministic scheduling hooks to make the concurrency bug reproducible."
        ),
    },
    "what are some signals that a team is over-testing or under-testing": {
        "points": [
            {"label": "under-testing shows up as repeated escaped bugs or low release confidence", "groups": [["escaped bug", "production issue", "low confidence", "manual regression", "fear of release"]]},
            {"label": "over-testing shows up as slow noisy suites with low signal", "groups": [["slow", "noisy", "brittle", "duplicate", "maintenance cost"]]},
            {"label": "the right balance ties tests to risk and value", "groups": [["risk", "value", "balance", "critical flow", "confidence"]]},
        ],
        "sample_answer": (
            "A team is usually under-testing when the same kinds of bugs keep escaping to production, releases feel risky, and people rely too much on manual regression. "
            "A team is over-testing when the suite is slow, brittle, expensive to maintain, and full of low-signal tests that do not improve confidence. "
            "The right balance is not about maximizing test count. It is about using the cheapest test that can cover the real risk."
        ),
    },
    "how do you measure whether your tests are actually useful": {
        "points": [
            {"label": "useful tests improve confidence and catch real regressions", "groups": [["confidence", "catch", "regression", "failure"]]},
            {"label": "speed, stability, and maintenance cost matter too", "groups": [["speed", "stable", "flaky", "maintenance", "cost"]]},
            {"label": "coverage percentage alone is not enough", "groups": [["coverage"], ["not enough", "insufficient", "alone"]]},
        ],
        "sample_answer": (
            "I measure test usefulness by whether the suite catches meaningful regressions and increases release confidence, not just by code coverage percentage. "
            "A useful test suite should be reasonably fast, stable, and cheap enough to maintain. "
            "If tests are flaky, redundant, or never catch real issues, they are not providing much value even if coverage numbers look high. "
            "So I look at signal quality, escaped defects, runtime, flakiness, and how well the tests protect high-risk behavior."
        ),
    },
    "what is the difference between a binary tree and a binary search tree": {
        "points": [
            {"label": "a binary tree only limits each node to at most two children", "groups": [["binary tree"], ["two children", "at most two"]]},
            {"label": "a binary search tree adds an ordering rule", "groups": [["binary search tree", "bst"], ["left", "right", "smaller", "greater", "ordering"]]},
            {"label": "the ordering makes search and ordered operations more efficient", "groups": [["search", "ordered", "lookup", "efficient", "faster"]]},
        ],
        "sample_answer": (
            "A binary tree is any tree where each node has at most two children. "
            "A binary search tree is a special kind of binary tree where values are ordered, so nodes on the left are smaller and nodes on the right are larger. "
            "The main difference is that a plain binary tree has no ordering guarantee, while a BST does, which makes searching and ordered operations much more efficient when the tree stays balanced."
        ),
        "ideal_answer": (
            "A binary tree is a tree in which each node can have at most two children, but it does not impose any ordering on the stored values. "
            "A binary search tree is a special type of binary tree where values in the left subtree are smaller than the node and values in the right subtree are larger. "
            "Because of that ordering property, a BST supports efficient search, insertion, and deletion when it is reasonably balanced, while a general binary tree does not automatically give that benefit."
        ),
    },
    "what is database indexing": {
        "points": [
            {"label": "an index is an extra data structure used to speed up lookups", "groups": [["index", "indexing"], ["speed", "faster", "lookup", "search", "query"]]},
            {"label": "the database uses the index to avoid scanning every row", "groups": [["avoid", "instead of", "without"], ["full scan", "scan every row", "entire table", "table scan"]]},
            {"label": "indexes improve read performance but add storage or write overhead", "groups": [["read", "query"], ["write", "insert", "update", "storage", "overhead"]]},
        ],
        "sample_answer": (
            "Database indexing is a way to speed up data retrieval by creating an extra structure that helps the database locate rows quickly. "
            "Instead of scanning the entire table for every query, the database can use the index to jump closer to the matching records. "
            "The tradeoff is that indexes improve read performance, but they also take extra storage and can slow down writes like inserts, updates, and deletes."
        ),
        "ideal_answer": (
            "Database indexing is the technique of creating an auxiliary data structure, often something like a B-tree, so the database can find rows more efficiently. "
            "Without an index, the database may need to scan the whole table to answer a query. "
            "With an index, it can narrow the search space much faster, which improves read-heavy workloads. "
            "The tradeoff is that indexes consume extra storage and make writes more expensive because the index also has to be maintained whenever data changes."
        ),
    },
    "what is normalization in databases": {
        "points": [
            {"label": "normalization organizes relational data to reduce redundancy", "groups": [["normalization"], ["reduce redundancy", "duplicate data", "redundancy"]]},
            {"label": "it splits data into related tables with keys", "groups": [["table", "tables"], ["key", "foreign key", "relationship", "related tables"]]},
            {"label": "the goal is better integrity and fewer update anomalies", "groups": [["integrity", "consistency", "anomaly", "update anomaly", "insert anomaly", "delete anomaly"]]},
        ],
        "sample_answer": (
            "Normalization is the process of organizing relational data into separate related tables so you reduce redundancy and keep the data more consistent. "
            "Instead of repeating the same information in many places, you split it into logical tables and connect them with keys. "
            "That helps prevent update anomalies and keeps the schema cleaner, although in some systems you may denormalize a bit later for read performance."
        ),
        "ideal_answer": (
            "Normalization is a database design technique used to reduce redundant data and improve data integrity by splitting information into well-structured related tables. "
            "The tables are connected through keys, which helps avoid problems like update, insert, and delete anomalies. "
            "In practice, normalization makes the schema cleaner and more consistent, although highly read-heavy systems may selectively denormalize for performance."
        ),
    },
    "what is a database transaction and what are acid properties": {
        "points": [
            {"label": "a transaction is a unit of work that should succeed or fail together", "groups": [["transaction"], ["all or nothing", "unit of work", "commit", "rollback"]]},
            {"label": "acid stands for atomicity consistency isolation and durability", "groups": [["atomicity"], ["consistency"], ["isolation"], ["durability"]]},
            {"label": "acid properties protect correctness under failures or concurrency", "groups": [["correctness", "reliable", "failure", "concurrency", "concurrent"]]},
        ],
        "sample_answer": (
            "A database transaction is a unit of work that should either complete fully or not happen at all, which is why commits and rollbacks matter. "
            "The ACID properties are atomicity, consistency, isolation, and durability. "
            "Together they help keep the database correct even when multiple operations happen concurrently or a failure occurs in the middle of the work."
        ),
    },
    "explain read replicas and how they improve scalability": {
        "points": [
            {"label": "read replicas are copies of the primary database used for reads", "groups": [["read replica", "replica"], ["copy", "secondary", "primary", "read traffic"]]},
            {"label": "they offload read traffic from the primary database", "groups": [["offload", "reduce load", "scale reads", "read-heavy"]]},
            {"label": "they introduce replication lag or consistency tradeoffs", "groups": [["lag", "eventual consistency", "replication delay", "stale data"]]},
        ],
        "sample_answer": (
            "Read replicas are secondary copies of the primary database that handle read queries. "
            "They improve scalability by moving read traffic away from the main database, which is especially useful in read-heavy systems. "
            "The tradeoff is that replicas can be slightly behind the primary, so you need to think about replication lag and stale reads."
        ),
    },
    "what is a heap and why is it useful for priority queues": {
        "points": [
            {"label": "a heap is a tree-based structure with an ordering property", "groups": [["heap"], ["tree", "ordering", "min-heap", "max-heap", "parent"]]},
            {"label": "the root keeps the highest-priority or lowest-priority element", "groups": [["root"], ["priority", "minimum", "maximum", "highest", "lowest"]]},
            {"label": "heaps make priority queue operations efficient", "groups": [["priority queue"], ["insert", "extract", "remove", "efficient", "log"]]},
        ],
        "sample_answer": (
            "A heap is a tree-based data structure that maintains an ordering property, so in a min-heap the smallest element stays near the root and in a max-heap the largest element does. "
            "That makes it useful for priority queues because you can quickly access and remove the highest-priority or lowest-priority item. "
            "Heaps are a good fit when you need repeated insertions plus fast retrieval of the next most important element."
        ),
        "ideal_answer": (
            "A heap is a specialized tree-based data structure, usually implemented with an array, that maintains a partial ordering property. "
            "In a min-heap, each parent is less than or equal to its children, so the minimum element stays at the root. "
            "In a max-heap, the maximum element stays at the root. "
            "That is why heaps are useful for priority queues: insertion and removal remain efficient, while access to the highest-priority or lowest-priority element is immediate."
        ),
    },
    "what is the difference between a queue and a deque": {
        "points": [
            {"label": "a queue usually follows first in first out order", "groups": [["queue"], ["fifo", "first in first out", "front", "rear"]]},
            {"label": "a deque supports insertion and removal at both ends", "groups": [["deque"], ["both ends", "front and back", "double ended"]]},
            {"label": "a deque is more flexible but a queue is simpler for strict fifo flows", "groups": [["flexible", "strict", "fifo", "use case", "task scheduling"]]},
        ],
        "sample_answer": (
            "A queue is a FIFO data structure, so the first element inserted is the first one removed. "
            "A deque, or double-ended queue, lets you insert and remove elements from both the front and the back. "
            "So a deque is more flexible, while a normal queue is the better fit when you want strict first-in-first-out behavior, like job scheduling."
        ),
    },
    "explain the difference between sql and nosql": {
        "points": [
            {"label": "sql databases use structured relational tables", "groups": [["sql"], ["relational", "table", "schema"]]},
            {"label": "nosql databases support more flexible non-relational data models", "groups": [["nosql"], ["flexible", "document", "key-value", "wide-column", "graph"]]},
            {"label": "the tradeoff is consistency and joins versus flexibility and scale patterns", "groups": [["join", "consistency", "schema"], ["scale", "flexibility", "horizontal"]]},
        ],
        "sample_answer": (
            "SQL databases are relational, so they store data in structured tables with a defined schema and are strong when you need joins, transactions, and consistent relationships. "
            "NoSQL databases use more flexible models like document, key-value, or graph storage, which can be easier to scale for certain workloads and changing data shapes. "
            "So the difference is not that one is always better. SQL is great for structured relational data, while NoSQL is useful when you need schema flexibility or a data model that does not fit tables well."
        ),
    },
    "what is the difference between a process and a thread": {
        "points": [
            {"label": "a process has its own memory space", "groups": [["process"], ["own memory", "separate memory", "isolated"]]},
            {"label": "threads share memory inside the same process", "groups": [["thread"], ["shared memory", "same process"]]},
            {"label": "threads are lighter but need synchronization", "groups": [["lighter", "context switch", "synchronization", "race condition"]]},
        ],
        "sample_answer": (
            "A process is an independent program in execution with its own memory space and system resources. "
            "A thread is a lighter unit of execution that runs inside a process and shares that process memory with other threads. "
            "So processes give stronger isolation, while threads are cheaper for concurrency but require careful synchronization because they share data."
        ),
    },
    "explain the difference between horizontal and vertical scaling": {
        "points": [
            {"label": "vertical scaling means adding more power to one machine", "groups": [["vertical"], ["bigger machine", "more cpu", "more ram", "single server"]]},
            {"label": "horizontal scaling means adding more machines", "groups": [["horizontal"], ["more machines", "more servers", "instances"]]},
            {"label": "horizontal scaling improves capacity and resilience but adds distributed-system complexity", "groups": [["resilience", "availability", "complexity", "load balancer", "distributed"]]},
        ],
        "sample_answer": (
            "Vertical scaling means making one machine stronger, for example by adding more CPU, RAM, or storage. "
            "Horizontal scaling means adding more machines or instances and distributing traffic across them. "
            "Vertical scaling is simpler at first, but horizontal scaling is usually better for large systems because it improves capacity and resilience, even though it adds distributed-system complexity."
        ),
    },
    "what is the difference between tcp and udp": {
        "points": [
            {"label": "tcp is connection-oriented and reliable", "groups": [["tcp"], ["reliable", "ordered", "connection-oriented", "acknowledgment"]]},
            {"label": "udp is connectionless and lower overhead", "groups": [["udp"], ["connectionless", "low overhead", "faster", "no guarantee"]]},
            {"label": "tcp is used when correctness matters more and udp when latency matters more", "groups": [["latency", "streaming", "video", "gaming", "correctness", "delivery"]]},
        ],
        "sample_answer": (
            "TCP is a connection-oriented protocol that provides reliable and ordered delivery, so it is a good fit when correctness matters, like web requests or database communication. "
            "UDP is connectionless and has lower overhead, so it is often used when low latency matters more than guaranteed delivery, like live streaming, gaming, or DNS. "
            "So the main tradeoff is reliability and ordering versus speed and lower overhead."
        ),
    },
    "how do authentication and authorization differ": {
        "points": [
            {"label": "authentication verifies identity", "groups": [["authentication"], ["identity", "who you are", "who the user is", "verify user"]]},
            {"label": "authorization decides what the user can access", "groups": [["authorization"], ["permission", "access", "allowed", "what you can do"]]},
            {"label": "authentication usually happens before authorization", "groups": [["before", "after login", "once authenticated", "after identity", "after they are authenticated"]]},
        ],
        "sample_answer": (
            "Authentication is about verifying who a user is, for example by checking a password, token, or login session. "
            "Authorization is about deciding what that authenticated user is allowed to access or do. "
            "So authentication answers who you are, while authorization answers what you can do, and in most systems authentication happens first."
        ),
    },
    "explain the difference between state and props": {
        "points": [
            {"label": "props are inputs passed into a component", "groups": [["props"], ["input", "passed", "parent", "read-only"]]},
            {"label": "state is data managed by the component itself", "groups": [["state"], ["managed", "owned", "local", "internal"]]},
            {"label": "state changes over time while props are received from outside", "groups": [["change", "update", "outside", "component"]]},
        ],
        "sample_answer": (
            "Props are inputs passed from a parent component to a child component. "
            "State is data that a component manages for itself and can update over time. "
            "So props are external inputs, while state is internal mutable data that drives the component's behavior and rendering."
        ),
    },
    "what are the key differences between var, let, and const": {
        "points": [
            {"label": "var is function-scoped and can be redeclared", "groups": [["var"], ["function-scoped", "redeclare", "hoist"]]},
            {"label": "let is block-scoped and can be reassigned", "groups": [["let"], ["block-scoped", "reassign"]]},
            {"label": "const is block-scoped and cannot be reassigned", "groups": [["const"], ["block-scoped", "cannot be reassigned", "not reassign"]]},
        ],
        "sample_answer": (
            "The main difference is scope and reassignment behavior. "
            "Var is function-scoped and can be redeclared, which is why it can create confusing bugs. "
            "Let is block-scoped and can be reassigned, so it is better for values that change. "
            "Const is also block-scoped but cannot be reassigned, so it is the default choice when the binding should stay fixed."
        ),
    },
    "how do promises differ from async and await": {
        "points": [
            {"label": "promises represent future asynchronous results", "groups": [["promise", "promises"], ["future result", "asynchronous result", "eventual result"]]},
            {"label": "async and await are syntax built on top of promises", "groups": [["async"], ["await"], ["syntax", "built on top", "uses promises"]]},
            {"label": "async and await improve readability while async functions still return promises", "groups": [["readable", "cleaner", "synchronous style"], ["return promise", "still return promises"]]},
        ],
        "sample_answer": (
            "Promises are objects that represent the eventual result of asynchronous work. "
            "Async and await are syntax built on top of promises that make asynchronous code easier to read and write. "
            "An async function still returns a promise, but await lets you pause inside that function until a promise settles, so the control flow feels cleaner than chaining then calls everywhere."
        ),
    },
    "what is the event loop and how does asynchronous code run in javascript": {
        "points": [
            {"label": "javascript runs on a single main call stack", "groups": [["single"], ["call stack", "main thread", "single-threaded"]]},
            {"label": "async work is handled by browser or runtime APIs and queued back later", "groups": [["web api", "runtime", "browser", "node"], ["queue", "callback queue", "task queue", "microtask"]]},
            {"label": "the event loop moves ready callbacks onto the stack when it is free", "groups": [["event loop"], ["stack", "free", "callback", "microtask", "macrotask"]]},
        ],
        "sample_answer": (
            "The event loop is the mechanism that lets JavaScript handle asynchronous work without blocking the main call stack. "
            "JavaScript itself runs code on a single call stack, while timers, network calls, and similar operations are handled by the browser or runtime. "
            "When those operations finish, their callbacks are placed into queues, and the event loop pushes them back onto the stack when the stack becomes free."
        ),
    },
    "what is a cdn and why is it important for scalability": {
        "points": [
            {"label": "a cdn is a distributed network of edge servers", "groups": [["cdn"], ["distributed", "edge", "servers", "edge locations"]]},
            {"label": "it serves content closer to users to reduce latency", "groups": [["closer to users", "near users", "latency", "faster delivery", "cache"]]},
            {"label": "it improves scalability by reducing origin load", "groups": [["scale", "scalability", "origin", "offload", "less load"]]},
        ],
        "sample_answer": (
            "A CDN, or content delivery network, is a distributed set of edge servers that cache and serve content closer to users. "
            "That reduces latency because users do not always need to fetch static assets from the origin server directly. "
            "It also improves scalability by offloading traffic from the origin, so the main application infrastructure does not have to serve every request itself."
        ),
    },
}

QUESTION_CONTRADICTION_PATTERNS = {
    "what is the difference between a binary tree and a binary search tree": [
        {"label": "treated a binary tree and BST as the same thing", "patterns": ["same thing", "exactly the same", "no difference"]},
        {"label": "said every binary tree follows BST ordering", "patterns": ["every binary tree is ordered", "binary tree is ordered", "all binary trees are search trees"]},
    ],
    "what is database indexing": [
        {"label": "claimed indexes always improve writes", "patterns": ["indexes make writes faster", "indexes speed up inserts", "indexes speed up updates"]},
        {"label": "claimed indexes help every query automatically", "patterns": ["indexes help every query", "indexes always make queries faster", "every query faster"]},
    ],
    "how do authentication and authorization differ": [
        {
            "label": "reversed authentication and authorization",
            "regex_patterns": [
                r"authentication.{0,40}(access|allowed|permission)",
                r"authorization.{0,40}(identity|who the user is|who you are|verify)",
            ],
        },
    ],
    "how do promises differ from async and await": [
        {"label": "claimed async and await are unrelated to promises", "patterns": ["async await is not based on promises", "async await has nothing to do with promises"]},
        {"label": "claimed promises are synchronous", "patterns": ["promises are synchronous", "promise is synchronous"]},
    ],
    "what is the difference between tcp and udp": [
        {"label": "claimed TCP is connectionless", "patterns": ["tcp is connectionless"]},
        {"label": "claimed UDP guarantees ordered reliable delivery", "patterns": ["udp is reliable and ordered", "udp guarantees delivery"]},
    ],
}

GENERIC_REFERENCE_STOP_TERMS = {
    "strong", "answer", "concept", "topic", "practical", "practice", "interview", "ready",
    "important", "directly", "clearly", "detail", "example", "better", "good", "main",
    "should", "would", "could", "also", "because", "thing",
}


def tokenize(text):
    return re.findall(r"[a-zA-Z0-9+#*]+", str(text or "").lower())


def normalize_question_key(question):
    normalized = re.sub(r"\s+", " ", str(question or "").lower()).strip(" ?!.\n\t")
    return normalized


def split_sentences(text):
    return [segment.strip() for segment in re.split(r"[.!?]+", str(text or "")) if segment.strip()]


def unique_terms(values):
    return list(dict.fromkeys(value for value in values if value))


def count_phrase_hits(text, phrases):
    lowered = str(text or "").lower()
    return sum(1 for phrase in phrases if phrase in lowered)


def normalize_match_token(token):
    value = re.sub(r"[^a-zA-Z0-9+#*]+", "", str(token or "").lower())
    if len(value) > 4 and value.endswith("ies"):
        return value[:-3] + "y"
    if len(value) > 4 and value.endswith("es"):
        return value[:-2]
    if len(value) > 3 and value.endswith("s") and not value.endswith("ss"):
        return value[:-1]
    return value


def normalized_token_set(text):
    return {
        normalize_match_token(token)
        for token in tokenize(text)
        if normalize_match_token(token) and normalize_match_token(token) not in STOP_WORDS
    }


def expand_option_terms(option):
    normalized_option = str(option or "").lower().strip()
    values = [normalized_option]
    alias_values = KEYWORD_ALIASES.get(normalized_option, [])
    values.extend(alias_values)
    expanded = []
    for value in values:
        expanded.append(value)
        normalized_tokens = [normalize_match_token(token) for token in tokenize(value)]
        normalized_tokens = [token for token in normalized_tokens if token]
        if normalized_tokens:
            expanded.append(" ".join(normalized_tokens))
    return unique_terms(expanded)


def option_match_strength(text, option):
    lowered_text = str(text or "").lower()
    if not lowered_text or not option:
        return 0.0

    expanded_options = expand_option_terms(option)
    text_tokens = normalized_token_set(text)
    best = 0.0

    for candidate in expanded_options:
        if candidate in lowered_text:
            return 1.0

        option_tokens = normalized_token_set(candidate)
        if not option_tokens:
            continue

        overlap = len(option_tokens & text_tokens)
        token_ratio = overlap / len(option_tokens)

        if len(option_tokens) == 1:
            best = max(best, 1.0 if token_ratio >= 1.0 else 0.0)
        else:
            if token_ratio >= 1.0:
                return 1.0
            if token_ratio >= 0.75:
                best = max(best, 0.88)
            elif token_ratio >= 0.5:
                best = max(best, 0.62)

    return round(best, 2)


def group_match_details(text, sentences, group):
    best_score = 0.0
    best_evidence = ""
    for option in group:
        overall_score = option_match_strength(text, option)
        if overall_score > best_score:
            best_score = overall_score
            best_evidence = option
        for sentence in sentences:
            sentence_score = option_match_strength(sentence, option)
            if sentence_score > best_score:
                best_score = sentence_score
                best_evidence = sentence
    return {
        "score": round(best_score, 2),
        "passed": best_score >= 0.86,
        "partial": 0.45 <= best_score < 0.86,
        "evidence": best_evidence,
    }


def evaluate_point_match(transcript_lower, point):
    groups = point.get("groups", [])
    if not groups:
        return {"matched": False, "partial": False, "score": 0.0, "evidence": []}

    sentences = split_sentences(transcript_lower)
    group_results = [group_match_details(transcript_lower, sentences, group) for group in groups]
    passed_groups = sum(1 for item in group_results if item["passed"])
    partial_groups = sum(1 for item in group_results if item["partial"])
    coverage = sum(item["score"] for item in group_results) / max(1, len(group_results))
    matched = passed_groups == len(group_results)
    partial = not matched and (passed_groups + partial_groups) >= max(1, len(group_results) - 1) and coverage >= 0.55
    return {
        "matched": matched,
        "partial": partial,
        "score": round(coverage, 2),
        "evidence": [item["evidence"] for item in group_results if item["evidence"]][:2],
    }


def get_question_guidance(question):
    return QUESTION_GUIDANCE.get(normalize_question_key(question))


def evaluate_question_guidance(question, transcript_lower, question_type=None):
    guidance = get_question_guidance(question)
    if not guidance:
        return None

    matched = []
    partial = []
    missing = []
    incorrect = []
    point_details = []
    for point in guidance.get("points", []):
        point_result = evaluate_point_match(transcript_lower, point)
        point_details.append({
            "label": point["label"],
            "score": point_result["score"],
            "matched": point_result["matched"],
            "partial": point_result["partial"],
            "evidence": point_result["evidence"],
        })
        if point_result["matched"]:
            matched.append(point["label"])
        elif point_result["partial"]:
            partial.append(point["label"])
        else:
            missing.append(point["label"])

    for point in guidance.get("mistakes", []):
        mistake_result = evaluate_point_match(transcript_lower, point)
        if mistake_result["matched"] or mistake_result["partial"]:
            incorrect.append(point["label"])

    if question_type == "comparison":
        same_thing_patterns = [
            "same thing", "no difference", "exactly the same", "same as", "equivalent in every way",
        ]
        if any(pattern in transcript_lower for pattern in same_thing_patterns):
            incorrect.append("treated the compared concepts as if they were the same")

    total = len(guidance.get("points", []))
    point_score = sum(detail["score"] for detail in point_details) / max(1, total)
    score = round(max(0, min(100, (point_score * 100) - (8 * len(incorrect)))))
    return {
        "matched": matched,
        "partial": partial,
        "missing": missing,
        "incorrect": unique_terms(incorrect),
        "score": score,
        "point_details": point_details,
        "sample_answer": guidance.get("sample_answer", ""),
        "ideal_answer": guidance.get("ideal_answer", guidance.get("sample_answer", "")),
    }


def detect_question_contradictions(question, transcript_lower):
    contradictions = []
    patterns = QUESTION_CONTRADICTION_PATTERNS.get(normalize_question_key(question), [])
    lowered = str(transcript_lower or "").lower()
    for item in patterns:
        if item.get("regex_patterns"):
            if any(re.search(pattern, lowered) for pattern in item["regex_patterns"]):
                contradictions.append(item["label"])
        elif item.get("groups"):
            contradiction_match = evaluate_point_match(lowered, {"groups": item["groups"]})
            if contradiction_match["matched"] or contradiction_match["partial"]:
                contradictions.append(item["label"])
        elif any(pattern in lowered for pattern in item.get("patterns", [])):
            contradictions.append(item["label"])
    return unique_terms(contradictions)


def build_reference_alignment(reference_answer, transcript_lower, topic, question_keywords=None):
    reference_terms = []
    reference_terms.extend(extract_meaningful_terms(reference_answer or ""))
    reference_terms.extend(topic_reference_terms(topic))
    reference_terms.extend(question_keywords or [])
    filtered_terms = []
    for term in unique_terms(reference_terms):
        normalized = normalize_match_token(term)
        if not normalized or normalized in STOP_WORDS or normalized in QUESTION_NOISE_WORDS or normalized in GENERIC_REFERENCE_STOP_TERMS:
            continue
        filtered_terms.append(term)
    filtered_terms = filtered_terms[:14]
    if not filtered_terms:
        return {"score": 0, "matched": [], "partial": [], "missing": []}

    matched = []
    partial = []
    missing = []
    for term in filtered_terms:
        strength = option_match_strength(transcript_lower, term)
        if strength >= 0.86:
            matched.append(term)
        elif strength >= 0.45:
            partial.append(term)
        else:
            missing.append(term)

    score = round(min(100, ((len(matched) + (0.5 * len(partial))) / max(1, len(filtered_terms))) * 100))
    return {
        "score": score,
        "matched": matched[:6],
        "partial": partial[:4],
        "missing": missing[:6],
    }


def extract_question_keywords(question):
    keywords = []
    for token in tokenize(question):
        if len(token) < 3 or token in STOP_WORDS or token in QUESTION_NOISE_WORDS:
            continue
        keywords.append(token)
    return unique_terms(keywords)


def extract_meaningful_terms(text):
    terms = []
    for token in tokenize(text):
        if len(token) < 3 or token in STOP_WORDS or token in QUESTION_NOISE_WORDS:
            continue
        terms.append(token)
    return unique_terms(terms)


def extract_answer_subject(question):
    cleaned = re.sub(r"\s+", " ", str(question or "")).strip(" ?!.")
    lowered = cleaned.lower()
    prefixes = [
        "explain what ", "explain how ", "explain why ", "explain the difference between ",
        "explain ", "what is ", "what are ", "how does ", "how do ", "how would you ",
        "when would you ", "why is ", "why are ", "compare ", "describe ", "walk through ",
        "tell me about ",
    ]
    for prefix in prefixes:
        if lowered.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break
    cleaned = re.split(r"\s+and\s+(why|where|when|how)\b", cleaned, maxsplit=1, flags=re.IGNORECASE)[0].strip(" ,")
    cleaned = re.sub(r"\b(works|work|does|do)\b$", "", cleaned, flags=re.IGNORECASE).strip(" ,")
    cleaned = re.sub(r"\b(in simple terms|at a high level|briefly|clearly)$", "", cleaned, flags=re.IGNORECASE).strip(" ,")
    return cleaned or "the topic"


def clean_subject_for_answer(subject):
    cleaned = re.sub(r"\s+", " ", str(subject or "")).strip(" ,")
    cleaned = re.sub(r"^(the|a|an)\s+", "", cleaned, flags=re.IGNORECASE)
    return cleaned or "the concept"


def extract_comparison_subjects(question):
    lowered = re.sub(r"\s+", " ", str(question or "")).strip(" ?!.").lower()

    def split_subject_list(value):
        subjects = []
        for part in re.split(r",|\band\b", value):
            cleaned = re.sub(r"^(a|an|the)\s+", "", part.strip())
            for prefix in sorted(QUESTION_PREFIXES, key=len, reverse=True):
                cleaned = re.sub(rf"^{re.escape(prefix)}\s+", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\b(in detail|briefly|for interviews)$", "", cleaned).strip(" ,")
            if cleaned:
                subjects.append(cleaned)
        return subjects

    patterns = [
        r"difference between (.+?) and (.+)$",
        r"compare (.+?) and (.+)$",
        r"compare (.+?) with (.+)$",
        r"(.+?) differ(?:s)? from (.+)$",
        r"(.+?) vs\.? (.+)$",
        r"(.+?) versus (.+)$",
        r"difference between (.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, lowered)
        if not match:
            continue
        subjects = []
        for part in match.groups():
            subjects.extend(split_subject_list(part))
        subjects = unique_terms(subjects)
        if len(subjects) >= 2:
            return subjects[:3]
    return []


def extract_question_phrases(question, question_type):
    phrases = []
    comparison_subjects = extract_comparison_subjects(question)
    if comparison_subjects:
        phrases.extend(comparison_subjects)
    return unique_terms(phrases)


def detect_language_mode(transcript):
    transcript_text = str(transcript or "")
    transcript_lower = transcript_text.lower()
    devanagari_present = bool(re.search(r"[\u0900-\u097F]", transcript_text))
    romanized_hits = sum(1 for term in ROMANIZED_HINDI_TERMS if re.search(rf"\b{re.escape(term)}\b", transcript_lower))
    english_terms = len(re.findall(r"[a-zA-Z]{3,}", transcript_text))
    if devanagari_present and english_terms:
        return "mixed"
    if devanagari_present:
        return "other"
    if romanized_hits >= 2 and english_terms >= 4:
        return "mixed"
    if english_terms:
        return "english"
    return "other"


def build_language_feedback(language_mode):
    if language_mode == "mixed":
        return "Mixed language is okay for practice, but for a formal interview try giving the final answer in one language."
    if language_mode == "other":
        return "If the target interview is in English, rehearse the final version in English even if you first think through it in another language."
    return ""


def term_matches_transcript(term, transcript_lower):
    lowered_term = str(term or "").lower()
    if not lowered_term:
        return False
    if lowered_term in transcript_lower:
        return True
    aliases = KEYWORD_ALIASES.get(lowered_term, [])
    return any(alias in transcript_lower for alias in aliases)


def score_keyword_coverage(transcript_lower, keywords, phrases=None):
    candidates = unique_terms((phrases or []) + list(keywords or []))
    if not candidates:
        return 50, []
    matched = [candidate for candidate in candidates if term_matches_transcript(candidate, transcript_lower)]
    return round(min(100, (len(matched) / len(candidates)) * 100)), matched


def score_topic_relevance(transcript_lower, topic):
    hints = TOPIC_HINTS.get(str(topic or "").lower(), [])
    if not hints:
        return 50, []
    matched = [hint for hint in hints if hint in transcript_lower]
    return round(min(100, (len(matched) / len(hints)) * 125)), matched


def detect_question_type(question_lower):
    if any(term in question_lower for term in ["difference between", "compare", "versus", " vs ", " differ"]):
        return "comparison"
    if any(term in question_lower for term in ["advantages", "disadvantages", "pros and cons", "benefits", "drawbacks", "tradeoff"]):
        return "tradeoff"
    if any(term in question_lower for term in ["time complexity", "space complexity", "big o", "complexity"]):
        return "complexity"
    if any(term in question_lower for term in ["design a", "design an", "system design", "scalable", "architecture"]):
        return "design"
    if any(term in question_lower for term in ["when would you", "which would you choose", "which is better", "when should you"]):
        return "decision"
    if any(term in question_lower for term in ["how would", "how does", "how do", "implement", "compute", "work", "works"]):
        return "process"
    if question_lower.startswith(("what is", "what are", "define", "explain")):
        return "definition"
    return "concept"


def score_intent_alignment(transcript_lower, question_type):
    if question_type == "comparison":
        hits = count_phrase_hits(transcript_lower, COMPARISON_SIGNALS + TRADEOFF_SIGNALS)
        return min(100, 36 + hits * 16)
    if question_type == "tradeoff":
        hits = count_phrase_hits(transcript_lower, TRADEOFF_SIGNALS + DECISION_SIGNALS)
        return min(100, 34 + hits * 16)
    if question_type == "complexity":
        hits = count_phrase_hits(transcript_lower, ["o(", "big o", "complexity", "linear", "log", "constant", "quadratic", "memory", "space complexity"])
        return min(100, 34 + hits * 16)
    if question_type == "design":
        hits = count_phrase_hits(transcript_lower, DESIGN_SIGNALS + TRADEOFF_SIGNALS)
        return min(100, 30 + hits * 14)
    if question_type == "decision":
        hits = count_phrase_hits(transcript_lower, DECISION_SIGNALS + TRADEOFF_SIGNALS)
        return min(100, 34 + hits * 16)
    if question_type == "process":
        hits = count_phrase_hits(transcript_lower, PROCESS_SIGNALS + RESULT_SIGNALS)
        return min(100, 30 + hits * 16)
    if question_type == "definition":
        hits = count_phrase_hits(transcript_lower, DEFINITION_SIGNALS + EXAMPLE_SIGNALS)
        return min(100, 36 + hits * 14)
    hits = count_phrase_hits(transcript_lower, EXAMPLE_SIGNALS + TRADEOFF_SIGNALS)
    return min(100, 42 + hits * 12)


def score_technical_depth(transcript_lower, word_count):
    if word_count == 0:
        return 0, 0
    hits = sum(1 for term in TECHNICAL_SIGNAL_TERMS if term in transcript_lower)
    density = hits / max(1, word_count / 25)
    return round(min(100, 28 + density * 20)), hits


def score_delivery(transcript, duration, difficulty):
    transcript_lower = transcript.lower()
    words = re.findall(r"\b\w+\b", transcript_lower)
    word_count = len(words)
    unique_words = len(set(words))
    filler_words = [
        "um", "uh", "like", "basically", "actually", "literally", "just", "maybe", "so",
        "well", "okay", "right", "honestly", "seriously", "stuff", "things",
    ]
    filler_phrases = ["you know", "i mean", "kind of", "sort of", "a little bit", "to be honest"]
    filler_used = [word for word in words if word in filler_words]
    phrase_used = [phrase for phrase in filler_phrases if phrase in transcript_lower]
    filler_list = filler_used + phrase_used
    filler_count = len(filler_list)
    wpm = round((word_count / duration) * 60, 2) if duration > 0 else 0
    diversity_ratio = unique_words / word_count if word_count > 0 else 0
    diversity_score = min(100, diversity_ratio * 150)
    sentence_count = len(split_sentences(transcript))
    structure_score = min(100, sentence_count * 20)
    filler_ratio = filler_count / word_count if word_count > 0 else 0
    filler_score = max(0, 100 - filler_ratio * 250)
    ideal_wpm = 140
    speed_score = 0 if wpm == 0 else max(0, 100 - abs(wpm - ideal_wpm))
    length_score = min(100, word_count * 2)
    delivery_score = round(
        (0.35 * filler_score) + (0.25 * speed_score) + (0.20 * diversity_score) +
        (0.10 * structure_score) + (0.10 * length_score)
    )
    if duration < 15 or word_count < 15:
        delivery_score = max(20, delivery_score - 25)
    elif wpm > 180:
        delivery_score = max(30, delivery_score - 20)
    elif wpm < 80:
        delivery_score = max(25, delivery_score - 15)
    elif duration > 90 or word_count > 200:
        delivery_score = max(40, delivery_score - 10)
    return {
        "transcript_lower": transcript_lower,
        "word_count": word_count,
        "wpm": wpm,
        "filler_count": filler_count,
        "filler_list": filler_list,
        "delivery_score": delivery_score,
        "structure_score": round(structure_score),
    }


def assess_answer_structure(question, transcript, question_type, question_keywords, technical_hits):
    transcript_lower = str(transcript or "").lower()
    sentences = split_sentences(transcript)
    first_sentence = sentences[0].lower() if sentences else ""
    transcript_terms = set(extract_meaningful_terms(transcript))
    comparison_subjects = extract_comparison_subjects(question)
    covered = []
    missing = []
    checks = 0

    def expect(covered_label, passed, missing_label):
        nonlocal checks
        checks += 1
        if passed:
            covered.append(covered_label)
        else:
            missing.append(missing_label)

    if question_type == "comparison":
        if comparison_subjects:
            both_sides = all(
                subject in transcript_lower or any(term in transcript_terms for term in extract_meaningful_terms(subject))
                for subject in comparison_subjects
            )
        else:
            both_sides = len(transcript_terms.intersection(set(question_keywords))) >= 2
        expect("named both sides", both_sides, "define both sides before comparing")
        expect(
            "stated the main difference",
            count_phrase_hits(transcript_lower, COMPARISON_SIGNALS) >= 1,
            "state the main difference directly",
        )
        expect(
            "added a tradeoff or use case",
            count_phrase_hits(transcript_lower, TRADEOFF_SIGNALS + DECISION_SIGNALS + EXAMPLE_SIGNALS) >= 1,
            "mention one use case or tradeoff",
        )
    elif question_type == "tradeoff":
        expect(
            "covered the upside",
            any(term in transcript_lower for term in ["advantage", "benefit", "pro", "helps", "good for"]),
            "state at least one advantage",
        )
        expect(
            "covered the downside",
            any(term in transcript_lower for term in ["disadvantage", "drawback", "con", "limitation", "cost", "risk"]),
            "state at least one downside",
        )
        expect(
            "explained when to use it",
            count_phrase_hits(transcript_lower, DECISION_SIGNALS + EXAMPLE_SIGNALS) >= 1,
            "say when you would choose it",
        )
    elif question_type == "complexity":
        expect(
            "named the time complexity",
            any(term in transcript_lower for term in ["time complexity", "big o", "o(", "linear", "constant", "log", "quadratic"]),
            "mention the time complexity clearly",
        )
        expect(
            "named the space cost",
            any(term in transcript_lower for term in ["space complexity", "memory", "extra space", "in place", "in-place"]),
            "mention the space or memory impact",
        )
        expect(
            "connected the complexity to the approach",
            technical_hits > 0 or count_phrase_hits(transcript_lower, PROCESS_SIGNALS) >= 1,
            "explain why the complexity comes from that approach",
        )
    elif question_type == "design":
        expect(
            "identified the main components",
            count_phrase_hits(transcript_lower, DESIGN_SIGNALS) >= 2,
            "name the main components first",
        )
        expect(
            "mentioned scale or reliability",
            any(term in transcript_lower for term in ["scale", "latency", "availability", "consistency", "throughput", "failure", "bottleneck"]),
            "mention scale, reliability, or bottlenecks",
        )
        expect(
            "called out a tradeoff",
            count_phrase_hits(transcript_lower, TRADEOFF_SIGNALS + DECISION_SIGNALS) >= 1,
            "call out at least one tradeoff",
        )
    elif question_type == "decision":
        expect(
            "made a recommendation",
            any(term in transcript_lower for term in ["choose", "prefer", "use", "better", "best"]),
            "make a clear recommendation",
        )
        expect(
            "explained the condition",
            any(term in transcript_lower for term in ["when", "if", "depends", "based on", "in that case"]),
            "explain the condition behind your choice",
        )
        expect(
            "mentioned a tradeoff",
            count_phrase_hits(transcript_lower, TRADEOFF_SIGNALS) >= 1,
            "mention the tradeoff behind the choice",
        )
    elif question_type == "process":
        expect(
            "opened with the core idea",
            any(keyword in first_sentence for keyword in question_keywords[:2]) or count_phrase_hits(first_sentence, DEFINITION_SIGNALS) >= 1,
            "open with the goal or core idea first",
        )
        expect(
            "walked through steps in order",
            count_phrase_hits(transcript_lower, PROCESS_SIGNALS) >= 2 or len(sentences) >= 3,
            "walk through the steps in order",
        )
        expect(
            "closed with a result or example",
            count_phrase_hits(transcript_lower, EXAMPLE_SIGNALS + RESULT_SIGNALS) >= 1,
            "add a result, example, or final outcome",
        )
    else:
        expect(
            "opened with a direct explanation",
            count_phrase_hits(first_sentence, DEFINITION_SIGNALS) >= 1 or any(keyword in first_sentence for keyword in question_keywords[:2]),
            "start with a direct definition or answer",
        )
        expect(
            "added one technical detail",
            technical_hits > 0 or len(transcript_terms.intersection(set(question_keywords))) >= 2,
            "add one technical detail that proves understanding",
        )
        expect(
            "used an example or tradeoff",
            count_phrase_hits(transcript_lower, EXAMPLE_SIGNALS + TRADEOFF_SIGNALS + DECISION_SIGNALS) >= 1,
            "finish with a short example or tradeoff",
        )

    return {
        "score": round((len(covered) / max(1, checks)) * 100),
        "covered": covered,
        "missing": unique_terms(missing),
    }


def assess_response_validity(question, transcript, word_count, keyword_coverage, topic_relevance, technical_depth):
    transcript_lower = str(transcript or "").lower().strip()
    question_lower = str(question or "").lower().strip(" ?!.")
    question_terms = set(extract_question_keywords(question))
    transcript_terms = extract_meaningful_terms(transcript)
    transcript_term_set = set(transcript_terms)
    novel_terms = [term for term in transcript_terms if term not in question_terms]
    overlap = transcript_term_set & question_terms
    union = transcript_term_set | question_terms
    similarity = len(overlap) / max(1, len(union))
    repeated_prompt = bool(question_lower) and question_lower in transcript_lower
    vague_hits = sum(1 for term in VAGUE_TERMS if re.search(rf"\b{re.escape(term)}\b", transcript_lower))

    if word_count < 8 or len(transcript_term_set) < 3:
        return {
            "label": "insufficient",
            "reason": "No meaningful answer detected yet. Try answering in your own words with one clear explanation.",
            "similarity": round(similarity, 2),
            "novel_terms": novel_terms[:6],
        }
    if repeated_prompt and len(novel_terms) < 3:
        return {
            "label": "insufficient",
            "reason": "The response mostly repeated the prompt instead of answering it. Try giving the explanation in your own words.",
            "similarity": round(similarity, 2),
            "novel_terms": novel_terms[:6],
        }
    if similarity >= 0.68 and len(novel_terms) < 3:
        return {
            "label": "insufficient",
            "reason": "The answer is too close to the question wording. Add your own explanation, one detail, and a short example.",
            "similarity": round(similarity, 2),
            "novel_terms": novel_terms[:6],
        }
    if word_count >= 12 and keyword_coverage < 18 and topic_relevance < 20 and technical_depth < 26:
        return {
            "label": "off_topic",
            "reason": "The response did not land on the core topic yet. Re-anchor the answer to the exact concept in the question.",
            "similarity": round(similarity, 2),
            "novel_terms": novel_terms[:6],
        }
    if word_count >= 10 and vague_hits >= 3 and technical_depth < 42:
        return {
            "label": "vague",
            "reason": "The answer stays too generic. Replace vague words with one concrete concept, detail, or example.",
            "similarity": round(similarity, 2),
            "novel_terms": novel_terms[:6],
        }
    if len(novel_terms) < 3 and technical_depth < 35 and keyword_coverage < 32:
        return {
            "label": "vague",
            "reason": "The answer needs more original substance. Add one technical detail and one example in your own words.",
            "similarity": round(similarity, 2),
            "novel_terms": novel_terms[:6],
        }
    return {
        "label": "valid",
        "reason": "",
        "similarity": round(similarity, 2),
        "novel_terms": novel_terms[:6],
    }


def join_phrases(values):
    values = [value for value in values if value]
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return f"{', '.join(values[:-1])}, and {values[-1]}"


def display_term(value):
    if str(value or "").isupper():
        return value
    if str(value or "").lower() in {"bfs", "dfs", "dbms", "oops", "genai", "bst", "api"}:
        return str(value).upper()
    return str(value)


def expected_concepts(question_keywords, question_phrases, topic, question_type):
    topic_hints = TOPIC_HINTS.get(str(topic or "").lower(), [])
    concepts = []
    concepts.extend(question_phrases[:2])
    concepts.extend(question_keywords[:3])
    if question_type == "comparison":
        concepts.extend(["difference", "tradeoff"])
    elif question_type == "tradeoff":
        concepts.extend(["advantage", "disadvantage"])
    elif question_type == "complexity":
        concepts.extend(["time complexity", "space complexity"])
    elif question_type == "design":
        concepts.extend(["components", "tradeoff"])
    elif question_type == "decision":
        concepts.extend(["condition", "tradeoff"])
    elif question_type == "process":
        concepts.extend(["steps", "example"])
    else:
        concepts.extend(["example", "technical detail"])
    if len(question_keywords) + len(question_phrases) <= 1:
        concepts.extend(topic_hints[:1])
    return unique_terms(concepts)


def build_missing_concepts(question_keywords, question_phrases, matched_keywords, topic, question_type, transcript_lower, structure_result, guidance_result=None):
    if guidance_result is not None:
        return guidance_result["missing"][:4]

    matched_set = {str(term).lower() for term in matched_keywords}
    missing = []
    ignored = {"difference", "tradeoff", "advantage", "disadvantage", "components", "condition", "steps", "example", "technical detail"}
    topic_lower = str(topic or "").lower()
    topic_variants = {topic_lower, topic_lower.rstrip("s"), f"{topic_lower}s"} if topic_lower else set()
    for concept in expected_concepts(question_keywords, question_phrases, topic, question_type):
        lowered = str(concept).lower()
        if lowered in ignored or lowered in topic_variants:
            continue
        if lowered not in matched_set and not term_matches_transcript(lowered, transcript_lower):
            missing.append(display_term(concept))
    return unique_terms(missing)[:4]


def build_correctness_result(
    question_type,
    keyword_coverage,
    topic_relevance,
    intent_alignment,
    structure_result,
    guidance_result,
    reference_alignment,
    missing_points,
    contradiction_points,
    response_validity,
):
    if response_validity["label"] != "valid":
        return {
            "score": 18,
            "verdict": "unclear",
            "summary": response_validity["reason"],
            "covered_points": [],
            "missing_points": missing_points[:4],
            "incorrect_points": contradiction_points[:3],
            "improvement_steps": [
                "Answer the question in your own words.",
                "State the core idea first.",
                "Add one concrete detail or example.",
            ],
        }

    if guidance_result:
        covered_points = guidance_result["matched"][:4]
        if guidance_result.get("partial"):
            covered_points.extend([f"Partially covered: {item}" for item in guidance_result["partial"][:2]])
        if reference_alignment.get("partial"):
            covered_points.extend([f"Reference overlap: {item}" for item in reference_alignment["partial"][:1]])
        incorrect_points = unique_terms(guidance_result["incorrect"] + contradiction_points)[:3]
        base_score = round(
            (0.62 * guidance_result["score"]) +
            (0.14 * structure_result["score"]) +
            (0.10 * keyword_coverage) +
            (0.14 * reference_alignment["score"])
        )
    else:
        covered_points = structure_result["covered"][:4]
        if reference_alignment.get("matched"):
            covered_points.extend([f"Reference overlap: {item}" for item in reference_alignment["matched"][:2]])
        incorrect_points = contradiction_points[:3]
        base_score = round(
            (0.30 * keyword_coverage) +
            (0.20 * topic_relevance) +
            (0.18 * intent_alignment) +
            (0.20 * structure_result["score"]) +
            (0.12 * reference_alignment["score"])
        )

    score = max(0, min(100, base_score - (18 * len(incorrect_points))))

    if incorrect_points and score < 55:
        verdict = "incorrect"
    elif incorrect_points or score < 55:
        verdict = "partially_correct"
    elif score < 76:
        verdict = "mostly_correct"
    else:
        verdict = "correct"

    if verdict == "correct":
        summary = "Correct. The answer covered the expected points clearly and stayed aligned with the question."
    elif verdict == "mostly_correct":
        if guidance_result and guidance_result.get("partial"):
            summary = f"Mostly correct. The answer is on track, but points like {join_phrases(guidance_result['partial'][:2])} need more depth or precision."
        elif missing_points:
            summary = f"Mostly correct. You covered the main idea, but you still missed {join_phrases(missing_points[:2])}."
        else:
            summary = "Mostly correct. The answer is solid, but it still needs a little more precision to feel complete."
    elif verdict == "partially_correct":
        if incorrect_points:
            summary = f"Partially correct. Some of the answer is on track, but it also {join_phrases(incorrect_points[:2])}."
        elif missing_points:
            summary = f"Partially correct. The answer touches the right topic, but it is missing {join_phrases(missing_points[:2])}."
        else:
            summary = "Partially correct. The answer needs more complete reasoning to sound reliable."
    else:
        summary = "Incorrect. The answer does not yet capture the key idea accurately enough."

    improvement_steps = build_improvement_steps(
        question_type,
        missing_points,
        incorrect_points,
        structure_result,
        "",
    )

    return {
        "score": score,
        "verdict": verdict,
        "summary": summary,
        "covered_points": covered_points,
        "missing_points": missing_points[:4],
        "incorrect_points": incorrect_points,
        "improvement_steps": improvement_steps[:3],
    }


def build_improvement_steps(question_type, missing_points, incorrect_points, structure_result, language_feedback):
    steps = []

    for incorrect_point in incorrect_points[:2]:
        steps.append(f"Correct this first: {incorrect_point}.")

    for missing_point in missing_points[:2]:
        steps.append(f"Add this clearly: {missing_point}.")

    if structure_result["missing"]:
        steps.append(structure_result["missing"][0].capitalize() + ".")
    elif question_type == "comparison":
        steps.append("State the biggest difference in one direct sentence before adding details.")
    elif question_type == "process":
        steps.append("Walk through the steps in order instead of mixing the explanation.")
    elif question_type == "design":
        steps.append("Start with the main components, then explain the request flow and one tradeoff.")
    elif question_type == "tradeoff":
        steps.append("Name both the benefit and the drawback so the answer sounds balanced.")
    elif question_type == "complexity":
        steps.append("Mention both time and space cost, then explain why that complexity occurs.")
    else:
        steps.append("Open with a direct definition, then add one technical detail and one short use case.")

    if language_feedback:
        steps.append(language_feedback)

    return unique_terms(steps)[:4]


def topic_reference_terms(topic):
    return TOPIC_REFERENCE_TERMS.get(str(topic or "").lower(), [])


def fallback_reference_points(topic, question_type, missing_concepts, matched_keywords):
    points = []
    points.extend([display_term(item) for item in matched_keywords[:2]])
    points.extend([display_term(item) for item in missing_concepts[:2]])
    points.extend(topic_reference_terms(topic)[:2])
    return unique_terms(points)[:4]


def build_reference_answer(subject, question_type, topic, missing_concepts, comparison_subjects, matched_keywords):
    subject = clean_subject_for_answer(subject)
    points = fallback_reference_points(topic, question_type, missing_concepts, matched_keywords)
    first_point = display_term(points[0]) if points else "the core idea"
    second_point = display_term(points[1]) if len(points) > 1 else "one technical detail"
    third_point = display_term(points[2]) if len(points) > 2 else "a practical use case"

    if question_type == "comparison" and comparison_subjects:
        left = comparison_subjects[0]
        right = comparison_subjects[1]
        extra = join_phrases(comparison_subjects[2:]) if len(comparison_subjects) > 2 else ""
        extra_tail = f", and {extra}" if extra else ""
        return (
            f"{left.capitalize()}, {right}{extra_tail} are related, but they are not the same thing. "
            f"The clearest way to answer is to define each one briefly, state the biggest difference directly, and then explain when each option is the better fit in practice."
        )

    if question_type == "comparison":
        return (
            f"{subject.capitalize()} should be answered by defining both sides first, then stating the main difference directly. "
            f"After that, the answer should explain when each option is the better fit so it sounds practical instead of vague."
        )

    if question_type == "process":
        return (
            f"{subject.capitalize()} works as a sequence rather than a one-line fact. "
            f"A strong answer would start with the goal, walk through the main steps in order, and finish with the result or one concrete example."
        )

    if question_type == "design":
        return (
            f"For {subject}, a strong answer starts with the goal of the system, then names the main components and the request flow. "
            f"It should also call out one important scaling, reliability, or cost tradeoff to show engineering judgment."
        )

    if question_type == "tradeoff":
        return (
            f"{subject.capitalize()} should be explained as a tradeoff, not just a definition. "
            f"A good answer states the main benefit first, then the limitation, and ends with when it is the better choice in practice."
        )

    if question_type == "complexity":
        return (
            f"{subject.capitalize()} should be explained together with the cost of the approach. "
            f"A strong answer states the time or space complexity directly and then explains why that cost comes from the algorithm or data structure."
        )

    return (
        f"{subject.capitalize()} is a concept in {topic or 'the topic'} that should be explained directly first. "
        f"A better answer would define it clearly, mention {second_point.lower()}, and connect it to {third_point.lower()} so it sounds concrete and interview ready."
    )


def build_ideal_answer(subject, question_type, topic, missing_concepts, comparison_subjects, matched_keywords):
    subject = clean_subject_for_answer(subject)
    topic_terms = topic_reference_terms(topic)
    detail_phrase = join_phrases([display_term(item) for item in topic_terms[:2]])

    if question_type == "comparison" and comparison_subjects:
        subject_phrase = join_phrases(comparison_subjects[:3])
        return (
            f"{subject_phrase.capitalize()} should be explained by defining each concept clearly, then stating the main difference in scope, behavior, or use case. "
            f"A strong answer would also mention the practical tradeoff and when each one is the better choice."
        )

    if question_type == "process":
        return (
            f"A strong answer on {subject} would begin with the goal, explain the steps in order, and then connect the process to {detail_phrase or 'the final result and one practical example'}. "
            f"The key is to make the explanation sequential, concrete, and technically grounded."
        )

    if question_type == "design":
        return (
            f"A strong answer on {subject} would identify the main components, explain how requests move through the system, and then discuss {detail_phrase or 'one important scaling, consistency, or reliability tradeoff'}. "
            f"That makes the design answer structured and realistic."
        )

    if question_type == "tradeoff":
        return (
            f"A strong answer on {subject} would describe the upside, the downside, and the condition under which you would choose it. "
            f"The goal is to sound balanced and practical instead of one-sided."
        )

    if question_type == "complexity":
        return (
            f"A strong answer on {subject} would name the time and space complexity, then explain why the algorithm or data structure has that cost. "
            f"If possible, it should also mention when that tradeoff is acceptable in practice."
        )

    return (
        f"A strong answer on {subject} would define the concept precisely, add one or two technical details such as {detail_phrase or 'the internal behavior or tradeoff'}, and end with a concrete use case or impact. "
        f"That makes the answer sound accurate, grounded, and interview ready."
    )


def determine_answer_quality(content_score, keyword_coverage, word_count, structure_score, correctness_score):
    if word_count < 8 or content_score < 42:
        return "needs work"
    if structure_score < 34 and correctness_score < 40:
        return "needs work"
    if keyword_coverage < 30 and content_score < 55:
        return "needs work"
    if correctness_score < 55:
        return "needs work"
    if content_score < 74 or keyword_coverage < 58 or structure_score < 60 or correctness_score < 76:
        return "partial"
    return "strong"


def build_feedback(content_score, delivery_score, question_type, matched_keywords, structure_result, technical_depth, language_feedback, guidance_result=None):
    strengths = []
    improvements = []
    if matched_keywords:
        shown_terms = [display_term(term) for term in matched_keywords[:3]]
        strengths.append(f"You covered key terms like {', '.join(shown_terms)}.")
    if guidance_result and guidance_result["matched"]:
        strengths.append(f"You covered important points like {join_phrases(guidance_result['matched'][:2])}.")
    if structure_result["score"] >= 66:
        strengths.append(f"The answer followed a clear {question_type} structure.")
    if technical_depth >= 64:
        strengths.append("You added technical detail instead of staying generic.")
    if content_score < 70:
        improvements.append("Answer the core question more directly before adding side details.")
    if structure_result["missing"]:
        improvements.append(structure_result["missing"][0].capitalize() + ".")
    if delivery_score < 70:
        improvements.append("Tighten pacing and reduce filler so the answer sounds more deliberate.")
    if language_feedback:
        improvements.append(language_feedback)
    return strengths[:3], improvements[:3]


def build_answer_quality_summary(quality_label, question_type, missing_concepts):
    if quality_label == "retry":
        return "No meaningful answer was detected yet. Try again with a direct explanation in your own words."
    if quality_label == "strong":
        return "This answer covered the core concept, followed a usable structure, and sounded close to interview ready."
    if quality_label == "partial":
        if missing_concepts:
            return f"The answer is on the right track, but it would feel more complete if you added {join_phrases(missing_concepts[:2])}."
        return "The answer is on the right track, but it needs one more layer of detail to feel complete."
    if missing_concepts:
        return f"The answer touched the topic, but it still needs {join_phrases(missing_concepts[:2])} to sound convincing."
    if question_type == "process":
        return "The answer needs a clearer step-by-step explanation before it will sound convincing."
    return "The answer needs a more direct explanation of the core concept before expanding further."


def build_sample_answer(subject, question_type, topic, missing_concepts, comparison_subjects, matched_keywords=None, guidance_result=None):
    if guidance_result and guidance_result.get("sample_answer"):
        return guidance_result["sample_answer"]

    return build_reference_answer(
        subject,
        question_type,
        topic,
        missing_concepts,
        comparison_subjects,
        matched_keywords or [],
    )


def build_retry_sample_answer(subject, question_type, response_validity, comparison_subjects=None):
    if response_validity == "off_topic":
        return f"Try again by naming the exact concept in {subject} first, then explain one technical detail that is directly tied to the question."
    if response_validity == "vague":
        return f"Try again by answering {subject} in one direct sentence, then add one concrete concept and one short example instead of generic wording."
    if question_type == "comparison":
        if comparison_subjects:
            subject_phrase = join_phrases(comparison_subjects[:3])
            return f"Try again by first defining {subject_phrase}, then state the biggest difference between them, and end with when you would choose each one."
        return (
            f"Try again by first defining both sides of {subject}, then state the biggest difference between them, and end with when you would choose each one."
        )
    if question_type == "process":
        return f"Try again by stating the goal of {subject}, then explain the steps in order, and finish with one example."
    if question_type == "complexity":
        return f"Try again by explaining {subject} directly, then mention the time or space complexity, and finish with one tradeoff."
    return f"Try again by defining {subject} directly, then explain one important detail, and end with a short example in your own words."


def build_time_target_result(duration, target_seconds):
    try:
        target_value = int(target_seconds or 0)
    except (TypeError, ValueError):
        target_value = 0

    if target_value <= 0:
        return {
            "target_seconds": 0,
            "delta_seconds": 0,
            "status": "not_set",
            "score": 50,
            "summary": "No target time was set for this answer.",
        }

    duration_value = float(duration or 0)
    delta_seconds = round(duration_value - target_value, 2)
    tolerance = max(8, round(target_value * 0.12))
    deviation_ratio = abs(delta_seconds) / max(target_value, 1)
    score = max(0, min(100, round(100 - (deviation_ratio * 100))))

    if abs(delta_seconds) <= tolerance:
        status = "on_target"
        summary = f"Time target hit cleanly. The answer finished within {tolerance}s of the {target_value}s target."
    elif delta_seconds < 0:
        status = "under"
        summary = f"The answer wrapped {abs(delta_seconds):.1f}s early against the {target_value}s target."
    else:
        status = "over"
        summary = f"The answer ran {delta_seconds:.1f}s over the {target_value}s target."

    return {
        "target_seconds": target_value,
        "delta_seconds": delta_seconds,
        "status": status,
        "score": score,
        "summary": summary,
    }


def determine_delivery_only_quality(overall_score, delivery_score, structure_score, time_target_score, response_validity_label):
    if response_validity_label == "insufficient":
        return "retry"
    if overall_score >= 78 and delivery_score >= 72 and structure_score >= 62 and time_target_score >= 60:
        return "strong"
    if overall_score >= 58:
        return "partial"
    return "needs work"


def build_delivery_only_summary(quality_label, time_target_result):
    if quality_label == "strong":
        return "Strong delivery round. The answer sounded controlled, structured, and reasonably well timed."
    if quality_label == "partial":
        return f"Usable delivery baseline. {time_target_result['summary']}"
    if quality_label == "retry":
        return "The response was too thin to judge well yet. Try again with a clearer spoken answer."
    return f"The response needs stronger delivery discipline. {time_target_result['summary']}"


def build_delivery_only_feedback(delivery_score, structure_result, filler_count, wpm, time_target_result, response_validity):
    strengths = []
    improvements = []

    if delivery_score >= 72:
        strengths.append("Your delivery sounded controlled and confident.")
    if structure_result["score"] >= 62:
        strengths.append("The answer had a usable structure instead of sounding scattered.")
    if filler_count <= 3:
        strengths.append("Filler usage stayed low enough to keep the answer cleaner.")
    if time_target_result["status"] == "on_target":
        strengths.append("You stayed close to the target time for this question.")

    if response_validity["label"] != "valid":
        improvements.append(response_validity["reason"])
    if filler_count > 5:
        improvements.append("Reduce filler words and replace them with short pauses.")
    if wpm > 170:
        improvements.append("Slow down slightly so the answer sounds easier to follow.")
    elif wpm < 105:
        improvements.append("Add a bit more pace so the answer sounds more confident.")
    if structure_result["score"] < 55:
        improvements.append("Open with the direct answer, then move through one or two clear points.")
    if time_target_result["status"] == "under":
        improvements.append("Stay with the answer a little longer and add one concrete supporting detail.")
    elif time_target_result["status"] == "over":
        improvements.append("Trim repetition so the answer lands inside the target time.")

    if not strengths:
        strengths.append("The system captured enough speech to give a delivery readout.")

    if not improvements:
        improvements.append("Keep the same pacing and structure on the next answer.")

    return strengths[:4], improvements[:4]


def analyze_transcript(
    transcript,
    duration,
    difficulty="medium",
    topic="",
    question="",
    sample_answer="",
    ideal_answer="",
    analytics_mode="full",
    target_seconds=0,
    question_weight=None,
):
    delivery = score_delivery(transcript, duration, difficulty)
    transcript_lower = delivery["transcript_lower"]
    question_lower = str(question or "").lower()
    provided_sample_answer = str(sample_answer or "").strip()
    provided_ideal_answer = str(ideal_answer or "").strip()
    reference_source = "database" if provided_ideal_answer or provided_sample_answer else "generated"
    question_type = detect_question_type(question_lower)
    question_keywords = extract_question_keywords(question)
    question_phrases = extract_question_phrases(question, question_type)
    guidance_result = evaluate_question_guidance(question, transcript_lower, question_type)
    contradiction_points = detect_question_contradictions(question, transcript_lower)
    keyword_coverage, matched_keywords = score_keyword_coverage(transcript_lower, question_keywords, question_phrases)
    topic_relevance, matched_topic_terms = score_topic_relevance(transcript_lower, topic)
    technical_depth, technical_hits = score_technical_depth(transcript_lower, delivery["word_count"])
    intent_alignment = score_intent_alignment(transcript_lower, question_type)
    structure_result = assess_answer_structure(question, transcript, question_type, question_keywords, technical_hits)
    reference_answer = provided_ideal_answer or provided_sample_answer
    if not reference_answer and guidance_result:
        reference_answer = guidance_result.get("ideal_answer") or guidance_result.get("sample_answer") or ""
    reference_alignment = build_reference_alignment(reference_answer, transcript_lower, topic, question_keywords)
    language_mode = detect_language_mode(transcript)
    language_feedback = build_language_feedback(language_mode)
    hedging_hits = sum(1 for term in HEDGING_TERMS if term in transcript_lower)
    hedging_penalty = min(14, hedging_hits * 3)
    response_validity = assess_response_validity(
        question, transcript, delivery["word_count"], keyword_coverage, topic_relevance, technical_depth
    )

    try:
        parsed_question_weight = float(question_weight)
    except (TypeError, ValueError):
        parsed_question_weight = 0

    resolved_weight = parsed_question_weight if parsed_question_weight > 0 else DIFFICULTY_WEIGHTS.get(difficulty, 25)

    if analytics_mode == "delivery_only":
        time_target_result = build_time_target_result(duration, target_seconds)
        focus_score = round((0.60 * keyword_coverage) + (0.40 * structure_result["score"]))
        content_score = max(0, min(100, focus_score - hedging_penalty))
        overall_score = round(
            (0.56 * delivery["delivery_score"]) +
            (0.24 * content_score) +
            (0.20 * time_target_result["score"])
        )
        strengths, improvements = build_delivery_only_feedback(
            delivery["delivery_score"],
            structure_result,
            delivery["filler_count"],
            delivery["wpm"],
            time_target_result,
            response_validity,
        )
        quality_label = determine_delivery_only_quality(
            overall_score,
            delivery["delivery_score"],
            structure_result["score"],
            time_target_result["score"],
            response_validity["label"],
        )
        quality_summary = build_delivery_only_summary(quality_label, time_target_result)

        return {
            "transcript": transcript,
            "word_count": delivery["word_count"],
            "filler_words": delivery["filler_count"],
            "filler_list": delivery["filler_list"],
            "duration": round(duration, 2),
            "wpm": delivery["wpm"],
            "confidence": overall_score,
            "overall_score": overall_score,
            "delivery_score": delivery["delivery_score"],
            "content_score": content_score,
            "keyword_coverage": keyword_coverage,
            "topic_relevance": topic_relevance,
            "intent_alignment": round(intent_alignment),
            "technical_depth": technical_depth,
            "answer_structure_score": structure_result["score"],
            "covered_answer_elements": structure_result["covered"],
            "correctness_score": time_target_result["score"],
            "correctness_verdict": time_target_result["status"],
            "correctness_summary": time_target_result["summary"],
            "covered_points": strengths,
            "missing_points": [],
            "incorrect_points": [],
            "improvement_steps": improvements,
            "question_keywords": question_keywords,
            "question_phrases": question_phrases,
            "matched_keywords": matched_keywords,
            "matched_topic_terms": matched_topic_terms,
            "technical_hits": technical_hits,
            "question_type": question_type,
            "question_guidance_score": None,
            "guided_points_covered": [],
            "guided_points_partial": [],
            "guided_point_details": [],
            "reference_alignment_score": 0,
            "reference_alignment_matched": [],
            "reference_alignment_partial": [],
            "contradiction_points": [],
            "response_validity": response_validity["label"],
            "response_validity_reason": response_validity["reason"],
            "question_similarity": response_validity["similarity"],
            "novel_terms_detected": response_validity["novel_terms"],
            "language_mode": language_mode,
            "language_feedback": language_feedback,
            "strengths": strengths,
            "improvements": improvements,
            "answer_quality_label": quality_label,
            "answer_quality_summary": quality_summary,
            "missing_concepts": [],
            "sample_answer": "",
            "ideal_answer": "",
            "reference_source": "none",
            "difficulty": difficulty,
            "weight": resolved_weight,
            "analytics_mode": "delivery_only",
            "time_target_seconds": time_target_result["target_seconds"],
            "time_target_delta_seconds": time_target_result["delta_seconds"],
            "time_target_status": time_target_result["status"],
            "time_target_score": time_target_result["score"],
        }

    missing_concepts = build_missing_concepts(
        question_keywords, question_phrases, matched_keywords, topic, question_type, transcript_lower, structure_result, guidance_result
    )
    correctness_result = build_correctness_result(
        question_type,
        keyword_coverage,
        topic_relevance,
        intent_alignment,
        structure_result,
        guidance_result,
        reference_alignment,
        missing_concepts,
        contradiction_points,
        response_validity,
    )
    if response_validity["label"] == "valid":
        correctness_result["improvement_steps"] = build_improvement_steps(
            question_type,
            correctness_result["missing_points"],
            correctness_result["incorrect_points"],
            structure_result,
            language_feedback,
        )

    content_score = round(
        (0.48 * correctness_result["score"]) +
        (0.16 * keyword_coverage) +
        (0.12 * topic_relevance) +
        (0.12 * intent_alignment) +
        (0.12 * structure_result["score"])
    )
    content_score = max(0, min(100, content_score - hedging_penalty))
    overall_score = round((0.52 * delivery["delivery_score"]) + (0.48 * content_score))
    subject = extract_answer_subject(question)
    comparison_subjects = extract_comparison_subjects(question)
    strengths, improvements = build_feedback(
        content_score, delivery["delivery_score"], question_type, matched_keywords, structure_result, technical_depth, language_feedback, guidance_result
    )

    if response_validity["label"] != "valid":
        content_score = min(content_score, 20)
        overall_score = min(overall_score, 28)
        strengths = []
        improvements = [
            response_validity["reason"],
            "Start with the direct answer instead of circling around the prompt.",
            "Add one concrete detail or example before moving on.",
        ]
        missing_concepts = correctness_result["missing_points"][:2]
        quality_label = "retry"
        quality_summary = build_answer_quality_summary(quality_label, question_type, missing_concepts)
        sample_answer = provided_sample_answer or build_retry_sample_answer(subject, question_type, response_validity["label"], comparison_subjects)
        ideal_answer = ""
    else:
        quality_label = determine_answer_quality(
            content_score, keyword_coverage, delivery["word_count"], structure_result["score"], correctness_result["score"]
        )
        quality_summary = build_answer_quality_summary(quality_label, question_type, missing_concepts)
        sample_answer = provided_sample_answer or build_sample_answer(
            subject,
            question_type,
            topic,
            missing_concepts,
            comparison_subjects,
            matched_keywords,
            guidance_result,
        )
        ideal_answer = (
            provided_ideal_answer
            or (guidance_result["ideal_answer"] if guidance_result and guidance_result.get("ideal_answer") else "")
            or build_ideal_answer(subject, question_type, topic, missing_concepts, comparison_subjects, matched_keywords)
        )

    weight = resolved_weight
    return {
        "transcript": transcript,
        "word_count": delivery["word_count"],
        "filler_words": delivery["filler_count"],
        "filler_list": delivery["filler_list"],
        "duration": round(duration, 2),
        "wpm": delivery["wpm"],
        "confidence": overall_score,
        "overall_score": overall_score,
        "delivery_score": delivery["delivery_score"],
        "content_score": content_score,
        "keyword_coverage": keyword_coverage,
        "topic_relevance": topic_relevance,
        "intent_alignment": round(intent_alignment),
        "technical_depth": technical_depth,
        "answer_structure_score": structure_result["score"],
        "covered_answer_elements": structure_result["covered"],
        "correctness_score": correctness_result["score"],
        "correctness_verdict": correctness_result["verdict"],
        "correctness_summary": correctness_result["summary"],
        "covered_points": correctness_result["covered_points"],
        "missing_points": correctness_result["missing_points"],
        "incorrect_points": correctness_result["incorrect_points"],
        "improvement_steps": correctness_result["improvement_steps"],
        "question_keywords": question_keywords,
        "question_phrases": question_phrases,
        "matched_keywords": matched_keywords,
        "matched_topic_terms": matched_topic_terms,
        "technical_hits": technical_hits,
        "question_type": question_type,
        "question_guidance_score": guidance_result["score"] if guidance_result else None,
        "guided_points_covered": guidance_result["matched"] if guidance_result else [],
        "guided_points_partial": guidance_result["partial"] if guidance_result else [],
        "guided_point_details": guidance_result["point_details"] if guidance_result else [],
        "reference_alignment_score": reference_alignment["score"],
        "reference_alignment_matched": reference_alignment["matched"],
        "reference_alignment_partial": reference_alignment["partial"],
        "contradiction_points": contradiction_points,
        "response_validity": response_validity["label"],
        "response_validity_reason": response_validity["reason"],
        "question_similarity": response_validity["similarity"],
        "novel_terms_detected": response_validity["novel_terms"],
        "language_mode": language_mode,
        "language_feedback": language_feedback,
        "strengths": strengths,
        "improvements": improvements,
        "answer_quality_label": quality_label,
        "answer_quality_summary": quality_summary,
        "missing_concepts": missing_concepts,
        "sample_answer": sample_answer,
        "ideal_answer": ideal_answer,
        "reference_source": reference_source if ideal_answer or sample_answer else "generated",
        "difficulty": difficulty,
        "weight": weight,
        "analytics_mode": "full",
        "time_target_seconds": 0,
        "time_target_delta_seconds": 0,
        "time_target_status": "not_set",
        "time_target_score": 0,
    }
