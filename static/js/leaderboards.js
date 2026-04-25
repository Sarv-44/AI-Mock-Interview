import { loadInterviewCatalog } from "./catalog.js"
import { authenticatedFetch, getCurrentUser } from "./session.js"

const boardButtons = [...document.querySelectorAll("[data-board]")]
const topicSelect = document.getElementById("leaderboard-topic-select")
const statusBanner = document.getElementById("leaderboard-status-banner")
const summaryGrid = document.getElementById("leaderboard-summary-grid")
const userPanel = document.getElementById("leaderboard-user-panel")
const tableBody = document.getElementById("leaderboard-table-body")
const activeLabel = document.getElementById("leaderboard-active-label")
const thresholdLabel = document.getElementById("leaderboard-threshold-label")
const userCountLabel = document.getElementById("leaderboard-user-count")
const tableTitle = document.getElementById("leaderboard-table-title")
const tableCopy = document.getElementById("leaderboard-table-copy")
const topicPicker = document.getElementById("leaderboard-topic-picker")
const topicHelper = document.getElementById("leaderboard-topic-helper")

const state = {
  board: "overall",
  topicId: "",
  topics: [],
  isLoading: false,
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;")
}

function setStatus(message, tone = "neutral") {
  if (statusBanner) {
    statusBanner.textContent = message
    statusBanner.dataset.tone = tone
  }
}

function getBoardLabel(board, topicTitle = "") {
  if (board === "weekly") return "Weekly score"
  if (board === "topic") return topicTitle ? `${topicTitle} score` : "Topic score"
  return "Overall score"
}

function formatDateTime(value) {
  if (!value) return "-"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })
}

function updateControls() {
  boardButtons.forEach(button => {
    button.classList.toggle("is-active", button.dataset.board === state.board)
    button.setAttribute("aria-pressed", String(button.dataset.board === state.board))
    button.disabled = state.isLoading
  })

  if (topicSelect) {
    topicSelect.disabled = state.board !== "topic" || state.isLoading || !state.topics.length
  }
  if (topicPicker) {
    topicPicker.classList.toggle("is-active", state.board === "topic")
  }
  if (topicHelper) {
    topicHelper.textContent = state.board === "topic"
      ? (state.topics.length ? "Pick the topic you want to rank." : "Topics are unavailable right now.")
      : "Switch to topic mode to rank one topic lane at a time."
  }
}

function renderTopicOptions() {
  if (!topicSelect) return

  topicSelect.innerHTML = `
    <option value="">Choose a topic</option>
    ${state.topics.map(topic => `<option value="${topic.topic_id}">${escapeHtml(topic.title)}</option>`).join("")}
  `

  if (!state.topicId && state.topics.length) {
    state.topicId = state.topics[0].topic_id
  }

  topicSelect.value = state.topicId
}

function renderSummary(result) {
  if (!summaryGrid) return

  const topEntry = result.entries?.[0] || null
  const secondEntry = result.entries?.[1] || null
  const thirdEntry = result.entries?.[2] || null
  const topicTitle = result.topic?.title || ""

  if (!topEntry) {
    summaryGrid.innerHTML = `
      <div class="leaderboard-empty-state compact">
        <p>No ranked users qualify for this board yet. Finish a few more saved interviews to populate it.</p>
      </div>
    `
    return
  }

  summaryGrid.innerHTML = `
    <article class="leaderboard-summary-card">
      <span class="summary-label">Top Performer</span>
      <strong>${escapeHtml(topEntry.display_name)}</strong>
      <p>${escapeHtml(topEntry.average_score)} average across ${escapeHtml(topEntry.interview_count)} attempts</p>
    </article>
    <article class="leaderboard-summary-card">
      <span class="summary-label">Board Focus</span>
      <strong>${escapeHtml(getBoardLabel(result.board, topicTitle))}</strong>
      <p>${result.timeframe_days ? `Last ${result.timeframe_days} days only` : "All eligible saved sessions"}</p>
    </article>
    <article class="leaderboard-summary-card">
      <span class="summary-label">Chasing Pack</span>
      <strong>${escapeHtml(secondEntry?.display_name || thirdEntry?.display_name || "Building...")}</strong>
      <p>${escapeHtml(result.total_ranked_users)} ranked user${result.total_ranked_users === 1 ? "" : "s"} currently qualify</p>
    </article>
  `
}

function renderUserPanel(result) {
  if (!userPanel) return

  const currentUser = getCurrentUser()
  if (!currentUser?.user_id) {
    userPanel.innerHTML = `
      <div class="leaderboard-empty-state">
        <h4>Sign in to see your exact rank</h4>
        <p>You can still browse the public leaderboard now, but your personal placement only appears for signed-in accounts.</p>
      </div>
    `
    return
  }

  const currentEntry = result.current_user_entry
  const progress = result.current_user_progress

  if (currentEntry) {
    userPanel.innerHTML = `
      <article class="leaderboard-user-spotlight">
        <span class="summary-label">Current Rank</span>
        <strong>#${escapeHtml(currentEntry.rank)}</strong>
        <p>${escapeHtml(currentEntry.average_score)} average score across ${escapeHtml(currentEntry.interview_count)} eligible attempts.</p>
      </article>
      <div class="leaderboard-user-stats">
        <article class="leaderboard-user-stat">
          <span class="summary-label">Board Entry</span>
          <strong>${escapeHtml(currentEntry.display_name)}</strong>
        </article>
        <article class="leaderboard-user-stat">
          <span class="summary-label">Latest Session</span>
          <strong>${escapeHtml(formatDateTime(currentEntry.latest_session_at))}</strong>
        </article>
      </div>
    `
    return
  }

  const attempts = progress?.interview_count || 0
  const minimum = progress?.minimum_interviews || result.minimum_interviews || 0
  const missing = Math.max(0, minimum - attempts)
  userPanel.innerHTML = `
    <div class="leaderboard-empty-state">
      <h4>Not ranked on this board yet</h4>
      <p>You have ${attempts} qualifying attempt${attempts === 1 ? "" : "s"} on this board. You need ${minimum} to appear in the rankings.</p>
      <p>${missing > 0 ? `${missing} more saved interview${missing === 1 ? "" : "s"} will unlock your rank.` : "Finish another session to refresh your placement."}</p>
    </div>
  `
}

function renderTable(result) {
  if (!tableBody) return

  const topicTitle = result.topic?.title || ""
  if (tableTitle) {
    tableTitle.textContent = result.title || "Leaderboard table"
  }
  if (tableCopy) {
    tableCopy.textContent = topicTitle
      ? `Entries here only count pure topic-track interviews for ${topicTitle}.`
      : "Entries are anonymous unless the row belongs to the currently signed-in user."
  }

  if (!result.entries?.length) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="5">
          <div class="leaderboard-empty-state compact">
            <p>No one qualifies for this board yet. Finish and save more interviews to populate it.</p>
          </div>
        </td>
      </tr>
    `
    return
  }

  tableBody.innerHTML = result.entries.map(entry => `
    <tr class="${entry.is_current_user ? "is-current-user" : ""}">
      <td>
        <span class="leaderboard-rank-badge ${entry.rank <= 3 ? "is-top" : ""}">
          #${escapeHtml(entry.rank)}
        </span>
      </td>
      <td>
        <div class="leaderboard-name-cell">
          ${entry.is_current_user ? `<span class="leaderboard-user-dot" aria-hidden="true"></span>` : ""}
          <div>
            <div class="${entry.is_current_user ? "leaderboard-table-copy-strong" : ""}">${escapeHtml(entry.display_name)}</div>
            <small>${entry.is_current_user ? "Your account" : "Anonymous competitor"}</small>
          </div>
        </div>
      </td>
      <td><span class="leaderboard-score">${escapeHtml(entry.average_score)}</span></td>
      <td>${escapeHtml(entry.interview_count)}</td>
      <td>${escapeHtml(formatDateTime(entry.latest_session_at))}</td>
    </tr>
  `).join("")
}

async function fetchLeaderboard() {
  state.isLoading = true
  updateControls()
  try {
    const params = new URLSearchParams({
      board: state.board,
      limit: "10",
    })

    if (state.board === "topic" && state.topicId) {
      params.set("topic_id", state.topicId)
    }

    setStatus("Loading leaderboard data...", "loading")
    const response = await authenticatedFetch(`/api/leaderboards?${params.toString()}`)
    const result = await response.json()

    if (!response.ok || !result.success) {
      throw new Error(result.detail || result.error || "Leaderboard request failed")
    }

    const topicTitle = result.topic?.title || ""
    if (activeLabel) activeLabel.textContent = getBoardLabel(result.board, topicTitle)
    if (thresholdLabel) thresholdLabel.textContent = `${result.minimum_interviews}+ saved interviews`
    if (userCountLabel) userCountLabel.textContent = String(result.total_ranked_users || 0)

    setStatus(
      result.timeframe_days
        ? `Showing ranked users from the last ${result.timeframe_days} days.`
        : result.topic
          ? `Showing topic-track ranking for ${result.topic.title}.`
          : "Showing ranked users across all saved interview modes.",
      "neutral"
    )

    renderSummary(result)
    renderUserPanel(result)
    renderTable(result)
  } catch (error) {
    const message = error instanceof Error ? error.message : "Leaderboard loading failed"
    setStatus(message, "error")
    if (summaryGrid) {
      summaryGrid.innerHTML = `
        <div class="leaderboard-empty-state compact">
          <p>${escapeHtml(message)}</p>
        </div>
      `
    }
    if (userPanel) {
      userPanel.innerHTML = `
        <div class="leaderboard-empty-state">
          <h4>Leaderboard unavailable</h4>
          <p>${escapeHtml(message)}</p>
        </div>
      `
    }
    if (tableBody) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="5">
            <div class="leaderboard-empty-state compact">
              <p>${escapeHtml(message)}</p>
            </div>
          </td>
        </tr>
      `
    }
  } finally {
    state.isLoading = false
    updateControls()
  }
}

async function initializeLeaderboards() {
  try {
    const { topics } = await loadInterviewCatalog()
    state.topics = topics
    renderTopicOptions()
  } catch (_error) {
    if (topicSelect) {
      topicSelect.innerHTML = `<option value="">Topics unavailable</option>`
    }
  }

  updateControls()
  await fetchLeaderboard()
}

boardButtons.forEach(button => {
  button.addEventListener("click", async () => {
    if (state.isLoading) return
    state.board = button.dataset.board || "overall"
    if (state.board === "topic" && !state.topicId && state.topics.length) {
      state.topicId = state.topics[0].topic_id
      if (topicSelect) topicSelect.value = state.topicId
    }
    if (state.board === "topic" && !state.topics.length) {
      updateControls()
      setStatus("Topic boards are temporarily unavailable because the topic catalog could not be loaded.", "error")
      return
    }
    updateControls()
    await fetchLeaderboard()
  })
})

if (topicSelect) {
  topicSelect.addEventListener("change", async () => {
    state.topicId = topicSelect.value
    if (state.board === "topic") {
      await fetchLeaderboard()
    }
  })
}

initializeLeaderboards()
