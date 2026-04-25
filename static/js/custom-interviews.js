import { authenticatedFetch, getCurrentUser } from "./session.js"

const BUILDER_STORAGE_KEY = "customInterviewBuilderDraft"
const CUSTOM_PLAN_STORAGE_KEY = "customInterviewPlan"
const CUSTOM_TEMPLATE_ID_KEY = "selectedCustomInterviewId"
const INTERVIEW_MODE_KEY = "selectedInterviewMode"

const titleInput = document.getElementById("custom-title")
const durationInput = document.getElementById("custom-duration")
const questionTotalInput = document.getElementById("custom-question-total")
const descriptionInput = document.getElementById("custom-description")
const questionList = document.getElementById("custom-question-list")
const questionCountEl = document.getElementById("custom-question-count")
const totalWeightEl = document.getElementById("custom-total-weight")
const totalTargetEl = document.getElementById("custom-total-target")
const builderStatus = document.getElementById("builder-status")
const builderNote = document.getElementById("custom-builder-note")
const libraryCopy = document.getElementById("custom-library-copy")
const templateList = document.getElementById("custom-template-list")
const addQuestionBtn = document.getElementById("add-question-btn")
const rebalanceBtn = document.getElementById("rebalance-btn")
const startCustomBtn = document.getElementById("start-custom-btn")
const saveCustomBtn = document.getElementById("save-custom-btn")
const resetCustomBtn = document.getElementById("reset-custom-btn")

function createDefaultQuestion(index) {
  return {
    question_text: "",
    weight: index === 1 ? 40 : 30,
    target_seconds: 90,
    section_label: `Custom ${index}`,
  }
}

function createDefaultBuilderState() {
  return {
    editingTemplateId: null,
    title: "Custom Interview",
    description: "",
    total_duration_minutes: 30,
    questions: [createDefaultQuestion(1)],
  }
}

function loadBuilderState() {
  try {
    const stored = JSON.parse(localStorage.getItem(BUILDER_STORAGE_KEY) || "null")
    if (!stored || typeof stored !== "object") {
      return createDefaultBuilderState()
    }

    const questions = Array.isArray(stored.questions) && stored.questions.length
      ? stored.questions.map((question, index) => ({
        question_text: String(question.question_text || question.q || "").trim(),
        weight: Number(question.weight || 1),
        target_seconds: Number(question.target_seconds || 90),
        section_label: String(question.section_label || `Custom ${index + 1}`),
      }))
      : createDefaultBuilderState().questions

    return {
      editingTemplateId: stored.editingTemplateId || stored.template_id || null,
      title: String(stored.title || "Custom Interview"),
      description: String(stored.description || ""),
      total_duration_minutes: Number(stored.total_duration_minutes || 30),
      questions,
    }
  } catch (error) {
    return createDefaultBuilderState()
  }
}

let builderState = loadBuilderState()

function persistBuilderState() {
  localStorage.setItem(BUILDER_STORAGE_KEY, JSON.stringify(builderState))
}

function clampQuestionCount(value) {
  const parsed = Math.round(Number(value))
  if (Number.isNaN(parsed)) return 1
  return Math.max(1, Math.min(parsed, 20))
}

function setBuilderStatus(message, tone = "working") {
  if (builderStatus) {
    builderStatus.innerText = message
    builderStatus.dataset.tone = tone
  }
}

function normalizePositiveNumber(value, fallback) {
  const parsed = Number(value)
  if (Number.isNaN(parsed) || parsed <= 0) return fallback
  return parsed
}

function normalizeQuestion(question, index) {
  const questionText = String(question.question_text || "").trim()
  if (!questionText) return null

  return {
    question_id: `custom_${String(index).padStart(3, "0")}`,
    question_text: questionText,
    weight: Number(normalizePositiveNumber(question.weight, 1).toFixed(2)),
    target_seconds: Math.round(normalizePositiveNumber(question.target_seconds, 90)),
    section_label: `Custom ${index}`,
  }
}

function collectBuilderPayload() {
  const title = String(titleInput?.value || "").trim()
  const description = String(descriptionInput?.value || "").trim()
  const totalDurationMinutes = Math.max(5, Math.min(240, Math.round(normalizePositiveNumber(durationInput?.value, 30))))
  const questions = (builderState.questions || [])
    .map((question, index) => normalizeQuestion(question, index + 1))
    .filter(Boolean)

  const errors = []
  if (!title) {
    errors.push("Add an interview title.")
  }
  if (!questions.length) {
    errors.push("Add at least one non-empty question.")
  }

  return {
    errors,
    payload: {
      title,
      description,
      total_duration_minutes: totalDurationMinutes,
      questions,
    },
  }
}

function buildSessionPlan(payload, templateId = null) {
  return {
    mode: "custom",
    analytics_mode: "delivery_only",
    template_id: templateId,
    title: payload.title,
    subtitle: payload.description || `Custom interview with ${payload.questions.length} user-defined questions and delivery-focused analytics.`,
    duration_minutes: payload.total_duration_minutes,
    blueprint_label: "Custom flow",
    primary_topic_id: "custom",
    questions: payload.questions.map((question, index) => ({
      question_id: question.question_id || `custom_${String(index + 1).padStart(3, "0")}`,
      topic_id: "custom",
      q: question.question_text,
      difficulty: "custom",
      weight: question.weight,
      target_seconds: question.target_seconds,
      section_label: question.section_label || `Custom ${index + 1}`,
    })),
  }
}

function setSelectedCustomPlan(plan) {
  localStorage.setItem(INTERVIEW_MODE_KEY, "custom")
  localStorage.removeItem("selectedTopic")
  localStorage.removeItem("selectedRole")
  localStorage.removeItem("selectedStudyPlanId")
  localStorage.removeItem("selectedStudyStepId")
  localStorage.setItem("selectedDuration", String(plan.duration_minutes || 30))
  localStorage.setItem(CUSTOM_PLAN_STORAGE_KEY, JSON.stringify(plan))

  if (plan.template_id) {
    localStorage.setItem(CUSTOM_TEMPLATE_ID_KEY, plan.template_id)
  } else {
    localStorage.removeItem(CUSTOM_TEMPLATE_ID_KEY)
  }
}

function renderBuilderSummary() {
  const questions = builderState.questions || []
  const totalWeight = questions.reduce((sum, question) => sum + normalizePositiveNumber(question.weight, 0), 0)
  const totalTargetSeconds = questions.reduce((sum, question) => sum + normalizePositiveNumber(question.target_seconds, 0), 0)

  if (questionCountEl) questionCountEl.innerText = String(questions.length)
  if (questionTotalInput) questionTotalInput.value = String(questions.length)
  if (totalWeightEl) totalWeightEl.innerText = String(Number(totalWeight.toFixed(2)))
  if (totalTargetEl) totalTargetEl.innerText = `${Math.round(totalTargetSeconds / 60)} min`

  if (builderNote) {
    builderNote.innerText = totalWeight === 100
      ? "Weight total is exactly 100. This is a clean interview scoring setup."
      : `Current total weight is ${Number(totalWeight.toFixed(2))}. Relative weights are allowed, but 100 is recommended.`
  }
}

function renderQuestionList() {
  if (!questionList) return

  const questions = builderState.questions || []
  questionList.innerHTML = questions.map((question, index) => `
    <article class="custom-question-card">
      <div class="custom-question-card-top">
        <div class="custom-question-order">Q${index + 1}</div>
        <div class="custom-template-actions">
          <button class="secondary-action" type="button" data-move-up="${index}" ${index === 0 ? "disabled" : ""}>Move up</button>
          <button class="secondary-action" type="button" data-move-down="${index}" ${index === questions.length - 1 ? "disabled" : ""}>Move down</button>
          <button class="secondary-action" type="button" data-remove-question="${index}" ${questions.length === 1 ? "disabled" : ""}>Remove</button>
        </div>
      </div>

      <div class="custom-question-grid">
        <label class="custom-field">
          <span class="summary-label">Question Text</span>
          <textarea rows="4" data-question-field="question_text" data-index="${index}" placeholder="Write the exact question you want asked.">${question.question_text || ""}</textarea>
        </label>

        <label class="custom-field">
          <span class="summary-label">Weight</span>
          <input type="number" min="0.1" step="0.1" value="${question.weight || 1}" data-question-field="weight" data-index="${index}">
        </label>

        <label class="custom-field">
          <span class="summary-label">Target Seconds</span>
          <input type="number" min="15" max="1800" step="5" value="${question.target_seconds || 90}" data-question-field="target_seconds" data-index="${index}">
        </label>
      </div>
    </article>
  `).join("")

  questionList.querySelectorAll("[data-question-field]").forEach(element => {
    element.addEventListener("input", () => {
      const index = Number(element.dataset.index)
      const field = element.dataset.questionField
      if (!builderState.questions[index]) return
      builderState.questions[index][field] = element.value
      persistBuilderState()
      renderBuilderSummary()
      setBuilderStatus(builderState.editingTemplateId ? "Editing saved template" : "Draft mode", "working")
    })
  })

  questionList.querySelectorAll("[data-remove-question]").forEach(button => {
    button.addEventListener("click", () => {
      const index = Number(button.dataset.removeQuestion)
      builderState.questions.splice(index, 1)
      persistBuilderState()
      renderBuilder()
    })
  })

  questionList.querySelectorAll("[data-move-up]").forEach(button => {
    button.addEventListener("click", () => {
      const index = Number(button.dataset.moveUp)
      if (index <= 0) return
      const temp = builderState.questions[index - 1]
      builderState.questions[index - 1] = builderState.questions[index]
      builderState.questions[index] = temp
      persistBuilderState()
      renderBuilder()
    })
  })

  questionList.querySelectorAll("[data-move-down]").forEach(button => {
    button.addEventListener("click", () => {
      const index = Number(button.dataset.moveDown)
      if (index >= builderState.questions.length - 1) return
      const temp = builderState.questions[index + 1]
      builderState.questions[index + 1] = builderState.questions[index]
      builderState.questions[index] = temp
      persistBuilderState()
      renderBuilder()
    })
  })
}

function renderBuilder() {
  if (titleInput) titleInput.value = builderState.title || ""
  if (durationInput) durationInput.value = String(builderState.total_duration_minutes || 30)
  if (questionTotalInput) questionTotalInput.value = String((builderState.questions || []).length || 1)
  if (descriptionInput) descriptionInput.value = builderState.description || ""
  setBuilderStatus(builderState.editingTemplateId ? "Editing saved template" : "Draft mode", "working")
  renderQuestionList()
  renderBuilderSummary()
}

function setQuestionCount(nextCount) {
  const targetCount = clampQuestionCount(nextCount)
  const currentQuestions = [...(builderState.questions || [])]

  if (currentQuestions.length < targetCount) {
    for (let index = currentQuestions.length + 1; index <= targetCount; index++) {
      currentQuestions.push(createDefaultQuestion(index))
    }
  } else if (currentQuestions.length > targetCount) {
    currentQuestions.length = targetCount
  }

  builderState.questions = currentQuestions.map((question, index) => ({
    ...question,
    section_label: `Custom ${index + 1}`,
  }))
  persistBuilderState()
  renderBuilder()
}

function resetBuilder() {
  builderState = createDefaultBuilderState()
  persistBuilderState()
  renderBuilder()
}

function loadBuilderFromTemplate(template) {
  builderState = {
    editingTemplateId: template.template_id,
    title: template.title || "Custom Interview",
    description: template.description || "",
    total_duration_minutes: Number(template.total_duration_minutes || 30),
    questions: (template.questions || []).map((question, index) => ({
      question_text: question.question_text || question.q || "",
      weight: Number(question.weight || 1),
      target_seconds: Number(question.target_seconds || 90),
      section_label: question.section_label || `Custom ${index + 1}`,
    })),
  }
  persistBuilderState()
  renderBuilder()
}

function rebalanceWeights() {
  if (!builderState.questions.length) return

  const baseWeight = Number((100 / builderState.questions.length).toFixed(2))
  let runningTotal = 0
  builderState.questions = builderState.questions.map((question, index) => {
    const nextWeight = index === builderState.questions.length - 1
      ? Number((100 - runningTotal).toFixed(2))
      : baseWeight
    runningTotal += nextWeight
    return {
      ...question,
      weight: nextWeight,
    }
  })

  persistBuilderState()
  renderBuilder()
}

function renderTemplateList(templates) {
  if (!templateList) return

  if (!templates.length) {
    templateList.innerHTML = `
      <div class="custom-empty-state">
        <h4>No saved custom interviews yet</h4>
        <p>Build one on the left and save it while signed in. After that, it will appear here for quick reuse.</p>
      </div>
    `
    return
  }

  templateList.innerHTML = templates.map(template => `
    <article class="custom-template-card">
      <div class="custom-template-head">
        <div>
          <p class="section-kicker">Saved Template</p>
          <h4>${template.title}</h4>
        </div>
        <div class="status-badge">${template.question_count} question${template.question_count === 1 ? "" : "s"}</div>
      </div>
      <p>${template.description || "No extra description was added for this custom interview."}</p>
      <div class="custom-template-meta">
        <span class="custom-meta-badge">${template.total_duration_minutes} min round</span>
        <span class="custom-meta-badge">Updated ${new Date(template.updated_at || template.created_at || Date.now()).toLocaleDateString()}</span>
      </div>
      <div class="custom-template-actions" style="margin-top: 16px;">
        <button class="primary-action" type="button" data-start-template="${template.template_id}">Start</button>
        <button class="secondary-action" type="button" data-edit-template="${template.template_id}">Edit</button>
        <button class="secondary-action" type="button" data-delete-template="${template.template_id}">Delete</button>
      </div>
    </article>
  `).join("")

  templateList.querySelectorAll("[data-start-template]").forEach(button => {
    button.addEventListener("click", () => {
      const template = templates.find(item => item.template_id === button.dataset.startTemplate)
      if (!template) return
      const plan = buildSessionPlan(template, template.template_id)
      setSelectedCustomPlan(plan)
      window.location.href = "/interview"
    })
  })

  templateList.querySelectorAll("[data-edit-template]").forEach(button => {
    button.addEventListener("click", () => {
      const template = templates.find(item => item.template_id === button.dataset.editTemplate)
      if (!template) return
      loadBuilderFromTemplate(template)
      setBuilderStatus("Editing saved template", "working")
      window.scrollTo({ top: 0, behavior: "smooth" })
    })
  })

  templateList.querySelectorAll("[data-delete-template]").forEach(button => {
    button.addEventListener("click", async () => {
      const template = templates.find(item => item.template_id === button.dataset.deleteTemplate)
      if (!template) return
      const confirmed = window.confirm(`Delete "${template.title}"?`)
      if (!confirmed) return

      try {
        const response = await authenticatedFetch(`/api/custom-interviews/${template.template_id}`, { method: "DELETE" })
        const result = await response.json()
        if (!result.success) {
          throw new Error(result.error || "Delete failed")
        }
        if (builderState.editingTemplateId === template.template_id) {
          resetBuilder()
        }
        await loadSavedTemplates()
      } catch (error) {
        setBuilderStatus("Could not delete template", "error")
      }
    })
  })
}

async function loadSavedTemplates() {
  const currentUser = getCurrentUser()

  if (!currentUser?.user_id) {
    if (libraryCopy) {
      libraryCopy.innerText = "Sign in to save and manage reusable custom interviews. Guest mode can still build and run a one-off interview."
    }
    if (templateList) {
      templateList.innerHTML = `
        <div class="custom-empty-state">
          <h4>Sign in to unlock saved templates</h4>
          <p>You can still build and run a custom interview now, but template saving is tied to an account.</p>
        </div>
      `
    }
    return
  }

  if (libraryCopy) {
    libraryCopy.innerText = "Saved custom interviews live here. Start one instantly, edit it, or use it as a template for the next round."
  }

  try {
    const response = await authenticatedFetch("/api/custom-interviews")
    const result = await response.json()
    if (!result.success) {
      throw new Error(result.error || "Failed to load templates")
    }
    renderTemplateList(result.templates || [])
  } catch (error) {
    if (templateList) {
      templateList.innerHTML = `
        <div class="custom-empty-state">
          <h4>Could not load saved templates</h4>
          <p>The builder still works locally, but the backend template list is unavailable right now.</p>
        </div>
      `
    }
  }
}

async function saveTemplate() {
  const currentUser = getCurrentUser()
  if (!currentUser?.user_id) {
    setBuilderStatus("Sign in to save templates", "error")
    return
  }

  const { errors, payload } = collectBuilderPayload()
  if (errors.length) {
    setBuilderStatus(errors[0], "error")
    return
  }

  try {
    const isEditing = Boolean(builderState.editingTemplateId)
    const response = await authenticatedFetch(
      isEditing ? `/api/custom-interviews/${builderState.editingTemplateId}` : "/api/custom-interviews",
      {
        method: isEditing ? "PUT" : "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      }
    )
    const result = await response.json()
    if (!result.success || !result.template) {
      throw new Error(result.error || "Failed to save template")
    }

    loadBuilderFromTemplate(result.template)
    setBuilderStatus("Template saved", "success")
    await loadSavedTemplates()
  } catch (error) {
    setBuilderStatus("Could not save template", "error")
  }
}

function startCustomInterview() {
  const { errors, payload } = collectBuilderPayload()
  if (errors.length) {
    setBuilderStatus(errors[0], "error")
    return
  }

  const plan = buildSessionPlan(payload, builderState.editingTemplateId)
  builderState = {
    ...builderState,
    ...payload,
    questions: payload.questions.map(question => ({
      question_text: question.question_text,
      weight: question.weight,
      target_seconds: question.target_seconds,
      section_label: question.section_label,
    })),
  }
  persistBuilderState()
  setSelectedCustomPlan(plan)
  window.location.href = "/interview"
}

if (titleInput) {
  titleInput.addEventListener("input", () => {
    builderState.title = titleInput.value
    persistBuilderState()
    setBuilderStatus(builderState.editingTemplateId ? "Editing saved template" : "Draft mode", "working")
  })
}

if (durationInput) {
  durationInput.addEventListener("input", () => {
    builderState.total_duration_minutes = durationInput.value
    persistBuilderState()
  })
}

if (questionTotalInput) {
  questionTotalInput.addEventListener("input", () => {
    setQuestionCount(questionTotalInput.value)
  })
}

if (descriptionInput) {
  descriptionInput.addEventListener("input", () => {
    builderState.description = descriptionInput.value
    persistBuilderState()
  })
}

if (addQuestionBtn) {
  addQuestionBtn.addEventListener("click", () => {
    setQuestionCount((builderState.questions?.length || 0) + 1)
  })
}

if (rebalanceBtn) {
  rebalanceBtn.addEventListener("click", rebalanceWeights)
}

if (startCustomBtn) {
  startCustomBtn.addEventListener("click", startCustomInterview)
}

if (saveCustomBtn) {
  saveCustomBtn.addEventListener("click", saveTemplate)
}

if (resetCustomBtn) {
  resetCustomBtn.addEventListener("click", resetBuilder)
}

renderBuilder()
loadSavedTemplates()
