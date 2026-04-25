import {
  createPreviewRoleCard,
  createPreviewTopicCard,
  getTotalQuestionCount,
  loadInterviewCatalog,
  loadTopicSummary,
  startRoleInterview,
  startTopicInterview,
} from "./catalog.js"

const homeTopicCount = document.getElementById("home-topic-count")
const homeRoleCount = document.getElementById("home-role-count")
const homeQuestionCount = document.getElementById("home-question-count")
const featuredTopicRoot = document.getElementById("featured-topic-root")
const featuredRoleRoot = document.getElementById("featured-role-root")

function attachPreviewActions() {
  document.querySelectorAll("[data-topic-id]").forEach(button => {
    button.addEventListener("click", () => {
      startTopicInterview(button.dataset.topicId)
    })
  })

  document.querySelectorAll("[data-role-id]").forEach(button => {
    button.addEventListener("click", () => {
      startRoleInterview(button.dataset.roleId, 30)
    })
  })
}

async function loadHomeContent() {
  try {
    const [{ topics, roles }, { ratings, activity }] = await Promise.all([
      loadInterviewCatalog(),
      loadTopicSummary(),
    ])

    const totalQuestions = getTotalQuestionCount(topics)
    const featuredTopic = topics[0] || null
    const featuredRole = roles[0] || null

    if (homeTopicCount) {
      homeTopicCount.innerText = `${topics.length} practice tracks`
    }

    if (homeRoleCount) {
      homeRoleCount.innerText = `${roles.length} role rounds`
    }

    if (homeQuestionCount) {
      homeQuestionCount.innerText = `${totalQuestions}+ curated prompts`
    }

    if (featuredTopicRoot) {
      featuredTopicRoot.innerHTML = createPreviewTopicCard(featuredTopic, ratings, activity)
    }

    if (featuredRoleRoot) {
      featuredRoleRoot.innerHTML = createPreviewRoleCard(featuredRole)
    }

    attachPreviewActions()
  } catch (error) {
    console.error("Failed to load home content", error)

    if (homeTopicCount) {
      homeTopicCount.innerText = "Catalog unavailable"
    }

    if (homeRoleCount) {
      homeRoleCount.innerText = "Catalog unavailable"
    }

    if (homeQuestionCount) {
      homeQuestionCount.innerText = "Try again later"
    }

    if (featuredTopicRoot) {
      featuredTopicRoot.innerHTML = `<p class="preview-empty">The topic catalog could not be loaded right now.</p>`
    }

    if (featuredRoleRoot) {
      featuredRoleRoot.innerHTML = `<p class="preview-empty">The role catalog could not be loaded right now.</p>`
    }
  }
}

loadHomeContent()
