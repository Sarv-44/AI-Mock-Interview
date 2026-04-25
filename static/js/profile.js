import { authenticatedFetch, clearCurrentUser, getCurrentUser, renderAppbarAccount } from "./session.js"

const historyContent = document.getElementById("history-content")
const profileName = document.getElementById("profile-name")
const profileCopy = document.getElementById("profile-copy")
const profileEmail = document.getElementById("profile-email")
const profileMemberSince = document.getElementById("profile-member-since")
const profileUserId = document.getElementById("profile-user-id")
const profileNextStep = document.getElementById("profile-next-step")
const profileHistoryCount = document.getElementById("profile-history-count")
const profileLatestTopic = document.getElementById("profile-latest-topic")

function formatDate(dateValue) {
  if (!dateValue) return "-"

  const parsed = new Date(dateValue)
  if (Number.isNaN(parsed.getTime())) return "-"

  return parsed.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  })
}

function buildSummaryFromSession(session) {
  const details = session.complete_data || {}

  return {
    topic: session.topic || details.topic || "Interview Session",
    sessionTitle: details.session_title || details.role_title || session.topic || "Interview Session",
    sessionMode: details.session_mode || session.session_mode || "topic",
    roleId: details.role_id || session.role_id || null,
    customTemplateId: details.custom_template_id || null,
    durationMinutes: details.duration_minutes || 30,
    finalScore: session.final_score ?? details.final_score ?? 0,
    questionsTotal: details.questions_total || details.questions?.length || 0,
    confidenceHistory: details.confidence_history || [],
    wpmHistory: details.wpm_history || [],
    fillerHistory: details.filler_history || [],
    targetSecondsHistory: details.target_seconds_history || details.questions?.map(question => question.target_seconds || 0) || [],
    timeDeltaHistory: details.time_delta_history || details.questions?.map(question => question.time_target_delta_seconds || 0) || [],
    timeStatusHistory: details.time_status_history || details.questions?.map(question => question.time_target_status || "not_set") || [],
    sessionId: session.session_id,
    userId: session.user_id || details.user_id || null
  }
}

async function openSavedReport(sessionId) {
  try {
    const response = await authenticatedFetch(`/get-session/${sessionId}`)
    const result = await response.json()

    if (!result.success || !result.data) {
      throw new Error(result.error || "Failed to load session")
    }

    const summary = buildSummaryFromSession(result.data)
    localStorage.setItem("interviewSummary", JSON.stringify(summary))
    localStorage.setItem("sessionId", summary.sessionId)
    window.location.href = "/results"
  } catch (error) {
    alert("Unable to open that saved report right now.")
  }
}

async function downloadSavedPdf(sessionId) {
  try {
    const response = await authenticatedFetch(`/generate-pdf/${sessionId}`)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const contentDisposition = response.headers.get("content-disposition")
    let filename = `interview_report_${sessionId}.pdf`

    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="(.+)"/)
      if (filenameMatch) {
        filename = filenameMatch[1]
      }
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const anchor = document.createElement("a")
    anchor.href = url
    anchor.download = filename
    document.body.appendChild(anchor)
    anchor.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(anchor)
  } catch (error) {
    alert("Unable to download that PDF right now.")
  }
}

function renderEmptyState(title, copy, ctaHref = null, ctaLabel = null) {
  const currentUser = getCurrentUser()
  const resolvedHref = ctaHref ?? (currentUser?.user_id ? "/" : "/auth")
  const resolvedLabel = ctaLabel ?? (currentUser?.user_id ? "Browse topics" : "Go to sign in")

  const actionMarkup = resolvedHref && resolvedLabel
    ? `<a href="${resolvedHref}" class="primary-action">${resolvedLabel}</a>`
    : ""

  historyContent.innerHTML = `
    <div class="history-empty-state">
      <h4>${title}</h4>
      <p>${copy}</p>
      ${actionMarkup}
    </div>
  `
}

function renderHistory(history) {
  if (!history.length) {
    renderEmptyState(
      "No saved interviews yet",
      "Complete and save your first interview while signed in, then it will appear here with quick access to the report and PDF.",
      "/",
      "Browse topics"
    )
    profileHistoryCount.innerText = "0"
    profileLatestTopic.innerText = "-"
    return
  }

  profileHistoryCount.innerText = String(history.length)
  profileLatestTopic.innerText = history[0].session_title || history[0].topic?.toUpperCase() || "-"

  historyContent.innerHTML = history.map(session => `
    <article class="history-session-card">
      <div class="history-session-head">
        <div>
          <p class="section-kicker">Saved Session</p>
          <h4>${session.session_title || session.topic?.toUpperCase() || "Interview Session"}</h4>
        </div>
        <div class="status-badge">${session.final_score}/100</div>
      </div>
      <p class="history-session-copy">
        Completed ${formatDate(session.interview_date || session.created_at)} and ready to reopen as a full report.
      </p>
      <div class="history-session-meta">
        <div class="history-meta-badge">
          <span class="summary-label">Questions</span>
          <strong>${session.questions_total || 0}</strong>
        </div>
        <div class="history-meta-badge">
          <span class="summary-label">Duration</span>
          <strong>${session.duration_seconds || 0}s</strong>
        </div>
        <div class="history-meta-badge">
          <span class="summary-label">Session ID</span>
          <strong>${session.session_id}</strong>
        </div>
      </div>
      <div class="history-session-actions">
        <button type="button" class="primary-action" data-open-report="${session.session_id}">Open report</button>
        <button type="button" class="secondary-action" data-download-pdf="${session.session_id}">Download PDF</button>
      </div>
    </article>
  `).join("")

  historyContent.querySelectorAll("[data-open-report]").forEach(button => {
    button.addEventListener("click", () => openSavedReport(button.dataset.openReport))
  })

  historyContent.querySelectorAll("[data-download-pdf]").forEach(button => {
    button.addEventListener("click", () => downloadSavedPdf(button.dataset.downloadPdf))
  })
}

async function loadProfile() {
  const currentUser = getCurrentUser()

  renderAppbarAccount({
    signedOutCopy: "Sign in to view your account history.",
    signedInCopy: currentUser ? `Signed in as ${currentUser.email}` : undefined
  })

  if (!currentUser?.user_id) {
    profileName.innerText = "Guest mode"
    profileCopy.innerText = "Sign in first, then we can attach interview sessions to your account and show them here."
    profileEmail.innerText = "-"
    profileMemberSince.innerText = "-"
    profileUserId.innerText = "-"
    profileNextStep.innerText = "Create or access your account"
    renderEmptyState(
      "You are not signed in",
      "Use the auth page to create an account or sign in. After that, your saved interviews will show up here."
    )
    return
  }

  try {
    const [userResponse, historyResponse] = await Promise.all([
      authenticatedFetch(`/api/auth/users/${currentUser.user_id}`),
      authenticatedFetch(`/api/auth/users/${currentUser.user_id}/history`)
    ])

    if (userResponse.status === 401 || historyResponse.status === 401) {
      clearCurrentUser()
      profileName.innerText = "Session expired"
      profileCopy.innerText = "Please sign in again to reopen your saved profile and interview history."
      profileEmail.innerText = "-"
      profileMemberSince.innerText = "-"
      profileUserId.innerText = "-"
      profileNextStep.innerText = "Sign in again"
      renderAppbarAccount()
      renderEmptyState(
        "Your sign-in session expired",
        "Your saved local session is no longer valid. Sign in again to reload your profile and history.",
        "/auth",
        "Go to sign in"
      )
      return
    }

    const userResult = await userResponse.json()
    const historyResult = await historyResponse.json()

    if (!userResult.success) {
      throw new Error(userResult.error || "Failed to load user")
    }

    const user = userResult.user
    const history = historyResult.success ? historyResult.history : []

    profileName.innerText = user.username
    profileCopy.innerText = "Your account is ready. Saved interview sessions show up here so you can reopen reports or export PDFs again."
    profileEmail.innerText = user.email
    profileMemberSince.innerText = formatDate(user.created_at)
    profileUserId.innerText = user.user_id
    profileNextStep.innerText = history.length ? "Review one past session and then practice again" : "Finish one new interview"

    renderHistory(history)
  } catch (error) {
    renderEmptyState(
      "We could not load your history",
      "The account is present locally, but the profile or history request failed. Try refreshing after the backend is running.",
      currentUser?.user_id ? "/" : "/auth",
      currentUser?.user_id ? "Browse topics" : "Go to sign in"
    )
  }
}

window.addEventListener("mock-auth-expired", () => {
  renderAppbarAccount()
})

loadProfile()
