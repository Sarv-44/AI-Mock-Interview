import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.analytics import (
    QUESTION_GUIDANCE,
    detect_question_type,
    extract_answer_subject,
    extract_comparison_subjects,
    normalize_question_key,
)
from backend.interview_catalog import ROLE_CATALOG, TOPIC_CATALOG, parse_question_bank

OUTPUT_PATH = PROJECT_ROOT / "AUTH2_SCHEMA.sql"

TOPIC_CONTEXT = {
    "graphs": {
        "area": "graph algorithms",
        "focus": "how nodes and edges are traversed, searched, or optimized",
        "tradeoff": "time complexity, memory use, and the structure of the graph",
        "components": ["nodes", "edges", "visited tracking"],
    },
    "datastructures": {
        "area": "data structures",
        "focus": "how data is stored, accessed, and updated efficiently",
        "tradeoff": "lookup speed, update cost, ordering, and memory usage",
        "components": ["storage model", "access pattern", "update behavior"],
    },
    "sorting": {
        "area": "sorting algorithms",
        "focus": "how data becomes ordered and what complexity that creates",
        "tradeoff": "runtime, stability, memory overhead, and data distribution",
        "components": ["partitioning or merging", "comparison strategy", "runtime behavior"],
    },
    "dp": {
        "area": "dynamic programming",
        "focus": "how repeated subproblems are reused through states and transitions",
        "tradeoff": "time improvement versus extra memory and implementation complexity",
        "components": ["state definition", "transition", "base case"],
    },
    "database": {
        "area": "database systems",
        "focus": "how data is modeled, queried, and kept correct at scale",
        "tradeoff": "read performance, write cost, consistency, and schema flexibility",
        "components": ["storage layout", "query path", "consistency rule"],
    },
    "systemdesign": {
        "area": "system design",
        "focus": "how the system handles requests, data, traffic, and failure",
        "tradeoff": "scale, availability, consistency, and operational complexity",
        "components": ["API layer", "storage", "caching or async work"],
    },
    "behavioral": {
        "area": "behavioral interviewing",
        "focus": "ownership, decision making, communication, and reflection",
        "tradeoff": "speed versus quality, autonomy versus alignment, and short-term versus long-term outcomes",
        "components": ["situation", "action", "result"],
    },
    "python": {
        "area": "Python engineering",
        "focus": "language behavior, runtime choices, and practical engineering use",
        "tradeoff": "clarity, performance, memory use, and language semantics",
        "components": ["language feature", "runtime behavior", "practical use case"],
    },
    "os": {
        "area": "operating systems",
        "focus": "processes, memory, scheduling, and concurrency behavior",
        "tradeoff": "isolation, efficiency, synchronization, and system overhead",
        "components": ["execution model", "resource handling", "concurrency rule"],
    },
    "java": {
        "area": "Java systems",
        "focus": "runtime behavior, object model, memory, and language features",
        "tradeoff": "abstraction, performance, safety, and maintainability",
        "components": ["language feature", "runtime detail", "practical engineering impact"],
    },
    "javascript": {
        "area": "JavaScript runtime behavior",
        "focus": "scope, async execution, browser or runtime behavior, and language semantics",
        "tradeoff": "readability, control flow, performance, and correctness",
        "components": ["execution model", "language rule", "real-world example"],
    },
    "react": {
        "area": "React applications",
        "focus": "component state, rendering, data flow, and UI structure",
        "tradeoff": "simplicity, reusability, performance, and maintainability",
        "components": ["component tree", "state flow", "render behavior"],
    },
    "nodejs": {
        "area": "Node.js services",
        "focus": "event-loop behavior, I/O throughput, and production service design",
        "tradeoff": "throughput, latency, CPU limits, and operational simplicity",
        "components": ["runtime model", "I/O handling", "production concern"],
    },
    "machinelearning": {
        "area": "machine learning",
        "focus": "training, evaluation, generalization, and deployment quality",
        "tradeoff": "bias, variance, interpretability, and model performance",
        "components": ["objective", "metric", "failure mode"],
    },
    "genai": {
        "area": "generative AI systems",
        "focus": "model behavior, prompts, retrieval, safety, and evaluation",
        "tradeoff": "latency, cost, answer quality, and hallucination risk",
        "components": ["model behavior", "control mechanism", "product tradeoff"],
    },
    "cloud": {
        "area": "cloud architecture",
        "focus": "scaling, resilience, deployment, and managed infrastructure choices",
        "tradeoff": "cost, reliability, operational complexity, and flexibility",
        "components": ["compute layer", "network edge", "storage or resilience choice"],
    },
    "networking": {
        "area": "networking",
        "focus": "protocol behavior, routing, latency, and communication guarantees",
        "tradeoff": "reliability, latency, throughput, and operational simplicity",
        "components": ["protocol rule", "network path", "practical impact"],
    },
    "security": {
        "area": "application security",
        "focus": "access control, vulnerabilities, mitigation, and incident handling",
        "tradeoff": "security strength, usability, operational overhead, and blast radius",
        "components": ["risk", "mitigation", "practical example"],
    },
    "testing": {
        "area": "software testing",
        "focus": "confidence, scope, cost, and defect prevention",
        "tradeoff": "speed, realism, maintenance cost, and release confidence",
        "components": ["scope", "failure mode", "confidence gain"],
    },
    "devops": {
        "area": "DevOps and platform engineering",
        "focus": "delivery flow, reliability, observability, and operational response",
        "tradeoff": "release speed, safety, automation, and system stability",
        "components": ["pipeline", "operational signal", "rollback or recovery"],
    },
    "apis": {
        "area": "API design",
        "focus": "contracts, consistency, versioning, and integration behavior",
        "tradeoff": "simplicity, flexibility, backward compatibility, and reliability",
        "components": ["interface contract", "client experience", "failure handling"],
    },
}

TYPE_MARKING = {
    "definition": {"correctness": 45, "coverage": 25, "reasoning": 15, "structure": 15},
    "comparison": {"correctness": 40, "coverage": 25, "reasoning": 20, "structure": 15},
    "process": {"correctness": 35, "coverage": 25, "reasoning": 25, "structure": 15},
    "design": {"correctness": 28, "coverage": 24, "reasoning": 33, "structure": 15},
    "complexity": {"correctness": 40, "coverage": 25, "reasoning": 20, "structure": 15},
    "tradeoff": {"correctness": 32, "coverage": 23, "reasoning": 30, "structure": 15},
    "decision": {"correctness": 30, "coverage": 20, "reasoning": 35, "structure": 15},
    "behavioral": {"correctness": 20, "coverage": 25, "reasoning": 30, "structure": 25},
    "concept": {"correctness": 40, "coverage": 25, "reasoning": 20, "structure": 15},
}


def sql_string(value):
    if value is None:
        return "NULL"
    return "'" + str(value).replace("\\", "\\\\").replace("'", "''") + "'"


def sql_json(value):
    return sql_string(json.dumps(value, ensure_ascii=False))


def topic_context(topic_id):
    return TOPIC_CONTEXT.get(
        topic_id,
        {
            "area": topic_id.replace("_", " "),
            "focus": "the core concept and why it matters in practice",
            "tradeoff": "correctness, simplicity, and performance",
            "components": ["core idea", "technical detail", "practical example"],
        },
    )


def question_type_for(question_text, topic_id):
    if topic_id == "behavioral":
        return "behavioral"
    return detect_question_type(str(question_text or "").lower())


def estimated_seconds(difficulty):
    return {"easy": 45, "medium": 75, "hard": 105}.get(difficulty, 60)


def build_generic_core_points(question_text, topic_id, question_type):
    subject = extract_answer_subject(question_text)
    subjects = extract_comparison_subjects(question_text)
    context = topic_context(topic_id)

    if question_type == "comparison":
        names = subjects[:2] or [subject, "the other concept"]
        return [
            f"Define {names[0]} clearly",
            f"Define {names[1]} clearly",
            "State the biggest difference directly",
            "Explain when each option is a better fit",
        ]

    if question_type == "process":
        return [
            f"State the goal of {subject}",
            "Explain the main steps in order",
            f"Connect the process to {context['focus']}",
            "Give one concrete example or outcome",
        ]

    if question_type == "design":
        return [
            f"Define the goal of {subject}",
            f"Name the main components such as {', '.join(context['components'][:3])}",
            "Describe the request or data flow",
            f"Mention a tradeoff around {context['tradeoff']}",
        ]

    if question_type == "complexity":
        return [
            f"State the main idea behind {subject}",
            "Mention the time complexity clearly",
            "Mention the space cost or memory impact",
            "Explain why the chosen approach has that cost",
        ]

    if question_type == "tradeoff":
        return [
            f"Define {subject} clearly",
            "State the main advantage",
            "State the main drawback or limitation",
            "Explain when the approach is a good fit",
        ]

    if question_type == "decision":
        return [
            f"Frame the decision around {subject}",
            "Make a clear recommendation",
            "Explain the condition behind the choice",
            f"Mention a tradeoff around {context['tradeoff']}",
        ]

    if question_type == "behavioral":
        return [
            "Set up the situation clearly",
            "Explain the action you personally took",
            "Describe the result with specifics",
            "Close with what you learned or would repeat",
        ]

    return [
        f"Define {subject} clearly",
        f"Explain why it matters in {context['area']}",
        f"Add one technical detail tied to {context['focus']}",
        "Include one practical use case or tradeoff",
    ]


def build_optional_points(question_text, topic_id, question_type):
    context = topic_context(topic_id)
    subject = extract_answer_subject(question_text)
    if question_type == "behavioral":
        return [
            "Keep the story concise and chronological",
            "Show ownership instead of speaking only about the team",
            "Mention the impact on users, delivery, or team trust",
        ]
    return [
        f"Relate {subject} to a real interview or production use case",
        f"Touch on {context['tradeoff']}",
        f"Reference one component such as {context['components'][0]}",
    ]


def build_common_mistakes(question_text, topic_id, question_type):
    subject = extract_answer_subject(question_text)

    if question_type == "comparison":
        return [
            "Treating the compared concepts as if they are the same",
            "Listing features without stating the main difference",
            "Skipping when each option should be used",
        ]
    if question_type == "process":
        return [
            "Jumping into details without stating the goal",
            "Explaining the steps out of order",
            "Missing the final outcome or practical example",
        ]
    if question_type == "design":
        return [
            "Naming components without explaining the flow",
            "Ignoring scaling, failure, or consistency tradeoffs",
            "Giving a generic architecture with no reasoning",
        ]
    if question_type == "complexity":
        return [
            "Giving the wrong complexity or skipping it entirely",
            "Mentioning Big O without explaining why",
            "Ignoring space cost or memory impact",
        ]
    if question_type == "behavioral":
        return [
            "Telling a team story without clarifying personal contribution",
            "Skipping the result or learning",
            "Giving a vague answer with no concrete situation",
        ]
    return [
        f"Giving a vague definition of {subject}",
        "Missing the key reason it matters",
        "Skipping the tradeoff, example, or practical use case",
    ]


def build_reasoning_steps(question_text, topic_id, question_type):
    subject = extract_answer_subject(question_text)
    subjects = extract_comparison_subjects(question_text)
    if question_type == "comparison":
        names = subjects[:2] or [subject, "the other concept"]
        return [
            f"Define {names[0]} briefly",
            f"Define {names[1]} briefly",
            "State the main difference in one sentence",
            "Close with a use case or tradeoff",
        ]
    if question_type == "behavioral":
        return [
            "Set the situation",
            "Explain your task or responsibility",
            "Describe the action you took",
            "End with the result and reflection",
        ]
    if question_type == "process":
        return ["State the goal", "Walk through the main steps", "Explain why the steps work", "End with an example or result"]
    if question_type == "design":
        return ["State the system goal", "Name the main components", "Explain the request and data flow", "Mention one important tradeoff"]
    return [
        f"Define {subject} directly",
        "Add one technical detail",
        "Connect it to a practical use case",
        "Mention one tradeoff or limitation if relevant",
    ]


def build_topic_specific_seed(question_text, topic_id):
    lower = question_text.lower()

    def seed(sample, ideal, core_points, optional_points=None, common_mistakes=None, reasoning_steps=None):
        return {
            "sample_answer": sample,
            "ideal_answer": ideal,
            "core_points": core_points,
            "optional_points": optional_points,
            "common_mistakes": common_mistakes,
            "reasoning_steps": reasoning_steps,
        }

    if topic_id == "graphs":
        if "dijkstra" in lower and "a*" in lower:
            return seed(
                "Both A* and Dijkstra are shortest-path algorithms, but A* uses a heuristic to guide the search toward the target, while Dijkstra explores based only on the shortest known distance so far. That means Dijkstra is more general for finding shortest paths in graphs with non-negative weights, but A* is usually faster when you have a good heuristic and only care about one destination.",
                "Both A* and Dijkstra solve shortest-path problems, but they optimize the search differently. Dijkstra expands the node with the smallest known distance from the source and guarantees optimal shortest paths in graphs with non-negative weights. A* adds a heuristic estimate of remaining distance, so it prioritizes nodes that look promising for the target. With an admissible heuristic, A* is still optimal, but in practice it often explores fewer nodes than Dijkstra for point-to-point search. So the tradeoff is generality versus guided efficiency.",
                [
                    "Dijkstra uses only the known distance from the source",
                    "A* adds a heuristic estimate toward the target",
                    "Both can find shortest paths when used under the right conditions",
                    "A* is usually faster for single-target search with a good heuristic",
                ],
            )
        if "dijkstra" in lower:
            return seed(
                "Dijkstra's algorithm finds the shortest path from one source node to all other nodes in a weighted graph, as long as the edge weights are non-negative. It keeps track of the best known distance to each node, repeatedly picks the unvisited node with the smallest distance, and relaxes its outgoing edges. A common implementation uses a min-heap, which gives a time complexity of about O((V + E) log V).",
                "Dijkstra's algorithm is a shortest-path algorithm for weighted graphs with non-negative edges. It starts with the source at distance zero, keeps a tentative distance for every node, and repeatedly extracts the node with the smallest current distance. From there it relaxes outgoing edges, updating neighbors if a shorter path is found. The reason it works is that once the smallest-distance unvisited node is chosen, its shortest distance is finalized under the non-negative edge assumption. With a priority queue, the typical complexity is O((V + E) log V), and common use cases include routing, maps, and network path selection.",
                [
                    "It finds shortest paths in weighted graphs with non-negative edges",
                    "It repeatedly selects the node with the smallest tentative distance",
                    "It relaxes outgoing edges to improve known distances",
                    "A heap-based implementation is typically O((V + E) log V)",
                ],
            )
        if "minimum spanning tree" in lower or "prim" in lower or "kruskal" in lower:
            return seed(
                "A minimum spanning tree connects all vertices in a connected weighted graph using the minimum total edge weight and without forming cycles. Prim's algorithm grows the tree from one starting node by repeatedly taking the cheapest edge that adds a new vertex, while Kruskal's algorithm sorts edges globally and keeps adding the next cheapest edge that does not create a cycle.",
                "A minimum spanning tree, or MST, is a subset of edges that connects every vertex in a connected weighted graph with minimum total weight and no cycles. Prim's algorithm builds the MST incrementally from a starting node, always choosing the cheapest edge that expands the current tree. Kruskal's algorithm instead sorts all edges by weight and adds them in order while using a disjoint-set structure to avoid cycles. Prim is often natural with adjacency structures, while Kruskal is elegant when edge sorting is convenient. Both solve the same problem, but the implementation style and performance details differ based on the graph representation.",
                [
                    "An MST connects all vertices with minimum total edge weight and no cycles",
                    "Prim grows the tree outward from a chosen start node",
                    "Kruskal sorts edges and adds the next cheapest safe edge",
                    "Cycle avoidance is essential, often using visited logic or union-find",
                ],
            )
        if "breadth-first search" in lower and "depth-first search" in lower:
            return seed(
                "Breadth-first search explores the graph level by level, usually with a queue, while depth-first search goes as deep as possible before backtracking, usually with a stack or recursion. BFS is the better choice when you need the shortest path in an unweighted graph, while DFS is often simpler for path existence, cycle detection, and topological-style traversal.",
                "Breadth-first search and depth-first search are both graph traversal strategies, but they behave differently. BFS uses a queue and visits nodes level by level, which is why it can find the shortest path in an unweighted graph. DFS uses recursion or an explicit stack and explores one branch deeply before backtracking. In practice, BFS is preferred for minimum-step reachability, while DFS is often convenient for cycle detection, connected components, recursion-friendly traversal, and some graph ordering problems. The main tradeoff is that BFS usually needs more memory on wide graphs, while DFS can go deep and risk recursion depth issues.",
                [
                    "BFS explores level by level, typically with a queue",
                    "DFS explores deeply before backtracking, typically with a stack or recursion",
                    "BFS is useful for shortest paths in unweighted graphs",
                    "DFS is useful for deep traversal, cycle logic, and recursive graph problems",
                ],
            )
        if "cycle in a directed graph" in lower:
            return seed(
                "A standard way to detect a cycle in a directed graph is to run DFS and track both visited nodes and the nodes currently in the recursion stack. If during traversal you reach a node that is already in the current recursion stack, that means you found a back edge, which proves there is a cycle.",
                "To detect a cycle in a directed graph, I would usually run depth-first search while tracking two states: nodes that have been visited at all, and nodes currently in the active DFS path. When DFS reaches a neighbor that is already in the current path, that indicates a back edge, which means a cycle exists. After fully exploring a node, you remove it from the active path. Another valid approach is Kahn's algorithm: if you cannot process all nodes in topological order, the graph contains a cycle. DFS with a recursion-stack check is the most common interview answer because it is direct and easy to reason about.",
                [
                    "DFS with a recursion-stack or active-path check is a common solution",
                    "A back edge to a node already in the current path indicates a cycle",
                    "Visited and active-path states serve different purposes",
                    "Topological-order failure is another way to detect a directed cycle",
                ],
            )
        if "topological sorting" in lower:
            return seed(
                "Topological sorting gives an ordering of nodes in a directed acyclic graph so that each node appears before the nodes that depend on it. It is useful for dependency scheduling, build systems, and task ordering. You can compute it with DFS postorder or with Kahn's algorithm using indegrees.",
                "Topological sorting is an ordering of vertices in a directed acyclic graph, or DAG, such that every directed edge goes from an earlier node to a later node in the order. It only exists when the graph has no directed cycle. In practice, it is useful for scheduling tasks with dependencies, resolving build order, or processing prerequisites. Two standard solutions are DFS, where you push nodes after exploring descendants, and Kahn's algorithm, where you repeatedly remove zero-indegree nodes. The core idea is preserving dependency direction in the final ordering.",
                [
                    "It orders nodes in a DAG so dependencies come first",
                    "It only works when the graph has no directed cycle",
                    "It is useful for scheduling and dependency resolution",
                    "Common implementations use DFS postorder or Kahn's algorithm",
                ],
            )
        if "connected components" in lower:
            return seed(
                "Connected components are groups of vertices where every node is reachable from every other node in the same group. In an undirected graph, you can find them by running DFS or BFS from each unvisited node and marking all nodes reached in that traversal as one component.",
                "A connected component in an undirected graph is a maximal set of vertices that are all reachable from one another. The usual way to find all components is to iterate through every node, and whenever you see an unvisited node, start a DFS or BFS from it. All nodes reached in that traversal belong to the same component. Then you continue until all nodes have been visited. The algorithm is linear in the size of the graph, O(V + E), because each node and edge is processed a limited number of times.",
                [
                    "A connected component is a maximal reachable group in an undirected graph",
                    "Start DFS or BFS from each unvisited node",
                    "Every traversal marks exactly one component",
                    "The standard complexity is O(V + E)",
                ],
            )

    if topic_id == "datastructures":
        if "what is a stack" in lower:
            return seed(
                "A stack is a linear data structure that follows last-in, first-out order, so the most recently added element is the first one removed. It is useful for function call handling, undo operations, expression evaluation, and depth-first traversal because those problems naturally need the most recent item first.",
                "A stack is a last-in, first-out data structure, often abbreviated as LIFO. The main operations are push, pop, and peek, all of which are typically O(1). Stacks are useful when the most recent item should be processed first, such as function call stacks, undo-redo systems, parsing expressions, and depth-first search. The core idea is very simple, but it becomes powerful because many recursive or nested workflows naturally map onto LIFO behavior.",
                [
                    "A stack follows last-in, first-out order",
                    "Common operations are push, pop, and peek",
                    "It is useful for call stacks, undo logic, and DFS-style problems",
                    "Operations are usually O(1)",
                ],
            )
        if "hash tables" in lower:
            return seed(
                "A hash table stores key-value pairs by using a hash function to map a key to an index or bucket. When two keys land in the same place, that is a collision, and common ways to handle it are chaining, where each bucket stores multiple entries, or open addressing, where you probe for another slot.",
                "A hash table gives average O(1) lookup, insert, and delete by using a hash function to map a key into an array-like storage structure. Because multiple keys can map to the same bucket, collision handling is essential. With chaining, each bucket holds a small list or structure of entries. With open addressing, the table probes for another available slot according to a strategy such as linear or quadratic probing. Performance depends on a good hash function and a controlled load factor, which is why resizing matters.",
                [
                    "A hash function maps keys to storage locations",
                    "Collisions happen when multiple keys map to the same location",
                    "Chaining and open addressing are common collision strategies",
                    "Performance depends on hash quality and load factor",
                ],
            )
        if "balanced binary trees" in lower:
            return seed(
                "Balanced binary trees keep their height under control, which helps search, insert, and delete stay efficient instead of degrading toward linear time. They are useful when you need ordered data plus predictable performance, because the balance property prevents one side of the tree from becoming too deep.",
                "The main advantage of a balanced binary tree is that it keeps the height close to logarithmic in the number of nodes. That matters because search, insertion, and deletion all depend on tree height, so a balanced tree keeps those operations around O(log n) instead of letting them degrade toward O(n) like an unbalanced chain. Balanced trees are useful when you need ordered traversal plus efficient updates, such as in sets, maps, interval structures, or in-memory indexes. The tradeoff is that balancing logic adds complexity and some maintenance overhead on updates.",
                [
                    "Balancing keeps tree height close to logarithmic",
                    "That preserves efficient search, insert, and delete",
                    "Balanced trees are useful when ordered data must stay efficient",
                    "The tradeoff is extra balancing complexity during updates",
                ],
            )
        if "arrays, linked lists, and dynamic arrays" in lower:
            return seed(
                "Arrays give O(1) random access because elements are contiguous, but inserts and deletes in the middle are expensive because items shift. Linked lists make inserts and deletes easy once you have the node, but random access is slow because you must traverse. Dynamic arrays keep the random-access strength of arrays while allowing growth, though resizing can occasionally be expensive.",
                "Arrays, linked lists, and dynamic arrays trade off access cost, update cost, and memory behavior. Arrays provide O(1) random access because elements are stored contiguously, but inserts and deletes in the middle are O(n) because elements shift. Linked lists make insertion and deletion easier near a known node, but random access is O(n) because traversal is required. Dynamic arrays behave like arrays for access, but they grow by reallocating and copying when capacity runs out, so append is amortized O(1). In practice, arrays or dynamic arrays are preferred most of the time unless linked-list insertion patterns are genuinely important.",
                [
                    "Arrays provide fast random access but costly middle updates",
                    "Linked lists support easier local insertion and deletion but slow access",
                    "Dynamic arrays combine fast access with resizable capacity",
                    "Choosing between them depends on access versus update patterns",
                ],
            )
        if "heap" in lower and "priority queue" in lower:
            return seed(
                "A heap is a tree-based structure, usually implemented as an array, where the smallest element in a min-heap or the largest element in a max-heap stays at the root. That makes it useful for priority queues because insert and extract-top operations stay efficient, typically O(log n), while peeking at the highest-priority item is O(1).",
                "A heap is a specialized complete binary tree that maintains a heap-order property, such as every parent being smaller than its children in a min-heap. In practice, heaps are usually stored in arrays, which makes parent-child navigation simple by index arithmetic. They are ideal for priority queues because the highest-priority item is always at the root, so peek is O(1), and insertion or extraction can be done in O(log n) by bubbling elements up or down. Heaps are common in schedulers, Dijkstra's algorithm, and any workflow where you repeatedly need the next best item rather than full sorted order.",
                [
                    "A heap maintains a heap-order property",
                    "It is commonly implemented as an array-backed complete binary tree",
                    "It supports efficient top-element access and O(log n) insert/extract",
                    "That makes it a good fit for priority queues",
                ],
            )
        if "binary tree and a binary search tree" in lower:
            return seed(
                "A binary tree is any tree where each node has at most two children. A binary search tree, or BST, is a special binary tree where values in the left subtree are smaller than the node and values in the right subtree are larger. So every BST is a binary tree, but not every binary tree supports ordered search behavior.",
                "A binary tree is a structural concept: each node can have up to two children. A binary search tree adds an ordering rule, where all values in the left subtree are smaller than the current node and all values in the right subtree are larger. That ordering is what makes search, insert, and delete efficient on average or in balanced cases. Without that ordering, a plain binary tree does not support the same kind of directed search. So the key distinction is shape versus shape plus ordering.",
                [
                    "A binary tree only constrains the number of children",
                    "A BST adds an ordering rule across left and right subtrees",
                    "That ordering enables faster directed search",
                    "Every BST is a binary tree but not vice versa",
                ],
            )
        if "lru cache" in lower:
            return seed(
                "A common LRU cache design combines a hash map with a doubly linked list. The hash map gives O(1) access to cached items by key, and the doubly linked list keeps items ordered by recent use. When an item is accessed, it moves to the front, and when the cache is full, you evict the node at the back because that is the least recently used item.",
                "To design an LRU cache efficiently, I would combine two data structures: a hash map and a doubly linked list. The hash map maps a key to the corresponding node in the list, which gives O(1) lookup. The doubly linked list maintains recency order, with the most recently used item near the front and the least recently used item near the back. On every read or write, you move the item to the front. If capacity is exceeded, you remove the tail node and also delete its hash-map entry. This design is standard because it achieves O(1) get and put while preserving eviction order.",
                [
                    "Use a hash map for O(1) key lookup",
                    "Use a doubly linked list to maintain recency order",
                    "Move accessed items to the front",
                    "Evict from the tail when capacity is exceeded",
                ],
            )
        if "trie" in lower:
            return seed(
                "A trie is a tree-like data structure used to store strings by character prefix. Each path from the root represents a prefix, and words end at marked terminal nodes. Tries are useful for autocomplete, prefix search, and dictionary-style lookups where shared prefixes should be reused efficiently.",
                "A trie stores strings one character at a time, so common prefixes share the same path from the root. Each node represents a prefix, and a terminal flag marks whether a full word ends there. That structure makes prefix operations efficient because you do not need to scan unrelated words once the prefix path is known. Tries are especially useful for autocomplete, spell checking, and prefix-based retrieval. The tradeoff is memory overhead, because many nodes may be created compared with storing raw strings in a flat list or hash map.",
                [
                    "A trie stores strings by shared prefix paths",
                    "Nodes represent prefixes and terminal markers represent full words",
                    "It is efficient for prefix search and autocomplete",
                    "The tradeoff is higher memory usage than simpler structures",
                ],
            )
        if "bloom filter" in lower:
            return seed(
                "A Bloom filter is a space-efficient probabilistic data structure used to test whether an element is possibly in a set. It can return false positives, but it does not return false negatives for inserted elements. That makes it useful when you want a fast, memory-light precheck before doing a more expensive lookup.",
                "A Bloom filter uses a bit array and multiple hash functions to represent set membership compactly. When you add an item, each hash function sets a bit. To query an item, you check whether all corresponding bits are set. If any required bit is missing, the item is definitely not present. If all bits are set, the item may be present, which is why Bloom filters can produce false positives. They are useful in systems like caches, databases, and networking where you want to avoid unnecessary expensive lookups while accepting a small probability of extra work.",
                [
                    "A Bloom filter is a probabilistic membership structure",
                    "It can produce false positives but not false negatives for inserted items",
                    "It uses a bit array plus multiple hash functions",
                    "It is useful as a fast precheck before an expensive lookup",
                ],
            )

    if topic_id == "sorting":
        if "bubble sort" in lower:
            return seed(
                "Bubble sort repeatedly compares adjacent elements and swaps them when they are in the wrong order, so larger elements keep moving toward the end of the list. It is simple to explain, but it has O(n^2) time complexity in the average and worst case, which makes it a poor choice for large datasets.",
                "Bubble sort is a simple comparison-based sorting algorithm that repeatedly scans the array, swapping adjacent out-of-order elements. After each full pass, the largest remaining unsorted element has effectively bubbled to its correct position at the end. Its main value in interviews is educational simplicity, not practical performance, because average and worst-case time complexity are O(n^2). It is usually only reasonable for tiny inputs or teaching the idea of repeated passes and swaps.",
                [
                    "It repeatedly swaps adjacent out-of-order elements",
                    "Large elements move toward the end after each pass",
                    "Its average and worst-case time complexity is O(n^2)",
                    "It is simple but usually not preferred in practice",
                ],
            )
        if "quick sort" in lower and "faster in practice" in lower:
            return seed(
                "Quick sort is often faster in practice because its inner loop is simple, it works in place, and it tends to use memory in a cache-friendly way. Even though its worst case is O(n^2), with a good pivot strategy its average case is O(n log n), and the constants are often better than more allocation-heavy alternatives.",
                "Quick sort is usually faster in practice because the algorithm has very small constant factors, good cache behavior, and in-place partitioning. On average it runs in O(n log n), and with randomized or well-chosen pivots it performs very well on typical in-memory workloads. Merge sort has the same asymptotic average complexity, but quick sort often wins on raw speed because it does less extra copying. The tradeoff is that quick sort has a worst case of O(n^2) and is not stable by default, so context still matters.",
                [
                    "Quick sort has small constant factors and good cache locality",
                    "It is in-place, so it avoids large extra memory overhead",
                    "Its average complexity is O(n log n)",
                    "Its worst case and stability tradeoffs still matter",
                ],
            )
        if "quick sort" in lower:
            return seed(
                "Quick sort chooses a pivot, partitions the array so smaller elements go to one side and larger elements go to the other, and then recursively sorts the two partitions. Its average time complexity is O(n log n), and it is popular because it is fast in practice and can be done mostly in place.",
                "Quick sort is a divide-and-conquer sorting algorithm. It selects a pivot, partitions the input so that elements smaller than the pivot are placed on one side and larger ones on the other, and then recursively sorts the partitions. Its average time complexity is O(n log n), but the worst case is O(n^2) if partitions become very unbalanced. In practice it is widely used because the in-place partitioning gives good cache locality and strong average performance. A strong answer should also mention pivot choice, because that heavily affects behavior.",
                [
                    "Choose a pivot and partition around it",
                    "Recursively sort the left and right partitions",
                    "Average time is O(n log n), worst case is O(n^2)",
                    "Pivot choice strongly affects performance",
                ],
            )
        if "merge sort" in lower:
            return seed(
                "Merge sort splits the array into halves, recursively sorts each half, and then merges the sorted halves back together. Its time complexity is O(n log n) in the best, average, and worst case, and it is stable, but it usually needs O(n) extra space for the merge step.",
                "Merge sort is a classic divide-and-conquer algorithm. It repeatedly splits the input into halves until each part is trivially sorted, then merges those halves back together in sorted order. Because each level of recursion processes all n elements and there are log n levels, the time complexity is O(n log n). It is stable and gives predictable performance, which makes it attractive in many contexts, but the usual tradeoff is O(n) extra memory for merging.",
                [
                    "It recursively splits the input into halves",
                    "It merges sorted halves back together",
                    "Time complexity is O(n log n) across cases",
                    "It is stable but usually needs extra memory",
                ],
            )
        if "comparison-based and non-comparison-based sorting" in lower:
            return seed(
                "Comparison-based sorting decides order by directly comparing elements, which is how algorithms like quick sort, merge sort, and heap sort work. Non-comparison-based sorting, like counting sort or radix sort, uses assumptions about the data, such as bounded integer ranges or digit structure, to do better than the general O(n log n) comparison lower bound in those special cases.",
                "Comparison-based sorting algorithms determine order by comparing elements, which means their general lower bound is O(n log n). Examples include quick sort, merge sort, and heap sort. Non-comparison-based algorithms such as counting sort, radix sort, and bucket sort avoid that lower bound by using additional assumptions about the input, like a limited value range or fixed-length digits. They can achieve linear or near-linear performance in the right setting, but the tradeoff is that they are not universally applicable. So the key difference is generality versus exploiting input structure.",
                [
                    "Comparison-based sorts rely on pairwise comparisons",
                    "They are subject to the general O(n log n) lower bound",
                    "Non-comparison-based sorts exploit structure in the input",
                    "Those special algorithms can be faster but are less general",
                ],
            )
        if "counting sort" in lower:
            return seed(
                "Counting sort achieves linear time when the input values lie in a reasonably small integer range. Instead of comparing elements, it counts how many times each value occurs, then reconstructs the sorted output from those counts. The time is roughly O(n + k), where k is the range size.",
                "Counting sort works well when values are integers from a limited range. It allocates a count array of size k, counts how often each value appears, and then uses those counts to place values in sorted order. Because it avoids direct comparisons, its time complexity is O(n + k), which can be effectively linear when k is not too large. The tradeoff is that memory usage depends on the value range, so it is a bad fit when keys are sparse or very large.",
                [
                    "It counts occurrences instead of comparing elements",
                    "Its complexity is O(n + k), where k is the value range",
                    "It works well when the range is small enough",
                    "The main tradeoff is range-dependent memory usage",
                ],
            )

    if topic_id == "database":
        if "sql and nosql" in lower:
            return seed(
                "SQL databases usually use relational tables with a fixed schema and strong support for joins and transactional consistency. NoSQL is a broader category that includes document, key-value, column-family, and graph databases, and it is often chosen for flexible schemas, horizontal scaling, or access patterns that do not fit relational modeling well.",
                "SQL databases are relational systems built around tables, structured schemas, joins, and strong query capabilities. They are usually a good fit when data relationships are important and transactional correctness matters. NoSQL refers to several non-relational models, such as document stores, key-value stores, wide-column databases, and graph databases. Those systems are often chosen when you need flexible schemas, very large horizontal scale, or simpler access patterns that do not require heavy relational joins. The real decision is not SQL versus modernity, but relational guarantees versus a data model optimized for a particular workload.",
                [
                    "SQL databases are relational and schema-oriented",
                    "NoSQL includes several non-relational data models",
                    "SQL is strong for relationships, joins, and transactions",
                    "NoSQL is often chosen for flexibility or scale-specific workloads",
                ],
            )
        if "foreign keys" in lower:
            return seed(
                "A foreign key is a constraint that links a column in one table to a primary key or unique key in another table. It helps maintain referential integrity, which means you cannot create records that point to missing parent rows. That matters because it keeps relationships between tables valid and prevents inconsistent data.",
                "A foreign key is a database constraint used to enforce a valid relationship between tables. For example, if an orders table stores a customer_id, a foreign key can ensure that every referenced customer actually exists in the customers table. That protects referential integrity and prevents orphaned data. Foreign keys also make the intended schema relationship explicit, which helps with correctness and maintainability. The tradeoff is that they add enforcement overhead, so in some very high-scale or distributed designs teams may manage integrity differently, but the default relational answer should strongly value them.",
                [
                    "A foreign key enforces a valid relationship between tables",
                    "It usually points to a primary or unique key in another table",
                    "It preserves referential integrity and prevents orphaned records",
                    "It improves schema correctness and maintainability",
                ],
            )
        if "slow database query" in lower:
            return seed(
                "To optimize a slow database query, I would first look at the query plan to see where time is being spent, then check indexing, filtering, joins, and row counts. After that I would reduce unnecessary scanned data, rewrite expensive parts if needed, and verify improvements with measurements rather than guessing.",
                "I would optimize a slow query in a measured way instead of guessing. First, inspect the execution plan and the actual workload profile to see whether the problem is full table scans, bad join order, missing indexes, poor selectivity, or excessive sorting. Then I would check whether the query is selecting too much data, using non-sargable filters, or joining on unindexed columns. Depending on the issue, the fix might be a better index, a rewritten query, denormalization, caching, or a schema change. Finally, I would benchmark before and after so the optimization is verified, not assumed.",
                [
                    "Start with the query or execution plan",
                    "Check indexes, joins, filters, and scan size",
                    "Reduce unnecessary work instead of optimizing blindly",
                    "Validate the improvement with measurement",
                ],
            )
        if "clustered and non-clustered indexes" in lower:
            return seed(
                "A clustered index determines the physical order of rows in the table, so the data itself is stored according to that index. A non-clustered index is a separate structure that stores indexed values plus a pointer to the underlying row. The main difference is whether the index defines data storage order or just provides an extra lookup path.",
                "A clustered index affects how table rows are physically organized, which is why a table can usually have only one effective clustered order. A non-clustered index is stored separately from the base data and maps indexed values to row locations. Clustered indexes are very helpful for range scans and ordered access patterns that align with the stored order. Non-clustered indexes are more flexible because you can create several of them, but each one adds maintenance cost on writes. So the tradeoff is physical storage order versus additional secondary access paths.",
                [
                    "A clustered index defines the physical row order",
                    "A non-clustered index is a separate lookup structure",
                    "Clustered indexes are strong for aligned range access",
                    "Non-clustered indexes provide flexible secondary access paths",
                ],
            )
        if "connection pooling" in lower:
            return seed(
                "Connection pooling means reusing a managed pool of open database connections instead of creating a brand-new connection for every request. That reduces connection setup overhead, improves throughput, and helps control how many concurrent database connections the application opens.",
                "Connection pooling is the practice of maintaining a reusable pool of database connections so requests can borrow and return them instead of constantly opening new ones. Creating a new connection is relatively expensive because of network setup, authentication, and protocol overhead. By reusing connections, the application improves latency and throughput while also enforcing limits on how much load it places on the database. The pool still needs careful sizing, because too few connections can bottleneck the app and too many can overwhelm the database.",
                [
                    "It reuses open connections instead of creating one per request",
                    "That reduces setup overhead and improves throughput",
                    "It helps control database concurrency",
                    "Pool size must be tuned to avoid bottlenecks or overload",
                ],
            )

    if topic_id == "javascript":
        if "var, let, and const" in lower:
            return seed(
                "The main differences are scope, reassignment, and hoisting behavior. Var is function-scoped and can be redeclared, which often creates bugs in larger codebases. Let is block-scoped and can be reassigned, while const is block-scoped and cannot be reassigned after initialization. In modern JavaScript, let and const are usually preferred because their behavior is more predictable.",
                "Var, let, and const all declare variables, but they differ in scope and mutability rules. Var is function-scoped and also gets hoisted in a way that can make its value behave unexpectedly before assignment. Let and const are block-scoped, which makes them safer in loops and conditional blocks. Let allows reassignment, while const requires one-time assignment of the binding. Because of clearer scoping and fewer accidental redeclarations, modern JavaScript code usually favors let and const over var.",
                [
                    "Var is function-scoped and can be redeclared",
                    "Let and const are block-scoped",
                    "Let allows reassignment while const does not",
                    "Let and const are usually preferred in modern code",
                ],
            )
        if "hoisting" in lower:
            return seed(
                "Hoisting means JavaScript moves declarations into an earlier phase of execution, even though the code still appears where you wrote it. Function declarations are available before their position in the file, while variables declared with var are hoisted but initialized as undefined until assignment. Let and const are also hoisted in a technical sense, but they stay in the temporal dead zone until initialization, so using them too early throws an error.",
                "Hoisting is the behavior where JavaScript processes declarations before the main execution flow runs. That is why function declarations can often be called before their textual position in the source code. Variables declared with var are hoisted too, but only the declaration is moved early, not the assigned value, so the variable exists as undefined before initialization. Let and const behave more safely because access before initialization triggers the temporal dead zone error. A strong answer should emphasize that hoisting affects declarations differently depending on what kind of declaration you use.",
                [
                    "JavaScript processes declarations before normal execution",
                    "Function declarations are available early",
                    "Var is hoisted with undefined before assignment",
                    "Let and const have temporal-dead-zone behavior before initialization",
                ],
            )
        if "regular functions and arrow functions" in lower:
            return seed(
                "The main difference is how this is bound. In a regular function, this depends on how the function is called, so it can point to different objects in different contexts. Arrow functions do not create their own this, and instead capture this lexically from the surrounding scope. That makes arrow functions convenient in callbacks, but less suitable when you actually want dynamic method-style binding.",
                "Regular functions and arrow functions differ mainly in how this is handled. A regular function gets its own this based on the call site, which is why the same function can behave differently depending on whether it is called as a method, standalone function, or with call or bind. Arrow functions do not create their own this at all; they inherit it from the surrounding lexical scope. That is helpful in callbacks and nested handlers because it avoids manual binding, but it also means arrow functions are not a drop-in replacement for methods when you want dynamic receiver behavior.",
                [
                    "Regular functions bind this from the call site",
                    "Arrow functions capture this lexically from the surrounding scope",
                    "Arrow functions are convenient in callbacks",
                    "Regular functions are better when dynamic receiver binding is needed",
                ],
            )
        if "== and ===" in lower:
            return seed(
                "Double equals checks loose equality and can perform type coercion before comparing values. Triple equals checks strict equality, so both the type and the value must match. In modern JavaScript, === is usually preferred because it avoids surprising coercion behavior.",
                "The difference between == and === is whether JavaScript performs coercion. With ==, JavaScript may convert one value to another type before comparing, which can lead to surprising results. With ===, both the value and the type must already match, so the comparison is more predictable. Because coercion can hide bugs and make conditions harder to reason about, most production JavaScript code prefers === unless there is a very deliberate reason to use loose equality.",
                [
                    "== allows type coercion before comparison",
                    "=== requires both type and value to match",
                    "=== is more predictable and usually preferred",
                    "Loose equality can create surprising bugs",
                ],
            )
        if "closures" in lower:
            return seed(
                "A closure happens when a function remembers variables from the scope where it was created, even after that outer function has finished running. That is useful for things like private state, function factories, and callbacks that need access to surrounding data later.",
                "A closure is created when an inner function keeps access to variables from its lexical scope after the outer function has returned. In other words, the function carries its surrounding environment with it. That is why closures are useful for encapsulation, currying, memoization, event handlers, and function factories. A practical example is a function that creates and returns a counter while preserving the count variable between calls. The key idea is lexical scope plus delayed execution.",
                [
                    "A closure preserves access to an outer lexical scope",
                    "That access remains even after the outer function returns",
                    "Closures are useful for private state and callbacks",
                    "A practical example is a counter or function factory",
                ],
            )
        if "event loop" in lower:
            return seed(
                "JavaScript uses an event loop to coordinate synchronous code, asynchronous callbacks, and the call stack. Synchronous code runs first on the call stack. When asynchronous work like timers or network events completes, its callbacks are queued and only executed when the stack is clear. That is why JavaScript can feel non-blocking even though ordinary code runs in a single main execution thread.",
                "The event loop is the mechanism that lets JavaScript handle asynchronous work without executing everything in parallel on the main call stack. Normal synchronous code runs to completion first. Browser APIs or runtime services handle timers, I/O, and other async operations outside that stack. When they finish, their callbacks are placed into task or microtask queues, and the event loop moves them onto the call stack when the current work is done. A strong answer should also mention that promises use the microtask queue, which usually runs before the next macrotask like a timer callback.",
                [
                    "Synchronous code runs on the call stack first",
                    "Async APIs complete outside the stack and queue callbacks",
                    "The event loop runs queued work when the stack is free",
                    "Promise callbacks typically use the microtask queue",
                ],
            )
        if "prototypes and prototypal inheritance" in lower:
            return seed(
                "In JavaScript, objects can inherit behavior from other objects through the prototype chain. A prototype is another object that a given object falls back to when a property or method is not found directly on itself. Prototypal inheritance is useful because it lets many objects share behavior without copying methods onto every instance.",
                "JavaScript uses prototype-based inheritance rather than classical class inheritance at the lowest level. Every object can link to another object called its prototype, and if a property or method is missing on the current object, JavaScript looks up the prototype chain. That is how shared methods work behind the scenes for constructor functions and classes. The benefit is behavior reuse without duplicating methods on each instance. A strong answer should also mention that modern class syntax is mostly a cleaner abstraction on top of this same prototype mechanism.",
                [
                    "Objects can delegate missing properties to their prototype",
                    "The prototype chain enables shared behavior reuse",
                    "Prototypal inheritance is the underlying inheritance model in JavaScript",
                    "Modern class syntax still builds on prototypes underneath",
                ],
            )
        if "event delegation" in lower:
            return seed(
                "Event delegation means attaching a single event handler to a parent element and then using event bubbling to respond to events from matching child elements. It is useful because it reduces the number of individual handlers you need and still works for child elements added later.",
                "Event delegation is a pattern where you place an event listener on a parent element instead of attaching separate listeners to every child. When an event bubbles up, the parent handler inspects the event target and decides whether to act. This is useful for performance, simpler code, and dynamic interfaces where child elements may be created or removed after the initial render. The key idea is that bubbling plus target inspection gives you centralized control over many related UI elements.",
                [
                    "A parent listener handles events from child elements through bubbling",
                    "The handler inspects the target to decide what to do",
                    "This reduces many individual listeners",
                    "It works well for dynamic lists and DOM updates",
                ],
            )

    if topic_id == "security":
        if "authentication and authorization" in lower:
            return seed(
                "Authentication answers the question 'who are you,' while authorization answers 'what are you allowed to do.' For example, logging in with a password or token is authentication, but checking whether that user can access an admin route is authorization.",
                "Authentication is the process of verifying identity, such as validating a password, session, or token. Authorization happens after identity is known and decides what that identity is permitted to access or change. A user may be successfully authenticated but still not be authorized to perform a privileged action. In practical systems, mixing up these two concepts leads to serious security bugs, because proving identity is not the same as enforcing least privilege.",
                [
                    "Authentication verifies identity",
                    "Authorization determines permissions or allowed actions",
                    "They happen at different stages in a secure flow",
                    "A user can be authenticated but still not authorized",
                ],
            )
        if "sql injection" in lower:
            return seed(
                "SQL injection happens when untrusted input is interpreted as part of a SQL query instead of being treated as plain data. The main defense is parameterized queries or prepared statements, because they separate query structure from user input. Input validation and least-privilege database accounts are also important supporting controls.",
                "SQL injection is a vulnerability where attacker-controlled input changes the meaning of a database query. For example, if application code concatenates raw user input into SQL, the attacker may be able to bypass checks, read extra data, or even modify records. The strongest primary defense is parameterized queries or prepared statements, because they ensure user input is bound as data rather than executable query logic. Additional protections include validation, escaping where appropriate, least-privilege database credentials, and careful review of dynamic query generation.",
                [
                    "Untrusted input changes the structure or meaning of a SQL query",
                    "Prepared statements or parameterized queries are the main defense",
                    "Input validation and least-privilege access also help",
                    "Raw string concatenation is the common root problem",
                ],
            )
        if "cross-site scripting" in lower:
            return seed(
                "Cross-site scripting, or XSS, happens when an application lets untrusted content run as script in the victim's browser. Common defenses include output encoding, avoiding unsafe DOM insertion, content security policy, and treating user-generated HTML as dangerous unless it is strictly sanitized.",
                "Cross-site scripting is a browser-side injection vulnerability where attacker-controlled input is rendered in a way that executes JavaScript in another user's browser. That can lead to session theft, unauthorized actions, or UI manipulation. The main defenses are context-aware output encoding, avoiding unsafe sinks like raw innerHTML, sanitizing any allowed rich content, and adding a strong Content Security Policy as defense in depth. A good answer should mention that XSS is about execution in the browser, not just bad input on the server.",
                [
                    "XSS allows attacker-controlled script execution in the browser",
                    "Output encoding and safe rendering are key defenses",
                    "Sanitization is needed for any allowed HTML content",
                    "CSP provides an additional layer of mitigation",
                ],
            )

    if topic_id == "react":
        if "what problem does react solve" in lower:
            return seed(
                "React helps developers build complex user interfaces by breaking them into reusable components and by keeping UI updates predictable when data changes. Instead of manually syncing the DOM everywhere, you describe the UI in terms of state and props, and React handles the rendering updates more systematically.",
                "React solves the problem of managing complex, stateful user interfaces in a maintainable way. It encourages developers to break the UI into reusable components, describe the interface declaratively, and let the framework reconcile the DOM when state changes. That reduces a lot of manual DOM manipulation and makes larger frontends easier to reason about. A strong answer should also mention that React is especially valuable when UI state, composition, and repeated updates become hard to manage by hand.",
                [
                    "React helps manage complex, stateful user interfaces",
                    "It uses reusable components and declarative rendering",
                    "It reduces manual DOM synchronization work",
                    "It is especially useful as UI complexity grows",
                ],
            )
        if "reconciliation" in lower:
            return seed(
                "React reconciliation is the process React uses to figure out what changed between one render and the next so it can update the UI efficiently. Instead of rebuilding the whole DOM, React compares the new virtual tree with the previous one and applies only the necessary updates.",
                "Reconciliation is React's process for comparing the previous render output with the next one and deciding what must actually change in the DOM. At a high level, React builds a new virtual representation, compares it with the old one, and reuses or replaces parts based on element type, position, and keys. This is why keys matter in lists and why stable component structure improves predictable updates. The goal of reconciliation is not magic speed in every case, but efficient, structured UI updates without manual diffing by the developer.",
                [
                    "Reconciliation compares one render tree with the next",
                    "React updates only the parts of the DOM that need to change",
                    "Keys influence how list items are matched during reconciliation",
                    "The process makes UI updates more structured and efficient",
                ],
            )
        if "useeffect" in lower:
            return seed(
                "I would use useEffect when a component needs to synchronize with something outside the pure render path, like data fetching, subscriptions, timers, or manual DOM integration. Common mistakes include putting derived render logic inside useEffect, missing dependencies, or creating effects that rerun unnecessarily and cause loops.",
                "Use useEffect when the component needs a side effect, meaning work that should happen after rendering rather than during pure render calculation. Typical examples are fetching data, subscribing to external events, starting timers, or integrating with browser APIs. Common mistakes are missing dependencies, including unstable dependencies that cause repeated reruns, forgetting cleanup for subscriptions or timers, and using useEffect for logic that should really be computed directly during render. A strong answer should make it clear that useEffect is for synchronization with the outside world, not for every piece of component logic.",
                [
                    "useEffect is for side effects after rendering",
                    "Typical uses include fetching, subscriptions, timers, and external APIs",
                    "Dependency mistakes can cause stale values or rerender loops",
                    "Cleanup is important for subscriptions and timers",
                ],
            )
        if "keys in lists" in lower:
            return seed(
                "Keys help React identify which list items are the same between renders. That matters because React can then update, move, or remove items more predictably instead of confusing one item with another. Stable keys improve correctness and help reconciliation work properly, especially when list order changes.",
                "Keys in React lists give each rendered item a stable identity across renders. During reconciliation, React uses keys to decide whether an item was added, removed, moved, or updated. Without good keys, React may reuse the wrong component instance or cause unnecessary rerenders and state bugs. That is why stable IDs from the data are usually the best choice, while array indexes are risky when the list can reorder or items can be inserted in the middle.",
                [
                    "Keys give list items stable identity across renders",
                    "React uses keys during reconciliation to match items correctly",
                    "Stable keys improve correctness and reduce state bugs",
                    "Array indexes are a weak choice when list order can change",
                ],
            )

    return None


def build_marking_rubric(question_type):
    return {
        "weights": TYPE_MARKING.get(question_type, TYPE_MARKING["concept"]),
        "pass_threshold": 60,
        "strong_threshold": 78,
        "dimensions": {
            "correctness": "Reward factual accuracy, correct distinctions, and absence of contradictions.",
            "coverage": "Reward the required points for the question, not just jargon or partial recall.",
            "reasoning": "Reward explanation of why, tradeoffs, constraints, or decision logic.",
            "structure": "Reward a direct answer first, then explanation, then example or tradeoff.",
        },
        "score_bands": {
            "excellent": "85-100: correct, complete, well-reasoned, and interview-ready.",
            "good": "70-84: mostly correct with minor omissions or limited depth.",
            "partial": "55-69: directionally right but missing important points or structure.",
            "weak": "0-54: inaccurate, vague, off-topic, or mostly repeated prompt language.",
        },
        "penalties": [
            "Prompt repetition without original explanation",
            "Confidently incorrect technical statements",
            "Buzzword-heavy answers with little reasoning",
            "Skipping tradeoffs when the question explicitly asks for comparison, design, or decisions",
        ],
        "notes": "Judge correctness first, then coverage, then reasoning and structure. Do not reward jargon if the core explanation is wrong.",
    }


def build_behavioral_answer(question_text):
    lower = question_text.lower()
    if "failed" in lower:
        return (
            "In one project, I underestimated the integration effort and we slipped the timeline. "
            "I took ownership, communicated the risk early, broke the work into smaller checkpoints, and added clearer validation before handoff. "
            "The result was that we recovered the delivery and I learned to surface uncertainty sooner instead of assuming it would resolve itself."
        )
    if "disagreement" in lower:
        return (
            "I once had a strong disagreement with a teammate about the right implementation path. "
            "Instead of arguing from opinion, I proposed that we compare the options against performance, maintainability, and delivery risk, and we reviewed the tradeoffs together. "
            "That led to a better decision and reinforced that productive disagreement works best when you align on criteria instead of ego."
        )
    if "leadership" in lower:
        return (
            "In one project, there was no formal owner for a risky part of the release, so I stepped in to organize the work. "
            "I aligned people on the plan, clarified dependencies, and kept communication tight until the uncertainty dropped. "
            "The project shipped more smoothly, and it showed me that leadership is often about creating clarity before it is about authority."
        )
    if "deadline" in lower or "pressure" in lower:
        return (
            "When I work under pressure, I first separate what is critical from what is optional. "
            "Then I communicate tradeoffs clearly, reduce context switching, and keep progress visible so the team can react early if something slips. "
            "That helps me stay calm and deliver without pretending that every task has the same priority."
        )
    return (
        "I would answer this using a clear STAR structure. "
        "First I would set the situation briefly, then explain the action I personally took, and end with a concrete result plus what I learned. "
        "That keeps the answer grounded, honest, and easy for an interviewer to follow."
    )


def build_sample_answer(question_text, topic_id, question_type):
    guidance = QUESTION_GUIDANCE.get(normalize_question_key(question_text))
    if guidance and guidance.get("sample_answer"):
        return guidance["sample_answer"]
    topic_seed = build_topic_specific_seed(question_text, topic_id)
    if topic_seed and topic_seed.get("sample_answer"):
        return topic_seed["sample_answer"]

    subject = extract_answer_subject(question_text)
    subjects = extract_comparison_subjects(question_text)
    context = topic_context(topic_id)

    if question_type == "behavioral":
        return build_behavioral_answer(question_text)
    if question_type == "comparison" and subjects:
        joined = f"{subjects[0]} and {subjects[1]}" if len(subjects) == 2 else ", ".join(subjects[:-1]) + f", and {subjects[-1]}"
        return (
            f"{joined.capitalize()} are related concepts, but they are not interchangeable. "
            f"The main distinction usually comes down to how they affect {context['focus']}. "
            f"In practice, the better choice depends on {context['tradeoff']}."
        )
    if question_type == "process":
        return (
            f"{subject.capitalize()} usually works as a sequence of steps rather than a single definition. "
            f"The flow typically depends on {context['components'][0]}, {context['components'][1]}, and how they interact over time. "
            f"What matters in practice is how that process affects {context['focus']}."
        )
    if question_type == "design":
        return (
            f"{subject.capitalize()} should be designed around a clear system goal, a small set of core components such as {', '.join(context['components'][:3])}, and a request or data flow that is easy to reason about. "
            f"The main design tradeoff usually sits around {context['tradeoff']}."
        )
    if question_type == "complexity":
        return (
            f"{subject.capitalize()} has to be explained together with its cost profile. "
            f"The important part is the time complexity, the space cost, and the reason the underlying steps create that behavior. "
            f"In practice, the tradeoff is tied to {context['tradeoff']}."
        )
    if question_type == "tradeoff":
        return (
            f"{subject.capitalize()} is really about balancing benefits against limitations. "
            f"It is useful because it improves one side of the problem, but it also creates cost elsewhere. "
            f"The right choice depends on {context['tradeoff']}."
        )
    if question_type == "decision":
        return (
            f"I would choose {subject} when the system cares most about the conditions behind {context['focus']}. "
            f"The decision is justified by the tradeoff around {context['tradeoff']}, not by one rule that fits every case."
        )
    return (
        f"{subject.capitalize()} is part of {context['area']}. At a high level, it matters because it shapes {context['focus']}. "
        f"In practice, it usually comes up when engineers need to reason about {context['components'][0]} and {context['components'][1]}. "
        f"A complete answer should also mention the tradeoff around {context['tradeoff']}."
    )


def build_ideal_answer(question_text, topic_id, question_type):
    guidance = QUESTION_GUIDANCE.get(normalize_question_key(question_text))
    if guidance:
        return guidance.get("ideal_answer") or guidance.get("sample_answer", "")
    topic_seed = build_topic_specific_seed(question_text, topic_id)
    if topic_seed and topic_seed.get("ideal_answer"):
        return topic_seed["ideal_answer"]

    subject = extract_answer_subject(question_text)
    subjects = extract_comparison_subjects(question_text)
    context = topic_context(topic_id)

    if question_type == "behavioral":
        return (
            "A strong behavioral answer should be specific, chronological, and owned by the candidate. "
            "It should make the situation clear, describe the action in enough detail to show judgment, and end with a measurable result or reflection."
        )
    if question_type == "comparison" and subjects:
        joined = f"{subjects[0]} and {subjects[1]}" if len(subjects) == 2 else ", ".join(subjects[:-1]) + f", and {subjects[-1]}"
        return (
            f"{joined.capitalize()} should be compared by defining each one clearly, then separating them by scope, behavior, or use case. "
            f"The strongest answers also connect the comparison back to {context['tradeoff']}."
        )
    if question_type == "design":
        return (
            f"{subject.capitalize()} should be explained through the system goal, the main components, the request path, the data path, and one important tradeoff around {context['tradeoff']}. "
            f"The answer is strongest when it shows system thinking instead of just naming tools."
        )
    if question_type == "process":
        return (
            f"{subject.capitalize()} should be explained step by step: first the goal, then the main operations, then the reason the sequence works. "
            f"The best answers also connect the flow back to {context['focus']} and a practical use case."
        )
    if question_type == "complexity":
        return (
            f"{subject.capitalize()} should be explained with both time and space complexity, plus the mechanism that causes those costs. "
            f"A complete answer also mentions when that tradeoff is acceptable in practice."
        )
    return (
        f"{subject.capitalize()} belongs to {context['area']}, and a strong answer should explain the core idea, how it affects {context['focus']}, and where it matters in practice. "
        f"The best answers also mention a concrete use case and one tradeoff around {context['tradeoff']}."
    )


def build_question_record(question_text, topic_id, difficulty, display_order):
    guidance = QUESTION_GUIDANCE.get(normalize_question_key(question_text))
    topic_seed = build_topic_specific_seed(question_text, topic_id)
    question_type = question_type_for(question_text, topic_id)

    if guidance:
        core_points = [point["label"] for point in guidance.get("points", [])]
        common_mistakes = [point["label"] for point in guidance.get("mistakes", [])] or build_common_mistakes(question_text, topic_id, question_type)
        sample_answer = guidance.get("sample_answer", "")
        ideal_answer = guidance.get("ideal_answer") or sample_answer
        optional_points = build_optional_points(question_text, topic_id, question_type)
        reasoning_steps = build_reasoning_steps(question_text, topic_id, question_type)
    elif topic_seed:
        core_points = topic_seed.get("core_points") or build_generic_core_points(question_text, topic_id, question_type)
        common_mistakes = topic_seed.get("common_mistakes") or build_common_mistakes(question_text, topic_id, question_type)
        sample_answer = topic_seed.get("sample_answer", "")
        ideal_answer = topic_seed.get("ideal_answer") or sample_answer
        optional_points = topic_seed.get("optional_points") or build_optional_points(question_text, topic_id, question_type)
        reasoning_steps = topic_seed.get("reasoning_steps") or build_reasoning_steps(question_text, topic_id, question_type)
    else:
        core_points = build_generic_core_points(question_text, topic_id, question_type)
        common_mistakes = build_common_mistakes(question_text, topic_id, question_type)
        sample_answer = build_sample_answer(question_text, topic_id, question_type)
        ideal_answer = build_ideal_answer(question_text, topic_id, question_type)
        optional_points = build_optional_points(question_text, topic_id, question_type)
        reasoning_steps = build_reasoning_steps(question_text, topic_id, question_type)

    return {
        "question_id": f"{topic_id}_{display_order:03d}",
        "topic_id": topic_id,
        "question_text": question_text,
        "question_type": question_type,
        "difficulty": difficulty,
        "display_order": display_order,
        "estimated_answer_seconds": estimated_seconds(difficulty),
        "sample_answer": sample_answer,
        "ideal_answer": ideal_answer,
        "core_points": core_points,
        "optional_points": optional_points,
        "common_mistakes": common_mistakes,
        "reasoning_steps": reasoning_steps,
        "marking_rubric": build_marking_rubric(question_type),
        "tags": [topic_id, difficulty, question_type],
    }


def generate_sql():
    question_bank = parse_question_bank()
    question_counts = {topic["topic_id"]: len(question_bank.get(topic["topic_id"], [])) for topic in TOPIC_CATALOG}
    question_rows = []
    for topic in TOPIC_CATALOG:
        for display_order, item in enumerate(question_bank.get(topic["topic_id"], []), start=1):
            question_rows.append(build_question_record(item["question_text"], topic["topic_id"], item["difficulty"], display_order))

    lines = []
    lines.append("-- AUTH2_SCHEMA.sql")
    lines.append("-- Full runnable schema for the mock interview app, including auth, sessions, role-wise interviews, and a seeded question bank with answers and rubric data.")
    lines.append("")
    lines.append("CREATE DATABASE IF NOT EXISTS interview_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    lines.append("USE interview_db;")
    lines.append("")
    lines.append("CREATE TABLE IF NOT EXISTS users (")
    lines.append("    id INT AUTO_INCREMENT PRIMARY KEY,")
    lines.append("    user_id VARCHAR(36) UNIQUE NOT NULL,")
    lines.append("    username VARCHAR(50) UNIQUE NOT NULL,")
    lines.append("    email VARCHAR(255) UNIQUE NOT NULL,")
    lines.append("    password_salt VARCHAR(32) NOT NULL,")
    lines.append("    password_hash VARCHAR(128) NOT NULL,")
    lines.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
    lines.append("    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    lines.append(");")
    lines.append("")
    lines.append("CREATE TABLE IF NOT EXISTS topics (")
    lines.append("    id INT AUTO_INCREMENT PRIMARY KEY,")
    lines.append("    topic_id VARCHAR(100) UNIQUE NOT NULL,")
    lines.append("    category VARCHAR(100) NOT NULL,")
    lines.append("    title VARCHAR(150) NOT NULL,")
    lines.append("    subtitle VARCHAR(255) NOT NULL,")
    lines.append("    description TEXT NOT NULL,")
    lines.append("    level_label VARCHAR(100) NOT NULL,")
    lines.append("    accent VARCHAR(100) NOT NULL,")
    lines.append("    question_count INT NOT NULL DEFAULT 0,")
    lines.append("    is_active BOOLEAN NOT NULL DEFAULT TRUE,")
    lines.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
    lines.append("    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,")
    lines.append("    INDEX idx_topics_category (category),")
    lines.append("    INDEX idx_topics_active (is_active)")
    lines.append(");")
    lines.append("")
    lines.append("CREATE TABLE IF NOT EXISTS job_roles (")
    lines.append("    id INT AUTO_INCREMENT PRIMARY KEY,")
    lines.append("    role_id VARCHAR(100) UNIQUE NOT NULL,")
    lines.append("    title VARCHAR(150) NOT NULL,")
    lines.append("    subtitle VARCHAR(255) NOT NULL,")
    lines.append("    description TEXT NOT NULL,")
    lines.append("    level_label VARCHAR(100) NOT NULL,")
    lines.append("    default_duration_minutes INT NOT NULL DEFAULT 30,")
    lines.append("    available_durations JSON NOT NULL,")
    lines.append("    is_active BOOLEAN NOT NULL DEFAULT TRUE,")
    lines.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
    lines.append("    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,")
    lines.append("    INDEX idx_job_roles_active (is_active)")
    lines.append(");")
    lines.append("")
    lines.append("CREATE TABLE IF NOT EXISTS role_topic_weights (")
    lines.append("    id INT AUTO_INCREMENT PRIMARY KEY,")
    lines.append("    role_id VARCHAR(100) NOT NULL,")
    lines.append("    topic_id VARCHAR(100) NOT NULL,")
    lines.append("    weight INT NOT NULL DEFAULT 10,")
    lines.append("    is_core BOOLEAN NOT NULL DEFAULT FALSE,")
    lines.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
    lines.append("    UNIQUE KEY uq_role_topic (role_id, topic_id),")
    lines.append("    CONSTRAINT fk_role_topic_weights_role FOREIGN KEY (role_id) REFERENCES job_roles(role_id) ON DELETE CASCADE,")
    lines.append("    CONSTRAINT fk_role_topic_weights_topic FOREIGN KEY (topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE,")
    lines.append("    INDEX idx_role_topic_weights_role (role_id),")
    lines.append("    INDEX idx_role_topic_weights_topic (topic_id)")
    lines.append(");")
    lines.append("")
    lines.append("CREATE TABLE IF NOT EXISTS questions (")
    lines.append("    id INT AUTO_INCREMENT PRIMARY KEY,")
    lines.append("    question_id VARCHAR(100) UNIQUE NOT NULL,")
    lines.append("    topic_id VARCHAR(100) NOT NULL,")
    lines.append("    question_text TEXT NOT NULL,")
    lines.append("    question_type VARCHAR(50) NOT NULL DEFAULT 'concept',")
    lines.append("    difficulty ENUM('easy', 'medium', 'hard') NOT NULL DEFAULT 'medium',")
    lines.append("    display_order INT NOT NULL DEFAULT 0,")
    lines.append("    estimated_answer_seconds INT NOT NULL DEFAULT 60,")
    lines.append("    sample_answer TEXT NULL,")
    lines.append("    ideal_answer TEXT NULL,")
    lines.append("    core_points JSON NULL,")
    lines.append("    optional_points JSON NULL,")
    lines.append("    common_mistakes JSON NULL,")
    lines.append("    reasoning_steps JSON NULL,")
    lines.append("    marking_rubric JSON NULL,")
    lines.append("    tags JSON NULL,")
    lines.append("    is_active BOOLEAN NOT NULL DEFAULT TRUE,")
    lines.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
    lines.append("    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,")
    lines.append("    CONSTRAINT fk_questions_topic FOREIGN KEY (topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE,")
    lines.append("    INDEX idx_questions_topic (topic_id),")
    lines.append("    INDEX idx_questions_difficulty (difficulty),")
    lines.append("    INDEX idx_questions_type (question_type),")
    lines.append("    INDEX idx_questions_active (is_active)")
    lines.append(");")
    lines.append("")
    lines.append("CREATE TABLE IF NOT EXISTS interviews (")
    lines.append("    id INT AUTO_INCREMENT PRIMARY KEY,")
    lines.append("    session_id VARCHAR(64) UNIQUE NOT NULL,")
    lines.append("    user_id VARCHAR(36) NULL,")
    lines.append("    topic VARCHAR(100) NOT NULL,")
    lines.append("    session_mode VARCHAR(20) NOT NULL DEFAULT 'topic',")
    lines.append("    role_id VARCHAR(100) NULL,")
    lines.append("    session_title VARCHAR(150) NULL,")
    lines.append("    duration_minutes INT NOT NULL DEFAULT 30,")
    lines.append("    final_score INT NOT NULL,")
    lines.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
    lines.append("    complete_data JSON NOT NULL,")
    lines.append("    INDEX idx_interviews_user_id (user_id),")
    lines.append("    INDEX idx_interviews_role_id (role_id),")
    lines.append("    INDEX idx_interviews_session_mode (session_mode),")
    lines.append("    CONSTRAINT fk_interviews_user_id FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL")
    lines.append(");")
    lines.append("")
    lines.append("CREATE TABLE IF NOT EXISTS topic_ratings (")
    lines.append("    id INT AUTO_INCREMENT PRIMARY KEY,")
    lines.append("    session_id VARCHAR(64) UNIQUE NOT NULL,")
    lines.append("    user_id VARCHAR(36) NULL,")
    lines.append("    topic_id VARCHAR(100) NOT NULL,")
    lines.append("    rating TINYINT NOT NULL,")
    lines.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
    lines.append("    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,")
    lines.append("    INDEX idx_topic_ratings_topic_id (topic_id),")
    lines.append("    INDEX idx_topic_ratings_user_id (user_id),")
    lines.append("    CONSTRAINT fk_topic_ratings_session_id FOREIGN KEY (session_id) REFERENCES interviews(session_id) ON DELETE CASCADE,")
    lines.append("    CONSTRAINT fk_topic_ratings_user_id FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL")
    lines.append(");")
    lines.append("")
    lines.append("CREATE TABLE IF NOT EXISTS topic_activity (")
    lines.append("    id INT AUTO_INCREMENT PRIMARY KEY,")
    lines.append("    session_id VARCHAR(64) UNIQUE NOT NULL,")
    lines.append("    user_id VARCHAR(36) NOT NULL,")
    lines.append("    topic_id VARCHAR(100) NOT NULL,")
    lines.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
    lines.append("    INDEX idx_topic_activity_topic_id (topic_id),")
    lines.append("    INDEX idx_topic_activity_user_id (user_id),")
    lines.append("    CONSTRAINT fk_topic_activity_session_id FOREIGN KEY (session_id) REFERENCES interviews(session_id) ON DELETE CASCADE,")
    lines.append("    CONSTRAINT fk_topic_activity_user_id FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE")
    lines.append(");")
    lines.append("")
    lines.append("-- Seed topics")
    lines.append("INSERT INTO topics (topic_id, category, title, subtitle, description, level_label, accent, question_count, is_active) VALUES")
    lines.append(",\n".join(
        "    (" + ", ".join([
            sql_string(topic["topic_id"]),
            sql_string(topic["category"]),
            sql_string(topic["title"]),
            sql_string(topic["subtitle"]),
            sql_string(topic["description"]),
            sql_string(topic["level_label"]),
            sql_string(topic["accent"]),
            str(question_counts[topic["topic_id"]]),
            "1",
        ]) + ")"
        for topic in TOPIC_CATALOG
    ))
    lines.append("ON DUPLICATE KEY UPDATE category = VALUES(category), title = VALUES(title), subtitle = VALUES(subtitle), description = VALUES(description), level_label = VALUES(level_label), accent = VALUES(accent), question_count = VALUES(question_count), is_active = VALUES(is_active);")
    lines.append("")
    lines.append("-- Seed job roles")
    lines.append("INSERT INTO job_roles (role_id, title, subtitle, description, level_label, default_duration_minutes, available_durations, is_active) VALUES")
    lines.append(",\n".join(
        "    (" + ", ".join([
            sql_string(role["role_id"]),
            sql_string(role["title"]),
            sql_string(role["subtitle"]),
            sql_string(role["description"]),
            sql_string(role["level_label"]),
            str(int(role["default_duration"])),
            sql_json(role["available_durations"]),
            "1",
        ]) + ")"
        for role in ROLE_CATALOG
    ))
    lines.append("ON DUPLICATE KEY UPDATE title = VALUES(title), subtitle = VALUES(subtitle), description = VALUES(description), level_label = VALUES(level_label), default_duration_minutes = VALUES(default_duration_minutes), available_durations = VALUES(available_durations), is_active = VALUES(is_active);")
    lines.append("")
    lines.append("-- Seed role to topic weights")
    weight_rows = []
    for role in ROLE_CATALOG:
        sorted_topics = sorted(role["topic_weights"].items(), key=lambda entry: entry[1], reverse=True)
        core_ids = {topic_id for topic_id, _ in sorted_topics[:2]}
        for topic_id, weight in sorted_topics:
            weight_rows.append(
                "    (" + ", ".join([
                    sql_string(role["role_id"]),
                    sql_string(topic_id),
                    str(int(weight)),
                    "1" if topic_id in core_ids else "0",
                ]) + ")"
            )
    lines.append("INSERT INTO role_topic_weights (role_id, topic_id, weight, is_core) VALUES")
    lines.append(",\n".join(weight_rows))
    lines.append("ON DUPLICATE KEY UPDATE weight = VALUES(weight), is_core = VALUES(is_core);")
    lines.append("")
    lines.append("-- Seed questions with answers and rubric data")
    lines.append("INSERT INTO questions (question_id, topic_id, question_text, question_type, difficulty, display_order, estimated_answer_seconds, sample_answer, ideal_answer, core_points, optional_points, common_mistakes, reasoning_steps, marking_rubric, tags, is_active) VALUES")
    lines.append(",\n".join(
        "    (" + ", ".join([
            sql_string(record["question_id"]),
            sql_string(record["topic_id"]),
            sql_string(record["question_text"]),
            sql_string(record["question_type"]),
            sql_string(record["difficulty"]),
            str(record["display_order"]),
            str(record["estimated_answer_seconds"]),
            sql_string(record["sample_answer"]),
            sql_string(record["ideal_answer"]),
            sql_json(record["core_points"]),
            sql_json(record["optional_points"]),
            sql_json(record["common_mistakes"]),
            sql_json(record["reasoning_steps"]),
            sql_json(record["marking_rubric"]),
            sql_json(record["tags"]),
            "1",
        ]) + ")"
        for record in question_rows
    ))
    lines.append("ON DUPLICATE KEY UPDATE question_text = VALUES(question_text), question_type = VALUES(question_type), difficulty = VALUES(difficulty), display_order = VALUES(display_order), estimated_answer_seconds = VALUES(estimated_answer_seconds), sample_answer = VALUES(sample_answer), ideal_answer = VALUES(ideal_answer), core_points = VALUES(core_points), optional_points = VALUES(optional_points), common_mistakes = VALUES(common_mistakes), reasoning_steps = VALUES(reasoning_steps), marking_rubric = VALUES(marking_rubric), tags = VALUES(tags), is_active = VALUES(is_active);")
    lines.append("")
    lines.append("-- This seed gives every question a stable id, answer text, reasoning steps, and marking rubric. You can still manually improve individual rows later.")
    return "\n".join(lines) + "\n"


def main():
    OUTPUT_PATH.write_text(generate_sql(), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
