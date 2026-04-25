import { authenticatedFetch, getCurrentUser } from "./session.js"

const accessRoot = document.getElementById("admin-access-root")
const workspace = document.getElementById("admin-workspace")
const entityButtonsRoot = document.getElementById("admin-entity-stack")
const editorTitle = document.getElementById("admin-editor-title")
const globalStatus = document.getElementById("admin-global-status")

const overviewSection = document.getElementById("admin-section-overview")
const usersSection = document.getElementById("admin-section-users")
const sessionsSection = document.getElementById("admin-section-sessions")
const metricUsers = document.getElementById("admin-metric-users")
const metricAdminUsers = document.getElementById("admin-metric-admin-users")
const metricSessions = document.getElementById("admin-metric-sessions")
const metricSessions7d = document.getElementById("admin-metric-sessions-7d")
const metricActiveUsers = document.getElementById("admin-metric-active-users")
const metricCustomTemplates = document.getElementById("admin-metric-custom-templates")
const metricAverageScore = document.getElementById("admin-metric-average-score")
const modeBreakdownRoot = document.getElementById("admin-mode-breakdown")
const topTopicBreakdownRoot = document.getElementById("admin-top-topic-breakdown")
const catalogHealthRoot = document.getElementById("admin-catalog-health")
const opsNotesRoot = document.getElementById("admin-ops-notes")
const usersTableBody = document.getElementById("admin-users-table-body")
const sessionsTableBody = document.getElementById("admin-sessions-table-body")
const usersSummaryTotal = document.getElementById("admin-users-summary-total")
const usersSummaryActive = document.getElementById("admin-users-summary-active")
const usersSummaryAdmins = document.getElementById("admin-users-summary-admins")
const sessionsSummaryTotal = document.getElementById("admin-sessions-summary-total")
const sessionsSummaryRecent = document.getElementById("admin-sessions-summary-recent")
const sessionsSummaryScore = document.getElementById("admin-sessions-summary-score")

const topicsCount = document.getElementById("admin-topics-count")
const questionsCount = document.getElementById("admin-questions-count")
const rolesCount = document.getElementById("admin-roles-count")

const topicSection = document.getElementById("admin-section-topics")
const topicBrowser = document.getElementById("admin-topic-browser")
const topicSelect = document.getElementById("admin-topic-select")
const topicSearchInput = document.getElementById("admin-topic-search")
const topicStatusFilter = document.getElementById("admin-topic-status-filter")
const topicStateChip = document.getElementById("admin-topic-state-chip")
const topicArchiveBtn = document.getElementById("admin-topic-archive-btn")
const topicRestoreBtn = document.getElementById("admin-topic-restore-btn")
const topicDeleteBtn = document.getElementById("admin-topic-delete-btn")
const topicForm = document.getElementById("admin-topic-form")
const topicIdInput = document.getElementById("admin-topic-id")
const topicCategoryInput = document.getElementById("admin-topic-category")
const topicTitleInput = document.getElementById("admin-topic-title")
const topicSubtitleInput = document.getElementById("admin-topic-subtitle")
const topicDescriptionInput = document.getElementById("admin-topic-description")
const topicLevelInput = document.getElementById("admin-topic-level")
const topicAccentInput = document.getElementById("admin-topic-accent")
const topicResetButton = document.getElementById("admin-topic-reset")

const questionSection = document.getElementById("admin-section-questions")
const questionBrowser = document.getElementById("admin-question-browser")
const questionFilterTopic = document.getElementById("admin-question-filter-topic")
const questionSelect = document.getElementById("admin-question-select")
const questionSearchInput = document.getElementById("admin-question-search")
const questionStatusFilter = document.getElementById("admin-question-status-filter")
const questionStateChip = document.getElementById("admin-question-state-chip")
const questionArchiveBtn = document.getElementById("admin-question-archive-btn")
const questionRestoreBtn = document.getElementById("admin-question-restore-btn")
const questionDeleteBtn = document.getElementById("admin-question-delete-btn")
const questionForm = document.getElementById("admin-question-form")
const questionIdInput = document.getElementById("admin-question-id")
const questionTopicSelect = document.getElementById("admin-question-topic")
const questionOrderInput = document.getElementById("admin-question-order")
const questionDifficultySelect = document.getElementById("admin-question-difficulty")
const questionTextInput = document.getElementById("admin-question-text")
const questionSampleInput = document.getElementById("admin-question-sample")
const questionIdealInput = document.getElementById("admin-question-ideal")
const questionResetButton = document.getElementById("admin-question-reset")

const roleSection = document.getElementById("admin-section-roles")
const roleBrowser = document.getElementById("admin-role-browser")
const roleSelect = document.getElementById("admin-role-select")
const roleSearchInput = document.getElementById("admin-role-search")
const roleStatusFilter = document.getElementById("admin-role-status-filter")
const roleStateChip = document.getElementById("admin-role-state-chip")
const roleArchiveBtn = document.getElementById("admin-role-archive-btn")
const roleRestoreBtn = document.getElementById("admin-role-restore-btn")
const roleDeleteBtn = document.getElementById("admin-role-delete-btn")
const roleForm = document.getElementById("admin-role-form")
const roleIdInput = document.getElementById("admin-role-id")
const roleTitleInput = document.getElementById("admin-role-title")
const roleSubtitleInput = document.getElementById("admin-role-subtitle")
const roleDescriptionInput = document.getElementById("admin-role-description")
const roleLevelInput = document.getElementById("admin-role-level")
const roleDefaultDurationInput = document.getElementById("admin-role-default-duration")
const roleAvailableDurationsInput = document.getElementById("admin-role-available-durations")
const rolePrimaryTopicSelect = document.getElementById("admin-role-primary-topic")
const roleWeightsRoot = document.getElementById("admin-role-topic-weights")
const roleWeightTotal = document.getElementById("admin-role-weight-total")
const roleResetButton = document.getElementById("admin-role-reset")

const entityTitles = {
  overview: "Admin overview",
  users: "User activity",
  sessions: "Recent sessions",
  topics: "Topic manager",
  questions: "Question manager",
  roles: "Role manager",
}

const state = {
  activeEntity: "overview",
  modes: { topics: "add", questions: "add", roles: "add" },
  selected: { topics: "", questions: "", roles: "" },
  filters: {
    topics: { query: "", status: "active" },
    questions: { query: "", status: "active", topicId: "all" },
    roles: { query: "", status: "active" },
  },
  topics: [],
  questions: [],
  roles: [],
  insights: {
    overview: {
      total_users: 0,
      admin_users: 0,
      total_sessions: 0,
      active_users_7d: 0,
      sessions_7d: 0,
      custom_templates: 0,
      average_score: 0,
    },
    mode_breakdown: [],
    top_topics: [],
    recent_sessions: [],
    users: [],
  },
}

function slugify(value) {
  return String(value || "").toLowerCase().trim().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "")
}

function normalizeQuery(value) {
  return String(value || "").toLowerCase().trim()
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;")
}

function formatDateTime(value) {
  if (!value) return "-"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })
}

function formatModeLabel(value) {
  const raw = String(value || "").trim()
  if (!raw) return "-"
  return raw
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ")
}

function setGlobalStatus(message, tone = "neutral") {
  if (!globalStatus) return
  globalStatus.innerText = message
  globalStatus.dataset.tone = tone
}

function renderAccessCard(title, copy, actions = []) {
  if (!accessRoot) return
  const actionsMarkup = actions.length
    ? `<div class="admin-access-actions">${actions.map(action => `<a href="${action.href}" class="${action.className || "secondary-action"}">${action.label}</a>`).join("")}</div>`
    : ""
  accessRoot.innerHTML = `<h3>${title}</h3><p>${copy}</p>${actionsMarkup}`
}

function getTopicById(topicId) {
  return state.topics.find(topic => topic.topic_id === topicId) || null
}

function getQuestionById(questionId) {
  return state.questions.find(question => question.question_id === questionId) || null
}

function getRoleById(roleId) {
  return state.roles.find(role => role.role_id === roleId) || null
}

function getStatusLabel(record) {
  return record?.is_active ? "Active" : "Archived"
}

function matchesStatus(record, statusFilter) {
  if (statusFilter === "all") return true
  if (statusFilter === "active") return Boolean(record?.is_active)
  return !record?.is_active
}

function topicSearchText(topic) {
  return [topic.topic_id, topic.title, topic.category, topic.subtitle, topic.description].join(" ").toLowerCase()
}

function roleSearchText(role) {
  return [role.role_id, role.title, role.subtitle, role.description].join(" ").toLowerCase()
}

function questionSearchText(question) {
  const topic = getTopicById(question.topic_id)
  return [question.question_id, question.topic_id, topic?.title || "", question.question_text, question.sample_answer, question.ideal_answer].join(" ").toLowerCase()
}

function getVisibleTopics() {
  const query = normalizeQuery(state.filters.topics.query)
  return state.topics.filter(topic => matchesStatus(topic, state.filters.topics.status) && (!query || topicSearchText(topic).includes(query)))
}

function getVisibleQuestions() {
  const query = normalizeQuery(state.filters.questions.query)
  return state.questions.filter(question => {
    if (!matchesStatus(question, state.filters.questions.status)) return false
    if (state.filters.questions.topicId !== "all" && question.topic_id !== state.filters.questions.topicId) return false
    return !query || questionSearchText(question).includes(query)
  })
}

function getVisibleRoles() {
  const query = normalizeQuery(state.filters.roles.query)
  return state.roles.filter(role => matchesStatus(role, state.filters.roles.status) && (!query || roleSearchText(role).includes(query)))
}

function renderCounts() {
  const activeTopics = state.topics.filter(topic => topic.is_active).length
  const activeQuestions = state.questions.filter(question => question.is_active).length
  const activeRoles = state.roles.filter(role => role.is_active).length
  if (topicsCount) topicsCount.innerText = `${activeTopics}/${state.topics.length}`
  if (questionsCount) questionsCount.innerText = `${activeQuestions}/${state.questions.length}`
  if (rolesCount) rolesCount.innerText = `${activeRoles}/${state.roles.length}`
}

function renderOverview() {
  const overview = state.insights.overview || {}
  if (metricUsers) metricUsers.innerText = String(overview.total_users || 0)
  if (metricAdminUsers) metricAdminUsers.innerText = String(overview.admin_users || 0)
  if (metricSessions) metricSessions.innerText = String(overview.total_sessions || 0)
  if (metricSessions7d) metricSessions7d.innerText = String(overview.sessions_7d || 0)
  if (metricActiveUsers) metricActiveUsers.innerText = String(overview.active_users_7d || 0)
  if (metricCustomTemplates) metricCustomTemplates.innerText = String(overview.custom_templates || 0)
  if (metricAverageScore) metricAverageScore.innerText = String(overview.average_score || 0)

  if (modeBreakdownRoot) {
    const rows = Array.isArray(state.insights.mode_breakdown) ? state.insights.mode_breakdown : []
    modeBreakdownRoot.innerHTML = rows.length
      ? rows.map(item => `
          <div class="admin-stack-row">
            <div>
              <strong>${escapeHtml(formatModeLabel(item.session_mode))}</strong>
              <p>${Number(item.session_count || 0)} sessions</p>
            </div>
            <span>${Number(item.average_score || 0)} avg</span>
          </div>
        `).join("")
      : `<p class="hero-text">No saved session data yet.</p>`
  }

  if (topTopicBreakdownRoot) {
    const rows = Array.isArray(state.insights.top_topics) ? state.insights.top_topics : []
    topTopicBreakdownRoot.innerHTML = rows.length
      ? rows.map(item => `
          <div class="admin-stack-row">
            <div>
              <strong>${escapeHtml(item.topic || "-")}</strong>
              <p>${Number(item.session_count || 0)} sessions</p>
            </div>
            <span>${Number(item.average_score || 0)} avg</span>
          </div>
        `).join("")
      : `<p class="hero-text">Topic activity will appear after interviews are saved.</p>`
  }

  if (catalogHealthRoot) {
    const activeTopics = state.topics.filter(topic => topic.is_active).length
    const archivedTopics = state.topics.length - activeTopics
    const activeQuestions = state.questions.filter(question => question.is_active).length
    const activeRoles = state.roles.filter(role => role.is_active).length
    catalogHealthRoot.innerHTML = `
      <div class="admin-stack-row">
        <div>
          <strong>Topics live</strong>
          <p>${activeTopics} active, ${archivedTopics} archived</p>
        </div>
        <span>${state.topics.length}</span>
      </div>
      <div class="admin-stack-row">
        <div>
          <strong>Questions live</strong>
          <p>Prompt inventory currently available to plans</p>
        </div>
        <span>${activeQuestions}</span>
      </div>
      <div class="admin-stack-row">
        <div>
          <strong>Role rounds live</strong>
          <p>Active mixed interview lanes</p>
        </div>
        <span>${activeRoles}</span>
      </div>
    `
  }

  if (opsNotesRoot) {
    const notes = []
    if ((overview.active_users_7d || 0) === 0) {
      notes.push({ title: "No active users in 7 days", detail: "Usage looks quiet. Check sign-in flow, landing clarity, or whether users are returning after their first session." })
    }
    if ((overview.sessions_7d || 0) > 0 && (overview.average_score || 0) < 55) {
      notes.push({ title: "Scores are trending low", detail: "Review whether prompts are too hard, role mixes are too aggressive, or analysis expectations need tuning." })
    }
    if (state.questions.filter(question => question.is_active).length < 10) {
      notes.push({ title: "Question bank is still thin", detail: "A small active prompt pool can make practice feel repetitive, especially in role mode." })
    }
    if (!notes.length) {
      notes.push({ title: "System looks balanced", detail: "Usage, content, and score health do not show an obvious issue from this snapshot." })
      notes.push({ title: "Next useful check", detail: "Open Sessions and confirm that the latest saved runs still cover a healthy mix of topics and modes." })
    }

    opsNotesRoot.innerHTML = notes.map(note => `
      <div class="admin-stack-row admin-stack-row-note">
        <div>
          <strong>${escapeHtml(note.title)}</strong>
          <p>${escapeHtml(note.detail)}</p>
        </div>
      </div>
    `).join("")
  }
}

function renderUsersView() {
  if (!usersTableBody) return
  const users = Array.isArray(state.insights.users) ? state.insights.users : []
  const overview = state.insights.overview || {}
  if (usersSummaryTotal) usersSummaryTotal.innerText = String(overview.total_users || users.length || 0)
  if (usersSummaryActive) usersSummaryActive.innerText = String(overview.active_users_7d || 0)
  if (usersSummaryAdmins) usersSummaryAdmins.innerText = String(overview.admin_users || users.filter(user => user.is_admin).length || 0)
  usersTableBody.innerHTML = users.length
    ? users.map(user => `
        <tr>
          <td>
            <strong>${escapeHtml(user.username || "-")}</strong>
            <div class="admin-table-subcopy">${escapeHtml(user.email || "")}</div>
          </td>
          <td>${user.is_admin ? "Admin" : "Member"}</td>
          <td>${Number(user.session_count || 0)}</td>
          <td>${Number(user.sessions_7d || 0)}</td>
          <td>${Number(user.average_score || 0)}</td>
          <td>${escapeHtml(formatDateTime(user.latest_session_at || user.created_at))}</td>
        </tr>
      `).join("")
    : `<tr><td colspan="6">No users found yet.</td></tr>`
}

function renderSessionsView() {
  if (!sessionsTableBody) return
  const sessions = Array.isArray(state.insights.recent_sessions) ? state.insights.recent_sessions : []
  const overview = state.insights.overview || {}
  if (sessionsSummaryTotal) sessionsSummaryTotal.innerText = String(overview.total_sessions || 0)
  if (sessionsSummaryRecent) sessionsSummaryRecent.innerText = String(overview.sessions_7d || 0)
  if (sessionsSummaryScore) sessionsSummaryScore.innerText = String(overview.average_score || 0)
  sessionsTableBody.innerHTML = sessions.length
    ? sessions.map(session => `
        <tr>
          <td>${escapeHtml(formatDateTime(session.created_at))}</td>
          <td>
            <strong>${escapeHtml(session.username || "Guest")}</strong>
            <div class="admin-table-subcopy">${escapeHtml(session.email || session.user_id || "")}</div>
          </td>
          <td>${escapeHtml(formatModeLabel(session.session_mode))}</td>
          <td>
            <strong>${escapeHtml(session.session_title || session.topic || session.role_id || "-")}</strong>
            <div class="admin-table-subcopy">${escapeHtml(session.topic || session.role_id || "")}</div>
          </td>
          <td>${Number(session.questions_total || 0)}</td>
          <td>${Number(session.final_score || 0)}</td>
        </tr>
      `).join("")
    : `<tr><td colspan="6">No recent interview sessions found.</td></tr>`
}

function renderEntityButtons() {
  if (!entityButtonsRoot) return
  entityButtonsRoot.querySelectorAll("[data-entity]").forEach(button => {
    button.classList.toggle("is-active", button.dataset.entity === state.activeEntity)
  })
}

function setSelectOptions(selectNode, records, selectedValue, formatter) {
  if (!selectNode) return ""
  if (!records.length) {
    selectNode.innerHTML = `<option value="">No matching records</option>`
    selectNode.value = ""
    return ""
  }
  const resolvedValue = records.some(record => formatter.value(record) === selectedValue) ? selectedValue : formatter.value(records[0])
  selectNode.innerHTML = records.map(record => `<option value="${formatter.value(record)}" ${formatter.value(record) === resolvedValue ? "selected" : ""}>${formatter.label(record)}</option>`).join("")
  selectNode.value = resolvedValue
  return resolvedValue
}

function renderTopicSelect() {
  state.selected.topics = setSelectOptions(topicSelect, getVisibleTopics(), state.selected.topics, {
    value: topic => topic.topic_id,
    label: topic => `${topic.title} (${topic.topic_id})${topic.is_active ? "" : " [Archived]"}`,
  })
}

function renderQuestionTopicOptions() {
  if (questionFilterTopic) {
    questionFilterTopic.innerHTML = `<option value="all">All topics</option>${state.topics.map(topic => `<option value="${topic.topic_id}">${topic.title}${topic.is_active ? "" : " [Archived]"}</option>`).join("")}`
    questionFilterTopic.value = state.filters.questions.topicId
  }
  if (questionTopicSelect) {
    questionTopicSelect.innerHTML = state.topics.length
      ? state.topics.map(topic => `<option value="${topic.topic_id}">${topic.title}${topic.is_active ? "" : " [Archived]"}</option>`).join("")
      : `<option value="">No topics yet</option>`
  }
}

function renderQuestionSelect() {
  state.selected.questions = setSelectOptions(questionSelect, getVisibleQuestions(), state.selected.questions, {
    value: question => question.question_id,
    label: question => {
      const topic = getTopicById(question.topic_id)
      return `${topic?.title || question.topic_id} - Q${question.display_order}${question.is_active ? "" : " [Archived]"}`
    },
  })
}

function renderRoleSelect() {
  state.selected.roles = setSelectOptions(roleSelect, getVisibleRoles(), state.selected.roles, {
    value: role => role.role_id,
    label: role => `${role.title} (${role.role_id})${role.is_active ? "" : " [Archived]"}`,
  })
}

function renderRoleTopicControls(topicWeights = {}, primaryTopicId = "") {
  if (!roleWeightsRoot || !rolePrimaryTopicSelect) return
  rolePrimaryTopicSelect.innerHTML = state.topics.length
    ? state.topics.map(topic => `<option value="${topic.topic_id}" ${topic.topic_id === primaryTopicId ? "selected" : ""}>${topic.title}${topic.is_active ? "" : " [Archived]"}</option>`).join("")
    : `<option value="">No topics yet</option>`
  roleWeightsRoot.innerHTML = state.topics.map(topic => `
    <label class="admin-weight-card">
      <div><h4>${topic.title}</h4><p>${topic.topic_id}${topic.is_active ? "" : " - Archived"}</p></div>
      <input type="number" min="0" step="1" value="${Number(topicWeights[topic.topic_id] || 0)}" data-role-weight-topic="${topic.topic_id}">
    </label>
  `).join("")
  roleWeightsRoot.querySelectorAll("[data-role-weight-topic]").forEach(input => input.addEventListener("input", updateRoleWeightTotal))
  updateRoleWeightTotal()
}

function updateRoleWeightTotal() {
  if (!roleWeightTotal || !roleWeightsRoot) return
  const total = Array.from(roleWeightsRoot.querySelectorAll("[data-role-weight-topic]")).reduce((sum, input) => {
    const value = Number(input.value)
    return sum + (Number.isFinite(value) && value > 0 ? value : 0)
  }, 0)
  roleWeightTotal.innerText = String(total)
}

function resetTopicForm() {
  topicIdInput.value = ""
  topicCategoryInput.value = ""
  topicTitleInput.value = ""
  topicSubtitleInput.value = ""
  topicDescriptionInput.value = ""
  topicLevelInput.value = "Intermediate"
  topicAccentInput.value = ""
  topicIdInput.readOnly = false
}

function fillTopicForm(topic) {
  if (!topic) return resetTopicForm()
  topicIdInput.value = topic.topic_id || ""
  topicCategoryInput.value = topic.category || ""
  topicTitleInput.value = topic.title || ""
  topicSubtitleInput.value = topic.subtitle || ""
  topicDescriptionInput.value = topic.description || ""
  topicLevelInput.value = topic.level_label || ""
  topicAccentInput.value = topic.accent || ""
  topicIdInput.readOnly = true
}

function resetQuestionForm() {
  questionIdInput.value = ""
  questionTopicSelect.value = state.topics[0]?.topic_id || ""
  questionOrderInput.value = "1"
  questionDifficultySelect.value = "medium"
  questionTextInput.value = ""
  questionSampleInput.value = ""
  questionIdealInput.value = ""
}

function fillQuestionForm(question) {
  if (!question) return resetQuestionForm()
  questionIdInput.value = question.question_id || ""
  questionTopicSelect.value = question.topic_id || state.topics[0]?.topic_id || ""
  questionOrderInput.value = String(question.display_order || 1)
  questionDifficultySelect.value = question.difficulty || "medium"
  questionTextInput.value = question.question_text || ""
  questionSampleInput.value = question.sample_answer || ""
  questionIdealInput.value = question.ideal_answer || ""
}

function resetRoleForm() {
  roleIdInput.value = ""
  roleTitleInput.value = ""
  roleSubtitleInput.value = ""
  roleDescriptionInput.value = ""
  roleLevelInput.value = "Interview loop"
  roleDefaultDurationInput.value = "30"
  roleAvailableDurationsInput.value = "15, 30, 60"
  renderRoleTopicControls({}, state.topics[0]?.topic_id || "")
  roleIdInput.readOnly = false
}

function fillRoleForm(role) {
  if (!role) return resetRoleForm()
  roleIdInput.value = role.role_id || ""
  roleTitleInput.value = role.title || ""
  roleSubtitleInput.value = role.subtitle || ""
  roleDescriptionInput.value = role.description || ""
  roleLevelInput.value = role.level_label || "Interview loop"
  roleDefaultDurationInput.value = String(role.default_duration || 30)
  roleAvailableDurationsInput.value = (role.available_durations || []).join(", ")
  renderRoleTopicControls(role.topic_weights || {}, role.primary_topic_id || "")
  roleIdInput.readOnly = true
}

function renderRecordActions(entity, record) {
  const config = {
    topics: { browser: topicBrowser, stateChip: topicStateChip, archiveBtn: topicArchiveBtn, restoreBtn: topicRestoreBtn, deleteBtn: topicDeleteBtn },
    questions: { browser: questionBrowser, stateChip: questionStateChip, archiveBtn: questionArchiveBtn, restoreBtn: questionRestoreBtn, deleteBtn: questionDeleteBtn },
    roles: { browser: roleBrowser, stateChip: roleStateChip, archiveBtn: roleArchiveBtn, restoreBtn: roleRestoreBtn, deleteBtn: roleDeleteBtn },
  }[entity]

  if (!config) return
  const isEditMode = state.modes[entity] === "edit"
  if (config.browser) config.browser.classList.toggle("is-idle", !isEditMode)
  if (config.stateChip) {
    config.stateChip.innerText = !isEditMode ? "Add mode" : record ? getStatusLabel(record) : "No match"
  }
  if (config.archiveBtn) config.archiveBtn.hidden = !isEditMode || !record || !record.is_active
  if (config.restoreBtn) config.restoreBtn.hidden = !isEditMode || !record || record.is_active
  if (config.deleteBtn) config.deleteBtn.hidden = !isEditMode || !record
}

function renderTopicEditor() {
  const topic = getTopicById(state.selected.topics)
  if (state.modes.topics === "edit") fillTopicForm(topic)
  else resetTopicForm()
  renderRecordActions("topics", topic)
}

function renderQuestionEditor() {
  const question = getQuestionById(state.selected.questions)
  if (state.modes.questions === "edit") fillQuestionForm(question)
  else resetQuestionForm()
  renderRecordActions("questions", question)
}

function renderRoleEditor() {
  const role = getRoleById(state.selected.roles)
  if (state.modes.roles === "edit") fillRoleForm(role)
  else resetRoleForm()
  renderRecordActions("roles", role)
}

function renderEditor() {
  editorTitle.innerText = entityTitles[state.activeEntity] || "Admin manager"
  if (topicSearchInput) topicSearchInput.value = state.filters.topics.query
  if (topicStatusFilter) topicStatusFilter.value = state.filters.topics.status
  if (questionSearchInput) questionSearchInput.value = state.filters.questions.query
  if (questionStatusFilter) questionStatusFilter.value = state.filters.questions.status
  if (roleSearchInput) roleSearchInput.value = state.filters.roles.query
  if (roleStatusFilter) roleStatusFilter.value = state.filters.roles.status
  if (overviewSection) overviewSection.hidden = state.activeEntity !== "overview"
  if (usersSection) usersSection.hidden = state.activeEntity !== "users"
  if (sessionsSection) sessionsSection.hidden = state.activeEntity !== "sessions"
  topicSection.hidden = state.activeEntity !== "topics"
  questionSection.hidden = state.activeEntity !== "questions"
  roleSection.hidden = state.activeEntity !== "roles"

  document.querySelectorAll(".admin-mode-button").forEach(button => {
    button.classList.toggle("is-active", state.modes[button.dataset.entityMode] === button.dataset.mode)
  })

  renderEntityButtons()
  renderCounts()
  renderTopicSelect()
  renderQuestionTopicOptions()
  renderQuestionSelect()
  renderRoleSelect()
  renderOverview()
  renderUsersView()
  renderSessionsView()
  renderTopicEditor()
  renderQuestionEditor()
  renderRoleEditor()
}

function collectTopicPayload() {
  return {
    topic_id: topicIdInput.value.trim(),
    category: topicCategoryInput.value.trim(),
    title: topicTitleInput.value.trim(),
    subtitle: topicSubtitleInput.value.trim(),
    description: topicDescriptionInput.value.trim(),
    level_label: topicLevelInput.value.trim(),
    accent: topicAccentInput.value.trim() || slugify(topicTitleInput.value || topicIdInput.value),
  }
}

function collectQuestionPayload() {
  return {
    question_id: questionIdInput.value.trim() || null,
    topic_id: questionTopicSelect.value,
    question_text: questionTextInput.value.trim(),
    difficulty: questionDifficultySelect.value,
    display_order: Number(questionOrderInput.value || 1),
    sample_answer: questionSampleInput.value.trim(),
    ideal_answer: questionIdealInput.value.trim(),
  }
}

function collectRolePayload() {
  const topicWeights = {}
  roleWeightsRoot.querySelectorAll("[data-role-weight-topic]").forEach(input => {
    const value = Number(input.value)
    if (Number.isFinite(value) && value > 0) topicWeights[input.dataset.roleWeightTopic] = Math.round(value)
  })

  return {
    role_id: roleIdInput.value.trim(),
    title: roleTitleInput.value.trim(),
    subtitle: roleSubtitleInput.value.trim(),
    description: roleDescriptionInput.value.trim(),
    level_label: roleLevelInput.value.trim(),
    default_duration: Number(roleDefaultDurationInput.value || 30),
    available_durations: roleAvailableDurationsInput.value.trim(),
    primary_topic_id: rolePrimaryTopicSelect.value,
    topic_weights: topicWeights,
  }
}

async function loadBootstrap() {
  const response = await authenticatedFetch("/api/admin/bootstrap")
  const result = await response.json()
  if (!result.success) throw new Error(result.error || "Failed to load admin data")
  state.topics = Array.isArray(result.topics) ? result.topics : []
  state.questions = Array.isArray(result.questions) ? result.questions : []
  state.roles = Array.isArray(result.roles) ? result.roles : []
  state.insights = result.insights && typeof result.insights === "object"
    ? {
        overview: result.insights.overview || state.insights.overview,
        mode_breakdown: Array.isArray(result.insights.mode_breakdown) ? result.insights.mode_breakdown : [],
        top_topics: Array.isArray(result.insights.top_topics) ? result.insights.top_topics : [],
        recent_sessions: Array.isArray(result.insights.recent_sessions) ? result.insights.recent_sessions : [],
        users: Array.isArray(result.insights.users) ? result.insights.users : [],
      }
    : state.insights
}

async function refreshBootstrap(nextSelection = {}) {
  await loadBootstrap()
  if (nextSelection.activeEntity) state.activeEntity = nextSelection.activeEntity
  if (typeof nextSelection.topicId === "string") state.selected.topics = nextSelection.topicId
  if (typeof nextSelection.questionId === "string") state.selected.questions = nextSelection.questionId
  if (typeof nextSelection.roleId === "string") state.selected.roles = nextSelection.roleId
  if (typeof nextSelection.questionFilterTopic === "string") state.filters.questions.topicId = nextSelection.questionFilterTopic
  if (typeof nextSelection.status === "string" && state.filters[nextSelection.activeEntity]) {
    state.filters[nextSelection.activeEntity].status = nextSelection.status
  }
  renderEditor()
}

async function saveEntity(url, method, payload) {
  const response = await authenticatedFetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  return response.json()
}

async function handleTopicSubmit(event) {
  event.preventDefault()
  const payload = collectTopicPayload()
  if (!payload.topic_id) return setGlobalStatus("Topic ID is required", "error")
  if (!payload.title) return setGlobalStatus("Topic title is required", "error")

  setGlobalStatus("Saving topic...", "working")
  const isEditMode = state.modes.topics === "edit"
  const result = await saveEntity(isEditMode ? `/api/admin/topics/${state.selected.topics}` : "/api/admin/topics", isEditMode ? "PUT" : "POST", payload)
  if (!result.success || !result.topic) return setGlobalStatus(result.error || "Could not save topic", "error")

  state.modes.topics = "edit"
  state.filters.topics.status = "all"
  setGlobalStatus(`Topic "${result.topic.title}" saved`, "success")
  await refreshBootstrap({ activeEntity: "topics", topicId: result.topic.topic_id, status: "all" })
}

async function handleQuestionSubmit(event) {
  event.preventDefault()
  const payload = collectQuestionPayload()
  if (!payload.topic_id) return setGlobalStatus("Choose a topic for the question", "error")
  if (!payload.question_text) return setGlobalStatus("Question text is required", "error")

  setGlobalStatus("Saving question...", "working")
  const isEditMode = state.modes.questions === "edit"
  const result = await saveEntity(isEditMode ? `/api/admin/questions/${state.selected.questions}` : "/api/admin/questions", isEditMode ? "PUT" : "POST", payload)
  if (!result.success || !result.question) return setGlobalStatus(result.error || "Could not save question", "error")

  state.modes.questions = "edit"
  state.filters.questions.status = "all"
  state.filters.questions.topicId = result.question.topic_id
  setGlobalStatus(`Question "${result.question.question_id}" saved`, "success")
  await refreshBootstrap({ activeEntity: "questions", questionId: result.question.question_id, questionFilterTopic: result.question.topic_id, status: "all" })
}

async function handleRoleSubmit(event) {
  event.preventDefault()
  const payload = collectRolePayload()
  if (!payload.role_id) return setGlobalStatus("Role ID is required", "error")
  if (!payload.title) return setGlobalStatus("Role title is required", "error")
  if (!Object.keys(payload.topic_weights).length) return setGlobalStatus("Add at least one topic weight greater than zero", "error")

  setGlobalStatus("Saving role...", "working")
  const isEditMode = state.modes.roles === "edit"
  const result = await saveEntity(isEditMode ? `/api/admin/roles/${state.selected.roles}` : "/api/admin/roles", isEditMode ? "PUT" : "POST", payload)
  if (!result.success || !result.role) return setGlobalStatus(result.error || "Could not save role", "error")

  state.modes.roles = "edit"
  state.filters.roles.status = "all"
  setGlobalStatus(`Role "${result.role.title}" saved`, "success")
  await refreshBootstrap({ activeEntity: "roles", roleId: result.role.role_id, status: "all" })
}

async function performRecordAction(entity, action) {
  const record = entity === "topics" ? getTopicById(state.selected.topics) : entity === "questions" ? getQuestionById(state.selected.questions) : getRoleById(state.selected.roles)
  if (!record) return setGlobalStatus("Pick a record first", "error")

  const displayName = record.title || record.question_id || record.topic_id || record.role_id
  const confirmed = window.confirm(action === "delete" ? `Delete "${displayName}" permanently? This cannot be undone.` : `${action === "archive" ? "Archive" : "Restore"} "${displayName}"?`)
  if (!confirmed) return

  setGlobalStatus(`${action === "delete" ? "Deleting" : action === "archive" ? "Archiving" : "Restoring"} record...`, "working")
  const id = entity === "topics" ? record.topic_id : entity === "questions" ? record.question_id : record.role_id
  const url = action === "delete" ? `/api/admin/${entity}/${id}` : `/api/admin/${entity}/${id}/${action}`
  const response = await authenticatedFetch(url, { method: action === "delete" ? "DELETE" : "POST" })
  const result = await response.json()
  if (!result.success) return setGlobalStatus(result.error || `Could not ${action} record`, "error")

  if (action !== "delete") state.filters[entity].status = "all"

  if (entity === "topics") {
    await refreshBootstrap({ activeEntity: entity, topicId: action === "delete" ? "" : id, status: action === "delete" ? state.filters.topics.status : "all" })
  } else if (entity === "questions") {
    await refreshBootstrap({ activeEntity: entity, questionId: action === "delete" ? "" : id, questionFilterTopic: state.filters.questions.topicId, status: action === "delete" ? state.filters.questions.status : "all" })
  } else {
    await refreshBootstrap({ activeEntity: entity, roleId: action === "delete" ? "" : id, status: action === "delete" ? state.filters.roles.status : "all" })
  }

  setGlobalStatus(action === "delete" ? `"${displayName}" deleted` : `"${displayName}" ${action === "archive" ? "archived" : "restored"}`, "success")
}

function handleEntitySelection() {
  entityButtonsRoot?.querySelectorAll("[data-entity]").forEach(button => {
    button.addEventListener("click", () => {
      state.activeEntity = button.dataset.entity
      renderEditor()
    })
  })

  document.querySelectorAll(".admin-mode-button").forEach(button => {
    button.addEventListener("click", () => {
      state.modes[button.dataset.entityMode] = button.dataset.mode
      renderEditor()
    })
  })
}

function attachBrowserListeners() {
  topicSearchInput?.addEventListener("input", () => { state.filters.topics.query = topicSearchInput.value; renderEditor() })
  topicStatusFilter?.addEventListener("change", () => { state.filters.topics.status = topicStatusFilter.value; renderEditor() })
  topicSelect?.addEventListener("change", () => { state.selected.topics = topicSelect.value; renderTopicEditor() })

  questionSearchInput?.addEventListener("input", () => { state.filters.questions.query = questionSearchInput.value; renderEditor() })
  questionStatusFilter?.addEventListener("change", () => { state.filters.questions.status = questionStatusFilter.value; renderEditor() })
  questionFilterTopic?.addEventListener("change", () => { state.filters.questions.topicId = questionFilterTopic.value; renderEditor() })
  questionSelect?.addEventListener("change", () => { state.selected.questions = questionSelect.value; renderQuestionEditor() })

  roleSearchInput?.addEventListener("input", () => { state.filters.roles.query = roleSearchInput.value; renderEditor() })
  roleStatusFilter?.addEventListener("change", () => { state.filters.roles.status = roleStatusFilter.value; renderEditor() })
  roleSelect?.addEventListener("change", () => { state.selected.roles = roleSelect.value; renderRoleEditor() })
}

function attachFormListeners() {
  topicTitleInput?.addEventListener("input", () => {
    if (state.modes.topics === "add" && !topicIdInput.value.trim()) topicIdInput.value = slugify(topicTitleInput.value)
  })
  roleTitleInput?.addEventListener("input", () => {
    if (state.modes.roles === "add" && !roleIdInput.value.trim()) roleIdInput.value = slugify(roleTitleInput.value)
  })

  topicResetButton?.addEventListener("click", () => renderTopicEditor())
  questionResetButton?.addEventListener("click", () => renderQuestionEditor())
  roleResetButton?.addEventListener("click", () => renderRoleEditor())

  topicArchiveBtn?.addEventListener("click", () => performRecordAction("topics", "archive").catch(() => setGlobalStatus("Could not archive topic", "error")))
  topicRestoreBtn?.addEventListener("click", () => performRecordAction("topics", "restore").catch(() => setGlobalStatus("Could not restore topic", "error")))
  topicDeleteBtn?.addEventListener("click", () => performRecordAction("topics", "delete").catch(() => setGlobalStatus("Could not delete topic", "error")))

  questionArchiveBtn?.addEventListener("click", () => performRecordAction("questions", "archive").catch(() => setGlobalStatus("Could not archive question", "error")))
  questionRestoreBtn?.addEventListener("click", () => performRecordAction("questions", "restore").catch(() => setGlobalStatus("Could not restore question", "error")))
  questionDeleteBtn?.addEventListener("click", () => performRecordAction("questions", "delete").catch(() => setGlobalStatus("Could not delete question", "error")))

  roleArchiveBtn?.addEventListener("click", () => performRecordAction("roles", "archive").catch(() => setGlobalStatus("Could not archive role", "error")))
  roleRestoreBtn?.addEventListener("click", () => performRecordAction("roles", "restore").catch(() => setGlobalStatus("Could not restore role", "error")))
  roleDeleteBtn?.addEventListener("click", () => performRecordAction("roles", "delete").catch(() => setGlobalStatus("Could not delete role", "error")))

  topicForm?.addEventListener("submit", event => handleTopicSubmit(event).catch(() => setGlobalStatus("Could not save topic", "error")))
  questionForm?.addEventListener("submit", event => handleQuestionSubmit(event).catch(() => setGlobalStatus("Could not save question", "error")))
  roleForm?.addEventListener("submit", event => handleRoleSubmit(event).catch(() => setGlobalStatus("Could not save role", "error")))
}

async function initAdminPage() {
  const currentUser = getCurrentUser()
  if (!currentUser?.user_id) {
    renderAccessCard("Sign in required", "This page manages the live interview catalog, so you need to be signed in before we can even check admin access.", [
      { href: "/auth", label: "Go to sign in", className: "primary-action" },
      { href: "/", label: "Back home", className: "secondary-action" },
    ])
    return
  }

  try {
    const accessResponse = await authenticatedFetch("/api/admin/access")
    const accessResult = await accessResponse.json()
    if (!accessResult.success || !accessResult.is_admin) {
      renderAccessCard("Admin access not available", "Your current account is signed in, but it is not allowed to edit the interview catalog from this page.", [
        { href: "/profile", label: "Open profile", className: "secondary-action" },
        { href: "/", label: "Back home", className: "secondary-action" },
      ])
      return
    }

    await loadBootstrap()
    accessRoot.hidden = true
    workspace.hidden = false
    attachBrowserListeners()
    attachFormListeners()
    handleEntitySelection()
    renderEditor()
    setGlobalStatus("Admin workspace ready", "success")
  } catch (error) {
    renderAccessCard("Could not load admin workspace", "The app could not reach the admin endpoints right now. The catalog has not been changed.", [
      { href: "/profile", label: "Open profile", className: "secondary-action" },
      { href: "/tracks", label: "Browse tracks", className: "secondary-action" },
    ])
  }
}

initAdminPage()
