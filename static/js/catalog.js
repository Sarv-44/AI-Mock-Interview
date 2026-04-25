function clearCustomInterviewSelection() {
  localStorage.removeItem("selectedInterviewMode")
  localStorage.removeItem("selectedCustomInterviewId")
  localStorage.removeItem("customInterviewPlan")
  localStorage.removeItem("selectedStudyPlanId")
  localStorage.removeItem("selectedStudyStepId")
}

export function startTopicInterview(topicId) {
  clearCustomInterviewSelection()
  localStorage.setItem("selectedTopic", topicId)
  localStorage.removeItem("selectedRole")
  localStorage.setItem("selectedDuration", "30")
  window.location.href = "/interview"
}

export function startRoleInterview(roleId, durationMinutes = 30) {
  clearCustomInterviewSelection()
  localStorage.setItem("selectedRole", roleId)
  localStorage.removeItem("selectedTopic")
  localStorage.setItem("selectedDuration", String(durationMinutes || 30))
  window.location.href = "/interview"
}

export async function loadInterviewCatalog() {
  const response = await fetch("/api/interview/catalog")
  const result = await response.json()

  if (!result.success) {
    throw new Error(result.error || "Catalog request failed")
  }

  return {
    topics: Array.isArray(result.topics) ? result.topics : [],
    roles: Array.isArray(result.roles) ? result.roles : [],
  }
}

export async function loadTopicSummary() {
  const response = await fetch("/api/topics/summary")
  const result = await response.json()

  if (!result.success) {
    return {
      ratings: {},
      activity: {},
    }
  }

  return {
    ratings: Object.fromEntries((result.ratings || []).map(entry => [entry.topic_id, entry])),
    activity: Object.fromEntries((result.activity || []).map(entry => [entry.topic_id, entry])),
  }
}

export function getTotalQuestionCount(topics = []) {
  return topics.reduce((sum, topic) => sum + (topic.question_count || 0), 0)
}

export function getTopicCategories(topics = []) {
  return ["all", ...new Set(topics.map(topic => String(topic.category || "").trim()).filter(Boolean))]
}

export function createTopicCard(topic, topicRatings = {}, topicActivity = {}) {
  const ratingData = topicRatings[topic.topic_id]
  const activityData = topicActivity[topic.topic_id]
  const ratingLabel = ratingData?.rating_count ? `${ratingData.average_rating}/5` : "No ratings yet"
  const ratingMeta = ratingData?.rating_count ? `${ratingData.rating_count} ratings` : "Rate after a completed session"
  const activityLabel = activityData?.interview_count
    ? `${activityData.interview_count} signed-in interviews completed`
    : "No signed-in interviews yet"

  return `
    <button class="topic-card ${topic.accent}" data-topic-id="${topic.topic_id}" type="button">
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
          <span>${topic.level_label}</span>
          <span>${topic.question_count} interview questions</span>
        </div>
        <div class="topic-footer-row">
          <span class="topic-popularity">${activityLabel}</span>
          <span class="topic-cta">Start track</span>
        </div>
      </div>
    </button>
  `
}

export function createRoleCard(role) {
  const focusPills = (role.focus_topics || []).slice(0, 4).map(topic => (
    `<span class="role-focus-pill">${topic.title}</span>`
  )).join("")

  return `
    <article class="role-card">
      <div class="role-card-head">
        <div>
          <div class="topic-chip">${role.level_label}</div>
          <h4>${role.title}</h4>
          <p>${role.subtitle}</p>
        </div>
        <div class="role-duration-badge">${role.default_duration} min default</div>
      </div>
      <p class="role-description">${role.description}</p>
      <div class="role-focus-row">
        ${focusPills}
      </div>
      <div class="role-card-footer">
        <span class="topic-popularity">${(role.available_durations || []).join(" / ")} min options</span>
        <button class="primary-action role-start-btn" type="button" data-role-id="${role.role_id}">Start role interview</button>
      </div>
    </article>
  `
}

export function createPreviewTopicCard(topic, topicRatings = {}, topicActivity = {}) {
  if (!topic) {
    return `<p class="preview-empty">No featured topic available right now.</p>`
  }

  const ratingData = topicRatings[topic.topic_id]
  const activityData = topicActivity[topic.topic_id]
  const ratingLabel = ratingData?.rating_count ? `${ratingData.average_rating}/5 rating` : "Not rated yet"
  const activityLabel = activityData?.interview_count
    ? `${activityData.interview_count} completed interviews`
    : "Fresh track"

  return `
    <article class="mini-preview-card ${topic.accent}">
      <p class="topic-chip">${topic.category}</p>
      <h4>${topic.title}</h4>
      <p>${topic.description}</p>
      <div class="mini-preview-meta">
        <span>${topic.question_count} prompts</span>
        <span>${ratingLabel}</span>
        <span>${activityLabel}</span>
      </div>
      <button class="hero-link preview-start-btn" type="button" data-topic-id="${topic.topic_id}">Start this track</button>
    </article>
  `
}

export function createPreviewRoleCard(role) {
  if (!role) {
    return `<p class="preview-empty">No featured role round available right now.</p>`
  }

  return `
    <article class="mini-preview-card">
      <p class="topic-chip">${role.level_label}</p>
      <h4>${role.title}</h4>
      <p>${role.description}</p>
      <div class="mini-preview-meta">
        <span>${role.default_duration} min default</span>
        <span>${(role.focus_topics || []).slice(0, 2).map(topic => topic.title).join(" + ")}</span>
      </div>
      <button class="hero-link preview-role-btn" type="button" data-role-id="${role.role_id}">Start this round</button>
    </article>
  `
}
