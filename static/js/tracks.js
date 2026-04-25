import {
  createTopicCard,
  getTotalQuestionCount,
  getTopicCategories,
  loadInterviewCatalog,
  loadTopicSummary,
  startTopicInterview,
} from "./catalog.js"

const topicGrid = document.getElementById("topic-grid")
const searchInput = document.getElementById("topic-search")
const searchButton = document.getElementById("topic-search-btn")
const resultSummaryEl = document.getElementById("catalog-summary")
const topicFilterGroup = document.getElementById("topic-filter-group")
const topicFilterSummary = document.getElementById("topic-filter-summary")
const tracksTopicCount = document.getElementById("tracks-topic-count")
const tracksQuestionCount = document.getElementById("tracks-question-count")

let topicRatings = {}
let topicActivity = {}
let topicCatalog = []
let activeCategory = "all"

function attachTopicActions() {
  topicGrid.querySelectorAll("[data-topic-id]").forEach(button => {
    button.addEventListener("click", () => {
      startTopicInterview(button.dataset.topicId)
    })
  })
}

function renderTopicFilters() {
  if (!topicFilterGroup) return

  const categories = getTopicCategories(topicCatalog)
  topicFilterGroup.innerHTML = categories.map(category => `
    <button
      type="button"
      class="filter-pill ${activeCategory === category ? "is-active" : ""}"
      data-category-filter="${category}"
    >
      ${category === "all" ? "All tracks" : category}
    </button>
  `).join("")

  topicFilterGroup.querySelectorAll("[data-category-filter]").forEach(button => {
    button.addEventListener("click", () => {
      activeCategory = button.dataset.categoryFilter || "all"
      renderTopicFilters()
      renderCatalog(searchInput?.value || "")
    })
  })
}

function renderCatalog(query = "") {
  const normalized = query.trim().toLowerCase()
  const visibleTopics = topicCatalog.filter(topic => {
    const categoryMatch = activeCategory === "all" || String(topic.category || "").toLowerCase() === activeCategory.toLowerCase()
    if (!categoryMatch) return false

    if (!normalized) return true

    return [
      topic.title,
      topic.subtitle,
      topic.description,
      topic.category,
      topic.level_label,
    ].some(value => String(value || "").toLowerCase().includes(normalized))
  })

  if (!visibleTopics.length) {
    topicGrid.innerHTML = `
      <div class="topic-empty-state">
        <h4>No matching tracks</h4>
        <p>Try a broader keyword like backend, systems, AI, frontend, database, or behavioral.</p>
      </div>
    `
  } else {
    topicGrid.innerHTML = visibleTopics.map(topic => createTopicCard(topic, topicRatings, topicActivity)).join("")
    attachTopicActions()
  }

  if (resultSummaryEl) {
    resultSummaryEl.innerText = normalized
      ? `${visibleTopics.length} tracks found for "${query.trim()}"`
      : `${topicCatalog.length} interview tracks available`
  }

  if (topicFilterSummary) {
    const filterLabel = activeCategory === "all" ? "all tracks" : `${activeCategory} tracks`
    topicFilterSummary.innerText = normalized
      ? `Showing ${visibleTopics.length} results in ${filterLabel}`
      : `Showing ${visibleTopics.length} ${filterLabel}`
  }
}

function runSearch() {
  renderCatalog(searchInput?.value || "")
}

async function loadTracksPage() {
  try {
    const [{ topics }, { ratings, activity }] = await Promise.all([
      loadInterviewCatalog(),
      loadTopicSummary(),
    ])

    topicCatalog = topics
    topicRatings = ratings
    topicActivity = activity

    const totalQuestions = getTotalQuestionCount(topicCatalog)

    if (tracksTopicCount) {
      tracksTopicCount.innerText = `${topicCatalog.length} topic tracks`
    }

    if (tracksQuestionCount) {
      tracksQuestionCount.innerText = `${totalQuestions}+ prompts`
    }

    renderTopicFilters()
    renderCatalog(searchInput?.value || "")
  } catch (error) {
    console.error("Failed to load tracks page", error)
    topicGrid.innerHTML = `
      <div class="topic-empty-state">
        <h4>Catalog unavailable</h4>
        <p>The interview catalog could not be loaded from the backend right now.</p>
      </div>
    `

    if (resultSummaryEl) {
      resultSummaryEl.innerText = "Catalog unavailable"
    }
  }
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

loadTracksPage()
