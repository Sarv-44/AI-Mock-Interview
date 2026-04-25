import { topics } from "./questions.js"

const TOPIC_CATALOG = [
  { id: "graphs", category: "Algorithms", title: "Graph Algorithms", subtitle: "Traversal, shortest paths, and graph reasoning", description: "Practice core graph interview questions spanning traversal, shortest path, connectivity, and graph optimization.", level: "Intermediate to Advanced", accent: "graphs" },
  { id: "datastructures", category: "Core CS", title: "Data Structures", subtitle: "Trees, heaps, maps, queues, and caches", description: "Sharpen the explanations interviewers expect around common data structures and practical tradeoffs.", level: "Beginner to Advanced", accent: "datastructures" },
  { id: "sorting", category: "Algorithms", title: "Sorting Algorithms", subtitle: "Complexity, stability, and strategy selection", description: "Build stronger answers about sorting internals, performance tradeoffs, and real-world use cases.", level: "Intermediate", accent: "sorting" },
  { id: "dp", category: "Problem Solving", title: "Dynamic Programming", subtitle: "Memoization, states, and transitions", description: "Train how to recognize dynamic programming patterns and explain them under interview pressure.", level: "Intermediate to Advanced", accent: "dp" },
  { id: "database", category: "Backend", title: "Databases", subtitle: "SQL, indexing, replication, and schema design", description: "Practice questions on storage systems, query optimization, transactions, and data modeling.", level: "Intermediate", accent: "database" },
  { id: "systemdesign", category: "Architecture", title: "System Design", subtitle: "Scalability, APIs, queues, and caching", description: "Prepare for senior interview rounds with system design prompts covering availability, scale, and tradeoffs.", level: "Advanced", accent: "systemdesign" },
  { id: "behavioral", category: "Leadership", title: "Behavioral", subtitle: "Leadership, ownership, and teamwork", description: "Practice structured storytelling for behavioral questions using outcomes, reflection, and impact.", level: "All levels", accent: "behavioral" },
  { id: "python", category: "Language", title: "Python Fundamentals", subtitle: "Language behavior, memory, and idioms", description: "Strengthen your explanations of Python features, runtime behavior, and engineering best practices.", level: "Beginner to Advanced", accent: "python" },
  { id: "os", category: "Systems", title: "OS and Concurrency", subtitle: "Processes, threads, memory, and scheduling", description: "Drill into the operating systems concepts that repeatedly show up in systems interviews.", level: "Intermediate to Advanced", accent: "os" },
  { id: "java", category: "Language", title: "Java", subtitle: "JVM, collections, memory, and idioms", description: "Practice the Java concepts most often discussed in backend and enterprise interview loops.", level: "Beginner to Advanced", accent: "java" },
  { id: "javascript", category: "Frontend", title: "JavaScript", subtitle: "Closures, async flow, and browser fundamentals", description: "Improve your explanations of the event loop, scope, memory, and real-world JavaScript behavior.", level: "Beginner to Advanced", accent: "javascript" },
  { id: "react", category: "Frontend", title: "React", subtitle: "State, rendering, hooks, and architecture", description: "Prepare for modern frontend interviews with a focused React practice track.", level: "Intermediate", accent: "react" },
  { id: "nodejs", category: "Backend", title: "Node.js", subtitle: "Event loop, streams, and production APIs", description: "Work through Node.js questions around concurrency, performance, and server design.", level: "Intermediate", accent: "nodejs" },
  { id: "machinelearning", category: "AI/ML", title: "Machine Learning", subtitle: "Models, evaluation, and production tradeoffs", description: "Practice explaining learning workflows, model performance, and deployment risks clearly.", level: "Intermediate to Advanced", accent: "machinelearning" },
  { id: "genai", category: "AI/ML", title: "Generative AI", subtitle: "LLMs, RAG, prompting, and evaluation", description: "Train for modern AI interviews with questions on LLM products, retrieval, safety, and cost tradeoffs.", level: "Intermediate to Advanced", accent: "genai" },
  { id: "cloud", category: "Cloud", title: "Cloud Architecture", subtitle: "Scalability, resilience, and cloud operations", description: "Practice the cloud concepts that show up in backend, platform, and infrastructure interviews.", level: "Intermediate to Advanced", accent: "cloud" },
  { id: "networking", category: "Systems", title: "Networking", subtitle: "TCP/IP, DNS, TLS, and latency", description: "Strengthen your ability to explain the network behavior behind distributed applications.", level: "Intermediate", accent: "networking" },
  { id: "security", category: "Security", title: "Application Security", subtitle: "Auth, secrets, browser risk, and defense in depth", description: "Build sharper answers on practical security topics that matter in engineering interviews.", level: "Intermediate to Advanced", accent: "security" },
  { id: "testing", category: "Engineering", title: "Testing Strategies", subtitle: "Unit, integration, end-to-end, and reliability", description: "Practice how to talk about software quality, confidence, and high-value test design.", level: "Intermediate", accent: "testing" },
  { id: "devops", category: "Platform", title: "DevOps", subtitle: "CI/CD, observability, deployments, and operations", description: "Prepare for platform and delivery questions around release safety, reliability, and scale.", level: "Intermediate to Advanced", accent: "devops" },
  { id: "apis", category: "Backend", title: "API Design", subtitle: "Contracts, versioning, pagination, and resilience", description: "Practice modern API interview questions spanning REST, GraphQL, idempotency, and reliability.", level: "Intermediate", accent: "apis" }
]

const topicGrid = document.getElementById("topic-grid")
const searchInput = document.getElementById("topic-search")
const searchButton = document.getElementById("topic-search-btn")
const topicCountEl = document.getElementById("topic-count")
const questionCountEl = document.getElementById("question-count")
const resultSummaryEl = document.getElementById("catalog-summary")

let topicRatings = {}
let topicActivity = {}

const totalQuestionCount = Object.values(topics).reduce((sum, topicQuestions) => sum + topicQuestions.length, 0)

function createCard(topic) {
  const questionCount = topics[topic.id]?.length ?? 0
  const ratingData = topicRatings[topic.id]
  const activityData = topicActivity[topic.id]
  const ratingLabel = ratingData?.rating_count ? `${ratingData.average_rating}/5` : "No ratings yet"
  const ratingMeta = ratingData?.rating_count ? `${ratingData.rating_count} ratings` : "Rate after a completed session"
  const activityLabel = activityData?.interview_count
    ? `${activityData.interview_count} signed-in interviews completed`
    : "No signed-in interviews yet"

  return `
    <button class="topic-card ${topic.accent}" data-topic-id="${topic.id}" type="button">
      <div class="topic-card-hero">
        <div>
          <div class="topic-chip">${topic.category}</div>
          <div class="topic-hero-title">${topic.title}</div>
          <div class="topic-hero-subtitle">${topic.subtitle}</div>
        </div>
        <div class="topic-rating">
          <strong>${ratingLabel}</strong>
          <span>${ratingMeta}</span>
        </div>
      </div>
      <div class="topic-card-body">
        <h4 class="topic-title">${topic.title}</h4>
        <p class="topic-description">${topic.description}</p>
        <div class="topic-detail-row">
          <span>${topic.level}</span>
          <span>${questionCount} interview questions</span>
        </div>
        <div class="topic-footer-row">
          <span class="topic-popularity">${activityLabel}</span>
          <span class="topic-cta">Explore track</span>
        </div>
      </div>
    </button>
  `
}

function renderCatalog(query = "") {
  const normalized = query.trim().toLowerCase()

  const visibleTopics = TOPIC_CATALOG.filter(topic => {
    if (!normalized) return true

    return [
      topic.title,
      topic.subtitle,
      topic.description,
      topic.category,
      topic.level
    ].some(value => value.toLowerCase().includes(normalized))
  })

  if (!visibleTopics.length) {
    topicGrid.innerHTML = `
      <div class="topic-empty-state">
        <h4>No matching tracks</h4>
        <p>Try a broader keyword like backend, systems, AI, or frontend.</p>
      </div>
    `
  } else {
    topicGrid.innerHTML = visibleTopics.map(createCard).join("")
  }

  if (resultSummaryEl) {
    resultSummaryEl.innerText = normalized
      ? `${visibleTopics.length} tracks found for "${query.trim()}"`
      : `${TOPIC_CATALOG.length} interview tracks available`
  }

  topicGrid.querySelectorAll("[data-topic-id]").forEach(button => {
    button.addEventListener("click", () => {
      const selectedTopic = button.dataset.topicId
      localStorage.setItem("selectedTopic", selectedTopic)
      window.location.href = "/interview"
    })
  })
}

function runSearch() {
  renderCatalog(searchInput?.value || "")
}

async function loadTopicSummary() {
  try {
    const response = await fetch("/api/topics/summary")
    const result = await response.json()
    if (!result.success) return

    topicRatings = Object.fromEntries(
      (result.ratings || []).map(entry => [entry.topic_id, entry])
    )
    topicActivity = Object.fromEntries(
      (result.activity || []).map(entry => [entry.topic_id, entry])
    )

    renderCatalog(searchInput?.value || "")
  } catch (error) {
    console.error("Failed to load topic summary", error)
  }
}

if (topicCountEl) {
  topicCountEl.innerText = `${TOPIC_CATALOG.length} practice tracks`
}

if (questionCountEl) {
  questionCountEl.innerText = `${totalQuestionCount}+ curated interview prompts`
}

if (searchButton) {
  searchButton.addEventListener("click", runSearch)
}

if (searchInput) {
  searchInput.addEventListener("keydown", event => {
    if (event.key === "Enter") {
      event.preventDefault()
      runSearch()
    }
  })
}

renderCatalog()
loadTopicSummary()
