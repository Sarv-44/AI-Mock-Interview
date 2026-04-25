import { loadInterviewCatalog } from "./catalog.js"
import { authenticatedFetch, getCurrentUser } from "./session.js"

const plannerForm = document.getElementById("planner-form")
const roleSelect = document.getElementById("planner-role-select")
const daysInput = document.getElementById("planner-days-input")
const submitButton = document.getElementById("planner-submit-btn")
const statusBanner = document.getElementById("planner-status-banner")
const roleCount = document.getElementById("planner-role-count")
const savedCount = document.getElementById("planner-saved-count")
const planListRoot = document.getElementById("planner-plan-list")
const detailTitle = document.getElementById("planner-detail-title")
const detailCopy = document.getElementById("planner-detail-copy")
const phaseStrip = document.getElementById("planner-phase-strip")
const progressStrip = document.getElementById("planner-progress-strip")
const stepsRoot = document.getElementById("planner-steps-root")
const materialRoot = document.getElementById("planner-material-root")
const PLANNER_RETURN_STORAGE_KEY = "plannerReturnContext"

let roleCatalog = []
let savedPlans = []
let activePlanId = null
let activePlanDetailResult = null
let activeDayKey = null
let activeMaterialTopicId = null
let activeQuizStepId = null
let activeQuizAnswers = {}
let pendingDeletePlanId = null
let pendingPlannerReturnContext = null

function setBanner(message, tone = "neutral") {
  if (!statusBanner) return
  statusBanner.textContent = message
  statusBanner.dataset.tone = tone
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;")
}

function readPlannerReturnContext() {
  const params = new URLSearchParams(window.location.search)
  let storedContext = null

  try {
    const raw = localStorage.getItem(PLANNER_RETURN_STORAGE_KEY)
    storedContext = raw ? JSON.parse(raw) : null
  } catch (error) {
    storedContext = null
  }

  const studyPlanId = params.get("plan") || storedContext?.studyPlanId || null
  const studyStepId = params.get("step") || storedContext?.studyStepId || null
  if (!studyPlanId || !studyStepId) return null

  return {
    studyPlanId,
    studyStepId,
    finalScore: storedContext?.finalScore ?? null,
    sessionId: storedContext?.sessionId ?? null,
  }
}

function clearPlannerReturnContext() {
  pendingPlannerReturnContext = null
  localStorage.removeItem(PLANNER_RETURN_STORAGE_KEY)

  const url = new URL(window.location.href)
  url.searchParams.delete("plan")
  url.searchParams.delete("step")
  const nextUrl = `${url.pathname}${url.search}${url.hash}`
  window.history.replaceState({}, "", nextUrl)
}

function clearInterviewLaunchContext() {
  localStorage.removeItem("selectedTopic")
  localStorage.removeItem("selectedRole")
  localStorage.removeItem("selectedCustomInterviewId")
  localStorage.removeItem("customInterviewPlan")
  localStorage.removeItem("selectedStudyPlanId")
  localStorage.removeItem("selectedStudyStepId")
}

function getStepTypeLabel(step) {
  if (!step) return "Revision"
  if (step.step_type === "mcq_quiz") return "Checkpoint quiz"
  if (step.step_type === "topic_round") {
    const stage = Number(step.snapshot?.round_stage || 1)
    return `Topic round ${stage}`
  }
  if (step.step_type === "mixed_quiz") return "Mixed round"
  if (step.step_type === "mock_interview") return "Role mock"
  return "Revision"
}

function getStepTone(stepType) {
  switch (stepType) {
    case "mcq_quiz":
      return "checkpoint"
    case "topic_round":
      return "focus"
    case "mixed_quiz":
      return "blend"
    case "mock_interview":
      return "simulation"
    default:
      return "revise"
  }
}

function getLaunchLabel(step) {
  if (step.step_type === "mcq_quiz") {
    return step.status === "done" ? "Review checkpoint" : "Launch checkpoint"
  }
  if (step.step_type === "topic_round") {
    return `Start ${step.snapshot?.stage_label || "round"}`
  }
  if (step.step_type === "mixed_quiz") return "Start mixed round"
  if (step.step_type === "mock_interview") return "Start mock"
  return "Review notes"
}

function canOpenQuizStep(step) {
  const snapshot = step?.snapshot || {}
  if (snapshot.can_launch_quiz) return true
  if (step?.step_type !== "mcq_quiz") return false
  if ((snapshot.launch_mode || "") === "mcq_quiz") return true
  return getQuizQuestions(step).length > 0
}

function getStepStats(step) {
  const snapshot = step.snapshot || {}
  const stats = []
  if (snapshot.stage_label) stats.push(snapshot.stage_label)
  if (snapshot.question_count) stats.push(`${snapshot.question_count} questions`)
  if (snapshot.difficulty_focus) stats.push(snapshot.difficulty_focus)
  if (snapshot.recommended_duration) stats.push(`${snapshot.recommended_duration} min`)
  const lastScore = snapshot.last_score ?? step.last_score
  if (lastScore !== undefined && lastScore !== null && lastScore !== "") {
    stats.push(`Last score ${lastScore}`)
  }
  if (snapshot.best_score !== undefined && snapshot.best_score !== null && snapshot.best_score !== "") {
    stats.push(`Best ${snapshot.best_score}`)
  }
  return stats
}

function getQuizQuestions(step) {
  return Array.isArray(step?.snapshot?.quiz_items) ? step.snapshot.quiz_items : []
}

function findStepById(stepId) {
  const steps = activePlanDetailResult?.steps || []
  return steps.find(step => step.step_id === stepId) || null
}

function groupStepsByDay(steps = []) {
  const groups = new Map()
  steps.forEach(step => {
    const key = String(step.scheduled_day || step.scheduled_label || "1")
    if (!groups.has(key)) {
      groups.set(key, {
        key,
        scheduledDay: Number(step.scheduled_day || 0),
        label: step.scheduled_label || `Day ${step.scheduled_day || 1}`,
        steps: [],
      })
    }
    groups.get(key).steps.push(step)
  })
  return [...groups.values()].sort((left, right) => left.scheduledDay - right.scheduledDay)
}

function dayHasStepType(group, stepType) {
  return Boolean(group?.steps?.some(step => step.step_type === stepType))
}

function getDaySummary(group) {
  const labels = [...new Set((group?.steps || []).map(step => getStepTypeLabel(step)))]
  if (!labels.length) return "No steps"
  if (labels.length === 1) return labels[0]
  if (labels.includes("Checkpoint quiz")) {
    const otherLabel = labels.find(label => label !== "Checkpoint quiz")
    return otherLabel ? `Checkpoint + ${otherLabel}` : "Checkpoint quiz"
  }
  if (labels.length === 2) return `${labels[0]} + ${labels[1]}`
  return `${labels[0]} + ${labels.length - 1} more`
}

function getDayTone(group) {
  if (dayHasStepType(group, "mcq_quiz")) return "checkpoint"
  if (dayHasStepType(group, "mock_interview")) return "simulation"
  if (dayHasStepType(group, "mixed_quiz")) return "blend"
  if (dayHasStepType(group, "topic_round")) return "focus"
  return "revise"
}

function getDaySupportCopy(group) {
  if (dayHasStepType(group, "mcq_quiz") && dayHasStepType(group, "topic_round")) {
    return "Quick recall check before the harder round starts."
  }
  if (dayHasStepType(group, "mcq_quiz")) {
    return "Short checkpoint day to keep recall active."
  }
  if (dayHasStepType(group, "mock_interview")) {
    return "Longer simulation block with role-style pressure."
  }
  if (dayHasStepType(group, "mixed_quiz")) {
    return "Multiple topic lanes blended into one sitting."
  }
  if (dayHasStepType(group, "topic_round")) {
    return "Focused interview reps on one topic lane."
  }
  return "Revision-first day with notes and answer patterns."
}

function getDayAccentLabel(group) {
  if (dayHasStepType(group, "mcq_quiz")) return "Quiz day"
  if (dayHasStepType(group, "mock_interview")) return "Mock day"
  if (dayHasStepType(group, "mixed_quiz")) return "Mixed day"
  if (dayHasStepType(group, "topic_round")) return "Practice day"
  return "Revision day"
}

function getDayStepLabels(group) {
  return [...new Set((group?.steps || []).map(step => getStepTypeLabel(step)))].slice(0, 3)
}

function scrollActiveDayChipIntoView(behavior = "smooth") {
  const rail = stepsRoot?.querySelector("[data-day-rail]")
  const activeChip = rail?.querySelector(".planner-day-pill.is-active")
  if (!rail || !activeChip) return

  const chipCenter = activeChip.offsetLeft + (activeChip.offsetWidth / 2)
  const targetLeft = Math.max(0, chipCenter - (rail.clientWidth / 2))
  rail.scrollTo({ left: targetLeft, behavior })
}

function resolveActiveDayKey(dayGroups) {
  if (dayGroups.some(group => group.key === activeDayKey)) {
    return activeDayKey
  }
  const nextOpenGroup = dayGroups.find(group => group.steps.some(step => step.status !== "done"))
  return nextOpenGroup?.key || dayGroups[0]?.key || null
}

function resolveActiveMaterialId(materials, stepsForDay = []) {
  if (materials.some(material => material.topic_id === activeMaterialTopicId)) {
    return activeMaterialTopicId
  }
  const dayTopic = stepsForDay.find(step => step.topic_id)?.topic_id
  if (dayTopic && materials.some(material => material.topic_id === dayTopic)) {
    return dayTopic
  }
  return materials[0]?.topic_id || null
}

function applyPlannerReturnContext(result) {
  if (!pendingPlannerReturnContext?.studyPlanId) return
  if (result?.plan?.plan_id !== pendingPlannerReturnContext.studyPlanId) return

  const matchedStep = (result?.steps || []).find(step => step.step_id === pendingPlannerReturnContext.studyStepId)
  if (matchedStep) {
    activeDayKey = String(matchedStep.scheduled_day || matchedStep.scheduled_label || activeDayKey || "")
    const latestScore = matchedStep.snapshot?.last_score ?? pendingPlannerReturnContext.finalScore
    const headline = matchedStep.snapshot?.headline || getStepTypeLabel(matchedStep)
    setBanner(
      latestScore !== undefined && latestScore !== null && latestScore !== ""
        ? `${headline} is back in your prep path with ${latestScore}/100 recorded.`
        : `${headline} is back in your prep path.`,
      "success",
    )
  } else {
    setBanner("Returned to your prep path.", "success")
  }

  clearPlannerReturnContext()
}

function renderRoleOptions() {
  if (!roleSelect) return
  roleSelect.innerHTML = `
    <option value="">Choose a role</option>
    ${roleCatalog.map(role => `<option value="${role.role_id}">${escapeHtml(role.title)}</option>`).join("")}
  `
}

function renderSavedPlans() {
  const currentUser = getCurrentUser()
  if (!planListRoot) return

  if (!currentUser?.user_id) {
    planListRoot.innerHTML = `
      <div class="planner-empty-state">
        <h4>Sign in to start saving</h4>
        <p>Prep paths are user-specific, so we only save and reload them for signed-in accounts.</p>
      </div>
    `
    if (savedCount) savedCount.textContent = "Sign in to save"
    return
  }

  if (!savedPlans.length) {
    planListRoot.innerHTML = `
      <div class="planner-empty-state">
        <h4>No saved prep paths yet</h4>
        <p>Create the first path from the builder and it will appear here for later reuse.</p>
      </div>
    `
    if (savedCount) savedCount.textContent = "0 saved paths"
    return
  }

  planListRoot.innerHTML = savedPlans.map(plan => {
    const progressLabel = `${plan.completed_steps || 0}/${plan.step_count || 0} done`
    const isPendingDelete = plan.plan_id === pendingDeletePlanId
    return `
      <article class="planner-plan-card ${plan.plan_id === activePlanId ? "is-active" : ""}">
        <button type="button" class="planner-plan-card-main" data-plan-id="${plan.plan_id}">
          <span class="summary-label">${escapeHtml(plan.role_title)}</span>
          <strong>${escapeHtml(plan.title)}</strong>
          <p>${escapeHtml(plan.target_days)} day path - ${escapeHtml(progressLabel)} - ${escapeHtml(plan.status)}</p>
        </button>
        <button type="button" class="planner-plan-delete" data-delete-plan="${plan.plan_id}" aria-label="Delete ${escapeHtml(plan.title)}">Delete</button>
        ${isPendingDelete ? `
          <div class="planner-plan-confirm" data-plan-confirm="${plan.plan_id}">
            <p>Delete <strong>${escapeHtml(plan.title)}</strong>? This removes the saved prep path from your account.</p>
            <div class="planner-plan-confirm-actions">
              <button type="button" class="planner-plan-confirm-btn is-danger" data-confirm-delete="${plan.plan_id}">Yes, delete</button>
              <button type="button" class="planner-plan-confirm-btn" data-cancel-delete="${plan.plan_id}">Cancel</button>
            </div>
          </div>
        ` : ""}
      </article>
    `
  }).join("")

  planListRoot.querySelectorAll("[data-plan-id]").forEach(button => {
    button.addEventListener("click", () => {
      loadPlanDetail(button.dataset.planId)
    })
  })
  planListRoot.querySelectorAll("[data-delete-plan]").forEach(button => {
    button.addEventListener("click", event => {
      event.stopPropagation()
      pendingDeletePlanId = pendingDeletePlanId === button.dataset.deletePlan ? null : button.dataset.deletePlan
      renderSavedPlans()
    })
  })
  planListRoot.querySelectorAll("[data-confirm-delete]").forEach(button => {
    button.addEventListener("click", event => {
      event.stopPropagation()
      deletePlan(button.dataset.confirmDelete)
    })
  })
  planListRoot.querySelectorAll("[data-cancel-delete]").forEach(button => {
    button.addEventListener("click", event => {
      event.stopPropagation()
      pendingDeletePlanId = null
      renderSavedPlans()
    })
  })

  if (savedCount) {
    savedCount.textContent = `${savedPlans.length} saved path${savedPlans.length === 1 ? "" : "s"}`
  }
}

function renderProgress(progress) {
  if (!progressStrip) return

  if (!progress) {
    progressStrip.innerHTML = `
      <div class="planner-empty-state compact">
        <p>Progress, score trend, and next-step guidance will appear here after a path is generated.</p>
      </div>
    `
    return
  }

  const topicProgress = (progress.topic_progress || []).slice(0, 4)
  const nextSteps = (progress.next_steps || []).slice(0, 3)
  const phaseBreakdown = progress.phase_breakdown || []
  const completionPercent = progress.completion_percent || 0
  const averageScore = progress.average_score || 0

  progressStrip.innerHTML = `
    <article class="planner-progress-card planner-progress-card--wide">
      <span class="summary-label">Path Snapshot</span>
      <div class="planner-progress-duo">
        <div class="planner-progress-metric">
          <strong>${escapeHtml(completionPercent)}%</strong>
          <p>${escapeHtml(progress.completed_steps || 0)} of ${escapeHtml(progress.total_steps || 0)} steps complete</p>
        </div>
        <div class="planner-progress-metric">
          <strong>${escapeHtml(averageScore)}</strong>
          <p>Rolling average across completed prep interviews</p>
        </div>
      </div>
    </article>
    <article class="planner-progress-card">
      <span class="summary-label">Current Focus</span>
      <strong>${escapeHtml(progress.current_focus?.headline || "Create a path to begin")}</strong>
      <p>${escapeHtml(progress.current_focus?.scheduled_label || "The next runnable step will appear here.")}</p>
    </article>
    <article class="planner-progress-card">
      <span class="summary-label">Phase Rhythm</span>
      <div class="planner-mini-bars">
        ${phaseBreakdown.map(phase => `
          <div class="planner-mini-bar">
            <div class="planner-mini-bar-copy">
              <strong>${escapeHtml(phase.title)}</strong>
              <span>${escapeHtml(phase.completed_steps)}/${escapeHtml(phase.total_steps)} done</span>
            </div>
            <div class="planner-mini-track">
              <div class="planner-mini-fill" style="width:${phase.total_steps ? Math.round((phase.completed_steps / phase.total_steps) * 100) : 0}%"></div>
            </div>
          </div>
        `).join("")}
      </div>
    </article>
    <article class="planner-progress-card planner-progress-card--wide">
      <span class="summary-label">Lane Watch</span>
      <div class="planner-progress-split">
        <div class="planner-progress-stack">
          <strong class="planner-progress-subtitle">Topic progress</strong>
          <div class="planner-topic-progress-list">
            ${topicProgress.length ? topicProgress.map(topic => `
              <div class="planner-topic-progress-item">
                <div class="planner-topic-progress-copy">
                  <strong>${escapeHtml(topic.topic_title)}</strong>
                  <span>${escapeHtml(topic.completed_rounds)}/${escapeHtml(topic.total_rounds)} rounds done</span>
                </div>
                <span class="planner-score-pill">${escapeHtml(topic.average_score || 0)}</span>
              </div>
            `).join("") : `<p class="planner-progress-note">Topic score trends will appear after completions start coming in.</p>`}
          </div>
        </div>
        <div class="planner-progress-stack">
          <strong class="planner-progress-subtitle">Up next</strong>
          <div class="planner-next-list">
            ${nextSteps.length ? nextSteps.map(step => `
              <div class="planner-next-item">
                <strong>${escapeHtml(step.headline)}</strong>
                <span>${escapeHtml(step.scheduled_label)}</span>
              </div>
            `).join("") : `<p class="planner-progress-note">No pending steps left.</p>`}
          </div>
        </div>
      </div>
    </article>
  `
}

function renderMaterialViewer(materials, stepsForDay = []) {
  if (!materialRoot) return

  if (!materials.length) {
    materialRoot.innerHTML = `
      <div class="planner-empty-state">
        <h4>No materials loaded yet</h4>
        <p>Once a prep path is created, the focus topics and revision notes for that role will show up here.</p>
      </div>
    `
    return
  }

  activeMaterialTopicId = resolveActiveMaterialId(materials, stepsForDay)
  const activeMaterial = materials.find(material => material.topic_id === activeMaterialTopicId) || materials[0]
  if (!activeMaterial) return
  const interviewChecks = (activeMaterial.interview_checks || []).slice(0, 5)
  const answerExamples = (activeMaterial.answer_examples || []).slice(0, 2)
  const promptExamples = (activeMaterial.prompt_examples || []).slice(0, 2)

  materialRoot.innerHTML = `
    <div class="planner-material-viewer">
      <div class="planner-material-tabs">
        ${materials.map(material => `
          <button
            type="button"
            class="planner-material-tab ${material.topic_id === activeMaterial.topic_id ? "is-active" : ""}"
            data-material-tab="${material.topic_id}"
          >
            ${escapeHtml(material.topic_title)}
          </button>
        `).join("")}
      </div>

      <article class="planner-material-card planner-material-card--featured" data-material-topic="${escapeHtml(activeMaterial.topic_id)}">
        <div class="planner-material-head">
          <div class="planner-material-head-copy">
            <span class="summary-label">${escapeHtml(activeMaterial.topic_title)}</span>
            <strong>${escapeHtml(activeMaterial.estimated_minutes)} min revision block</strong>
          </div>
          <div class="planner-material-focus">
            <span>${escapeHtml(activeMaterial.knowledge_card?.rows?.[0]?.value || "Focused revision")}</span>
          </div>
        </div>

        <div class="planner-material-layout">
          <div class="planner-material-column">
            <div class="planner-knowledge-card">
              <h4>${escapeHtml(activeMaterial.knowledge_card?.title || activeMaterial.topic_title)}</h4>
              <p>${escapeHtml(activeMaterial.knowledge_card?.summary || activeMaterial.overview)}</p>
              <div class="planner-knowledge-table">
                ${(activeMaterial.knowledge_card?.rows || []).map(row => `
                  <div class="planner-knowledge-row">
                    <span>${escapeHtml(row.label)}</span>
                    <strong>${escapeHtml(row.value)}</strong>
                  </div>
                `).join("")}
              </div>
            </div>

            <div class="planner-material-section">
              <h4>Revision notes</h4>
              <p>${escapeHtml(activeMaterial.revision_notes)}</p>
            </div>

            ${interviewChecks.length ? `
              <div class="planner-material-section">
                <h4>Interview checks</h4>
                <div class="planner-chip-row">${interviewChecks.map(point => `<span>${escapeHtml(point)}</span>`).join("")}</div>
              </div>
            ` : ""}
          </div>

          <div class="planner-material-column">
            ${answerExamples.length ? `
              <div class="planner-material-section">
                <h4>Benchmark answers</h4>
                <div class="planner-answer-stack">
                  ${answerExamples.map(example => `
                    <article class="planner-answer-card">
                      <strong>${escapeHtml(example.question)}</strong>
                      ${example.sample_answer ? `<p><span>Starter:</span> ${escapeHtml(example.sample_answer)}</p>` : ""}
                      ${example.ideal_answer ? `<p><span>Stronger answer:</span> ${escapeHtml(example.ideal_answer)}</p>` : ""}
                    </article>
                  `).join("")}
                </div>
              </div>
            ` : ""}

            ${promptExamples.length ? `
              <div class="planner-material-section">
                <h4>Prompt examples</h4>
                <div class="planner-prompt-list">${promptExamples.map(prompt => `<p>${escapeHtml(prompt)}</p>`).join("")}</div>
              </div>
            ` : ""}
          </div>
        </div>
      </article>
    </div>
  `

  materialRoot.querySelectorAll("[data-material-tab]").forEach(button => {
    button.addEventListener("click", () => {
      activeMaterialTopicId = button.dataset.materialTab
      renderMaterialViewer(materials, stepsForDay)
    })
  })
}

function renderQuizWorkspace(step) {
  const snapshot = step?.snapshot || {}
  const quizItems = getQuizQuestions(step)
  if (!step || !quizItems.length) {
    return `
      <div class="planner-empty-state compact">
        <p>This checkpoint quiz is not available right now.</p>
      </div>
    `
  }

  const selectedAnswers = activeQuizAnswers[step.step_id] || {}
  const reviewItems = Array.isArray(snapshot.last_quiz_review) ? snapshot.last_quiz_review : []
  const reviewById = new Map(reviewItems.map(item => [item.quiz_item_id, item]))
  const hasReview = reviewItems.length > 0
  const scoreLabel = snapshot.last_score ?? snapshot.last_quiz_result?.score

  return `
    <section class="planner-quiz-workspace" data-quiz-workspace="${step.step_id}">
      <div class="planner-quiz-head">
        <div>
          <span class="summary-label">Checkpoint Quiz</span>
          <h4>${escapeHtml(snapshot.headline || "Checkpoint quiz")}</h4>
          <p>${escapeHtml(snapshot.description || "Answer the short recall checkpoint and submit it back into the prep path.")}</p>
        </div>
        <div class="planner-quiz-meta">
          ${scoreLabel !== undefined && scoreLabel !== null && scoreLabel !== "" ? `<span class="planner-score-pill">${escapeHtml(scoreLabel)}/100</span>` : ""}
          <button type="button" class="secondary-action planner-quiz-close" data-step-quiz-close="${step.step_id}">Close</button>
        </div>
      </div>

      <div class="planner-quiz-stack">
        ${quizItems.map((item, index) => {
          const review = reviewById.get(item.quiz_item_id)
          return `
            <article class="planner-quiz-card">
              <div class="planner-quiz-card-head">
                <span class="planner-step-day">Question ${index + 1}</span>
                ${review ? `<span class="planner-quiz-flag ${review.is_correct ? "is-correct" : "is-wrong"}">${review.is_correct ? "Correct" : "Review"}</span>` : ""}
              </div>
              <h5>${escapeHtml(item.prompt)}</h5>
              <div class="planner-quiz-options">
                ${(item.choices || []).map((choice, choiceIndex) => {
                  const isCorrectChoice = review && Number(review.correct_index) === choiceIndex
                  const isWrongChoice = review && Number(review.selected_index) === choiceIndex && !review.is_correct
                  const isSelected = review ? Number(review.selected_index) === choiceIndex : Number(selectedAnswers[index]) === choiceIndex
                  return `
                    <label class="planner-quiz-option ${isSelected ? "is-selected" : ""} ${isCorrectChoice ? "is-correct" : ""} ${isWrongChoice ? "is-wrong" : ""}">
                      <input
                        type="radio"
                        name="planner-quiz-${step.step_id}-${index}"
                        value="${choiceIndex}"
                        data-quiz-choice="${step.step_id}"
                        data-quiz-question="${index}"
                        ${isSelected ? "checked" : ""}
                        ${hasReview ? "disabled" : ""}
                      >
                      <span>${escapeHtml(choice)}</span>
                    </label>
                  `
                }).join("")}
              </div>
              ${review ? `<p class="planner-quiz-review">${escapeHtml(review.explanation || "Review the stronger answer pattern before the next round.")}</p>` : ""}
            </article>
          `
        }).join("")}
      </div>

      <div class="planner-quiz-actions">
        <p>${hasReview ? "This checkpoint is already scored. Reset the step to planned if you want to retake it." : "Pick one answer for each question, then submit the checkpoint back into your prep path."}</p>
        ${hasReview ? `<span class="planner-step-status">Saved</span>` : `<button type="button" class="primary-action" data-quiz-submit="${step.step_id}">Submit checkpoint</button>`}
      </div>
    </section>
  `
}

function wireQuizWorkspace(stepId, steps, materials) {
  stepsRoot?.querySelectorAll(`[data-quiz-choice="${stepId}"]`).forEach(input => {
    input.addEventListener("change", () => {
      const quizStepId = input.dataset.quizChoice
      const questionIndex = Number(input.dataset.quizQuestion)
      const choiceIndex = Number(input.value)
      activeQuizAnswers = {
        ...activeQuizAnswers,
        [quizStepId]: {
          ...(activeQuizAnswers[quizStepId] || {}),
          [questionIndex]: choiceIndex,
        },
      }
      renderStepWorkspace(steps, materials)
    })
  })

  stepsRoot?.querySelector(`[data-quiz-submit="${stepId}"]`)?.addEventListener("click", () => {
    submitQuizStep(stepId)
  })

  stepsRoot?.querySelector(`[data-step-quiz-close="${stepId}"]`)?.addEventListener("click", () => {
    activeQuizStepId = null
    renderStepWorkspace(steps, materials)
  })
}

function renderStepWorkspace(steps, materials) {
  if (!stepsRoot) return

  const dayGroups = groupStepsByDay(steps)
  if (!dayGroups.length) {
    stepsRoot.innerHTML = `
      <div class="planner-empty-state">
        <h4>No scheduled steps yet</h4>
        <p>Your revision blocks, quizzes, and mock rounds will appear here in order.</p>
      </div>
    `
    renderMaterialViewer(materials, [])
    return
  }

  const previousDayKey = activeDayKey
  activeDayKey = resolveActiveDayKey(dayGroups)
  const activeDayIndex = Math.max(0, dayGroups.findIndex(group => group.key === activeDayKey))
  const activeDay = dayGroups[activeDayIndex] || dayGroups[0]
  const completedCount = activeDay.steps.filter(step => step.status === "done").length
  const activeQuizStep = activeDay.steps.find(step => step.step_id === activeQuizStepId && step.step_type === "mcq_quiz") || null
  const activeDayTone = getDayTone(activeDay)
  const activeDayAccent = getDayAccentLabel(activeDay)
  const activeDaySupportCopy = getDaySupportCopy(activeDay)
  const activeStepLabels = getDayStepLabels(activeDay)
  const railScrollBehavior = previousDayKey && previousDayKey !== activeDay.key ? "smooth" : "auto"

  stepsRoot.innerHTML = `
    <div class="planner-day-shell">
      <div class="planner-day-head">
        <div class="planner-day-copy">
          <span class="summary-label">Timeline</span>
          <h4>${escapeHtml(activeDay.label)} is selected</h4>
          <p>Browse the rail to jump days. Only the selected day expands into full steps below.</p>
        </div>
        <div class="planner-day-nav">
          <button type="button" class="secondary-action planner-day-btn" data-day-nav="prev" ${activeDayIndex === 0 ? "disabled" : ""}>Previous day</button>
          <button type="button" class="secondary-action planner-day-btn" data-day-nav="next" ${activeDayIndex === dayGroups.length - 1 ? "disabled" : ""}>Next day</button>
        </div>
      </div>

      <div class="planner-day-rail-shell">
        <div class="planner-day-rail" data-day-rail>
        ${dayGroups.map(group => {
          const groupDone = group.steps.every(step => step.status === "done")
          const daySummary = getDaySummary(group)
          const hasCheckpoint = dayHasStepType(group, "mcq_quiz")
          const dayTone = getDayTone(group)
          const accentLabel = getDayAccentLabel(group)
          const stepLabels = getDayStepLabels(group)
          return `
            <button
              type="button"
              class="planner-day-pill ${group.key === activeDay.key ? "is-active" : ""} ${hasCheckpoint ? "has-checkpoint" : ""} ${group.steps.length > 1 ? "has-multiple" : ""}"
              data-day-tone="${dayTone}"
              data-day-key="${group.key}"
            >
              <div class="planner-day-pill-top">
                <span>${escapeHtml(group.label)}</span>
                <em>${escapeHtml(accentLabel)}</em>
              </div>
              <strong>${escapeHtml(daySummary)}</strong>
              <div class="planner-day-pill-meta">
                <small>${groupDone ? "Done" : `${group.steps.length} step${group.steps.length === 1 ? "" : "s"}`}</small>
                <small>${groupDone ? "completed" : "planned"}</small>
              </div>
              ${stepLabels.length > 1 ? `<b class="planner-day-pill-count">${stepLabels.length}</b>` : ""}
            </button>
          `
        }).join("")}
        </div>
      </div>

      <div class="planner-day-panel">
        <div class="planner-day-panel-head">
          <div class="planner-day-panel-copy">
            <span class="summary-label">Selected Day</span>
            <h4>${escapeHtml(activeDay.label)}</h4>
            <p>${escapeHtml(activeDaySupportCopy)}</p>
          </div>
          <div class="planner-day-panel-meta">
            <span class="planner-step-tone ${escapeHtml(activeDayTone)}">${escapeHtml(activeDayAccent)}</span>
            <span class="planner-step-status">${completedCount === activeDay.steps.length ? "done" : "in plan"}</span>
          </div>
        </div>

        <div class="planner-day-panel-strip">
          <div class="planner-day-panel-count">
            <strong>${escapeHtml(completedCount)}/${escapeHtml(activeDay.steps.length)}</strong>
            <span>steps complete</span>
          </div>
          <div class="planner-day-panel-tags">
            ${activeStepLabels.map(label => `<span>${escapeHtml(label)}</span>`).join("")}
          </div>
        </div>

        <div class="planner-day-slide">
          ${activeDay.steps.map(step => {
            const snapshot = step.snapshot || {}
            const prompts = (snapshot.practice_prompts || []).slice(0, 1)
            const focusTopics = (snapshot.focus_topics || []).slice(0, 3)
            const stats = getStepStats(step).slice(0, 4)
            const canLaunch = Boolean(snapshot.can_launch_interview)
            const canQuiz = canOpenQuizStep(step)
            const canReview = step.step_type === "revise" && snapshot.material_topic_id
            const actionButtons = []

            if (canLaunch) {
              actionButtons.push(`<button type="button" class="primary-action planner-launch-btn" data-step-launch="${step.step_id}">${escapeHtml(getLaunchLabel(step))}</button>`)
            } else if (canQuiz) {
              actionButtons.push(`<button type="button" class="primary-action planner-quiz-btn" data-step-quiz="${step.step_id}">${escapeHtml(getLaunchLabel(step))}</button>`)
            } else if (canReview) {
              actionButtons.push(`<button type="button" class="secondary-action planner-review-btn" data-review-topic="${escapeHtml(snapshot.material_topic_id)}">Open notes</button>`)
            }

            actionButtons.push(step.status !== "done"
              ? `<button type="button" class="secondary-action planner-done-btn" data-step-complete="${step.step_id}">Mark done</button>`
              : `<button type="button" class="secondary-action planner-done-btn" data-step-reset="${step.step_id}">Mark planned</button>`)

            return `
              <article class="planner-step-card planner-step-card--focused" data-step-id="${step.step_id}">
                <div class="planner-step-head">
                  <div>
                    <span class="planner-step-day">${escapeHtml(step.scheduled_label)}</span>
                    <h4>${escapeHtml(snapshot.headline || getStepTypeLabel(step))}</h4>
                  </div>
                  <div class="planner-step-meta">
                    <span class="planner-step-tone ${getStepTone(step.step_type)}">${escapeHtml(getStepTypeLabel(step))}</span>
                    <span class="planner-step-status">${escapeHtml(step.status)}</span>
                  </div>
                </div>
                <p class="planner-step-copy">${escapeHtml(snapshot.description || "")}</p>
                ${step.topic_title ? `<div class="planner-step-linkage">Linked topic: ${escapeHtml(step.topic_title)}</div>` : ""}
                ${stats.length ? `<div class="planner-step-stats">${stats.map(item => `<span>${escapeHtml(item)}</span>`).join("")}</div>` : ""}
                ${focusTopics.length ? `<div class="planner-chip-row">${focusTopics.map(topic => `<span>${escapeHtml(topic)}</span>`).join("")}</div>` : ""}
                ${prompts.length ? `<div class="planner-prompt-list">${prompts.map(prompt => `<p>${escapeHtml(prompt)}</p>`).join("")}</div>` : ""}
                <div class="planner-step-actions">
                  ${actionButtons.join("")}
                </div>
              </article>
            `
          }).join("")}
        </div>
        ${activeQuizStep ? renderQuizWorkspace(activeQuizStep) : ""}
      </div>
    </div>
  `

  stepsRoot.querySelectorAll("[data-day-nav]").forEach(button => {
    button.addEventListener("click", () => {
      const nextIndex = button.dataset.dayNav === "prev" ? activeDayIndex - 1 : activeDayIndex + 1
      activeDayKey = dayGroups[nextIndex]?.key || activeDay.key
      renderStepWorkspace(steps, materials)
    })
  })
  stepsRoot.querySelectorAll("[data-day-key]").forEach(button => {
    button.addEventListener("click", () => {
      activeDayKey = button.dataset.dayKey
      renderStepWorkspace(steps, materials)
    })
  })
  stepsRoot.querySelectorAll("[data-step-complete]").forEach(button => {
    button.addEventListener("click", () => updateStepStatus(button.dataset.stepComplete, "done"))
  })
  stepsRoot.querySelectorAll("[data-step-reset]").forEach(button => {
    button.addEventListener("click", () => updateStepStatus(button.dataset.stepReset, "planned"))
  })
  stepsRoot.querySelectorAll("[data-step-launch]").forEach(button => {
    button.addEventListener("click", () => launchStudyStep(button.dataset.stepLaunch))
  })
  stepsRoot.querySelectorAll("[data-step-quiz]").forEach(button => {
    button.addEventListener("click", () => {
      activeQuizStepId = activeQuizStepId === button.dataset.stepQuiz ? null : button.dataset.stepQuiz
      renderStepWorkspace(steps, materials)
    })
  })
  stepsRoot.querySelectorAll("[data-review-topic]").forEach(button => {
    button.addEventListener("click", () => {
      activeMaterialTopicId = button.dataset.reviewTopic
      renderMaterialViewer(materials, activeDay.steps)
      materialRoot?.scrollIntoView({ behavior: "smooth", block: "start" })
    })
  })

  if (activeQuizStep) {
    wireQuizWorkspace(activeQuizStep.step_id, steps, materials)
  }

  requestAnimationFrame(() => {
    scrollActiveDayChipIntoView(railScrollBehavior)
  })

  renderMaterialViewer(materials, activeDay.steps)
}

function getCondensedPhases(phases) {
  if (!Array.isArray(phases) || !phases.length) return []
  if (phases.length <= 2) return phases

  const firstPhase = phases[0]
  const laterStartMatch = String(phases[1]?.day_range || "").match(/Day\s+(\d+)/i)
  const laterStartDay = laterStartMatch?.[1]

  return [
    firstPhase,
    {
      day_range: laterStartDay ? `Day ${laterStartDay} onwards` : "Later days",
      title: "Reinforcement and simulation",
      description: "Return for Round 2, move into mixed pressure, and finish with fuller role-style simulation rounds.",
    },
  ]
}

function renderPlanDetail(result) {
  activePlanDetailResult = result || null
  const plan = result?.plan
  const steps = result?.steps || []
  const materials = result?.materials || []
  const progress = result?.progress || null

  if (!plan) {
    activePlanId = null
    activeQuizStepId = null
    if (detailTitle) detailTitle.textContent = "No prep path selected yet"
    if (detailCopy) detailCopy.textContent = "Generate a role-based path to see the phase breakdown, day sequence, and study materials."
    if (phaseStrip) {
      phaseStrip.innerHTML = `
        <div class="planner-empty-state compact">
          <p>The planner will map the preparation into phases once a path is created.</p>
        </div>
      `
    }
    renderProgress(null)
    if (stepsRoot) {
      stepsRoot.innerHTML = `
        <div class="planner-empty-state">
          <h4>No scheduled steps yet</h4>
          <p>Your revision blocks, quizzes, and mock rounds will appear here in order.</p>
        </div>
      `
    }
    renderMaterialViewer([], [])
    return
  }

  activePlanId = plan.plan_id
  if (detailTitle) detailTitle.textContent = plan.title
  if (detailCopy) {
    detailCopy.textContent = `${plan.role_title} - ${plan.target_days} day path - ${plan.completed_steps || 0}/${plan.step_count || 0} steps done`
  }

  if (phaseStrip) {
    const phases = getCondensedPhases(plan.plan_summary?.phases || [])
    phaseStrip.innerHTML = phases.map(phase => `
      <article class="planner-phase-card">
        <span class="summary-label">${escapeHtml(phase.day_range)}</span>
        <strong>${escapeHtml(phase.title)}</strong>
        <p>${escapeHtml(phase.description)}</p>
      </article>
    `).join("")
  }

  applyPlannerReturnContext(result)
  renderProgress(progress)
  renderStepWorkspace(steps, materials)

  renderSavedPlans()
}

async function loadSavedPlans(preferredPlanId = null) {
  const currentUser = getCurrentUser()
  if (!currentUser?.user_id) {
    savedPlans = []
    renderSavedPlans()
    return
  }

  try {
    const response = await authenticatedFetch("/api/study-plans")
    if (!response.ok) {
      throw new Error("Failed to load study plans")
    }

    const result = await response.json()
    savedPlans = Array.isArray(result.plans) ? result.plans : []
    renderSavedPlans()

    if (preferredPlanId) {
      await loadPlanDetail(preferredPlanId)
      return
    }

    if (!activePlanId && savedPlans[0]?.plan_id) {
      await loadPlanDetail(savedPlans[0].plan_id)
    }
  } catch (error) {
    console.error("Failed to load study plans", error)
    setBanner("Saved prep paths could not be loaded right now.", "error")
  }
}

async function loadPlanDetail(planId) {
  if (!planId) return
  try {
    const response = await authenticatedFetch(`/api/study-plans/${planId}`)
    if (!response.ok) {
      throw new Error("Failed to load plan detail")
    }
    const result = await response.json()
    renderPlanDetail(result)
    renderSavedPlans()
  } catch (error) {
    console.error("Failed to load plan detail", error)
    setBanner("The selected prep path could not be loaded.", "error")
  }
}

async function updateStepStatus(stepId, status) {
  if (!activePlanId) return

  try {
    const response = await authenticatedFetch(`/api/study-plans/${activePlanId}/steps/${stepId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    })

    const result = await response.json()
    if (!response.ok || !result.success) {
      throw new Error(result.error || "Failed to update study step")
    }

    setBanner("Prep step progress updated.", "success")
    renderPlanDetail(result)
    await loadSavedPlans(activePlanId)
  } catch (error) {
    console.error("Failed to update study step", error)
    setBanner("That prep step could not be updated right now.", "error")
  }
}

async function submitQuizStep(stepId) {
  if (!activePlanId || !stepId) return

  const step = findStepById(stepId)
  const quizItems = getQuizQuestions(step)
  const answerMap = activeQuizAnswers[stepId] || {}
  const answers = quizItems.map((_, index) => answerMap[index])

  if (!quizItems.length) {
    setBanner("That checkpoint quiz is not available right now.", "error")
    return
  }

  if (answers.some(answer => answer === undefined || answer === null || Number.isNaN(Number(answer)))) {
    setBanner("Answer every checkpoint question before submitting it.", "error")
    return
  }

  try {
    const response = await authenticatedFetch(`/api/study-plans/${activePlanId}/steps/${stepId}/quiz-result`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answers }),
    })

    const result = await response.json()
    if (!response.ok || !result.success) {
      throw new Error(result.error || "Failed to save quiz result")
    }

    renderPlanDetail(result)
    const updatedStep = (result.steps || []).find(item => item.step_id === stepId)
    const updatedScore = updatedStep?.snapshot?.last_score
    setBanner(
      updatedScore !== undefined && updatedScore !== null
        ? `Checkpoint submitted. Score recorded: ${updatedScore}/100.`
        : "Checkpoint submitted and added to the prep path.",
      "success",
    )
    await loadSavedPlans(activePlanId)
  } catch (error) {
    console.error("Failed to submit checkpoint quiz", error)
    setBanner("That checkpoint quiz could not be saved right now.", "error")
  }
}

async function deletePlan(planId) {
  if (!planId) return

  try {
    const response = await authenticatedFetch(`/api/study-plans/${planId}`, { method: "DELETE" })
    const result = await response.json()
    if (!response.ok || !result.success) {
      throw new Error(result.error || "Failed to delete study plan")
    }

    pendingDeletePlanId = null
    savedPlans = savedPlans.filter(item => item.plan_id !== planId)
    if (activePlanId === planId) {
      activePlanId = null
      activePlanDetailResult = null
      activeDayKey = null
      activeMaterialTopicId = null
      activeQuizStepId = null
      renderPlanDetail(null)
    }

    renderSavedPlans()
    setBanner("Prep path deleted.", "success")

    if (!activePlanId && savedPlans[0]?.plan_id) {
      await loadPlanDetail(savedPlans[0].plan_id)
    }
  } catch (error) {
    console.error("Failed to delete study plan", error)
    setBanner("That prep path could not be deleted right now.", "error")
  }
}

async function launchStudyStep(stepId) {
  if (!activePlanId || !stepId) return

  try {
    setBanner("Building the exact interview for this prep step...", "neutral")
    const response = await authenticatedFetch(`/api/study-plans/${activePlanId}/steps/${stepId}/session-plan`)
    const result = await response.json()
    if (!response.ok || !result.success || !result.plan) {
      throw new Error(result.error || "Failed to load prep step interview")
    }

    clearInterviewLaunchContext()
    localStorage.setItem("selectedInterviewMode", "study_step")
    localStorage.setItem("selectedStudyPlanId", activePlanId)
    localStorage.setItem("selectedStudyStepId", stepId)
    localStorage.setItem("selectedDuration", String(result.plan.duration_minutes || 30))

    try {
      await updateStepStatus(stepId, "in_progress")
    } catch (error) {
      console.warn("Could not set step to in progress before launch", error)
    }

    window.location.href = "/interview"
  } catch (error) {
    console.error("Failed to launch study step", error)
    setBanner("That prep step interview could not be opened right now.", "error")
  }
}

async function createPlan(event) {
  event.preventDefault()

  const currentUser = getCurrentUser()
  if (!currentUser?.user_id) {
    setBanner("Sign in first to create and save prep paths.", "error")
    return
  }

  const roleId = roleSelect?.value || ""
  const targetDays = Number(daysInput?.value || 40)
  if (!roleId) {
    setBanner("Choose a role before creating the prep path.", "error")
    return
  }

  if (submitButton) submitButton.disabled = true
  setBanner("Building the prep path from your selected role and timeline...", "neutral")

  try {
    const response = await authenticatedFetch("/api/study-plans", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role_id: roleId, target_days: targetDays }),
    })
    const result = await response.json()

    if (!response.ok || !result.success) {
      throw new Error(result.error || "Failed to create study plan")
    }

    renderPlanDetail(result)
    setBanner("Prep path created. Each topic now includes revision, Round 1, Round 2, and later mixed or mock steps.", "success")
    await loadSavedPlans(result.plan?.plan_id)
  } catch (error) {
    console.error("Failed to create study plan", error)
    setBanner("The prep path could not be created right now.", "error")
  } finally {
    if (submitButton) submitButton.disabled = false
  }
}

async function loadPage() {
  try {
    pendingPlannerReturnContext = readPlannerReturnContext()
    const { roles } = await loadInterviewCatalog()
    roleCatalog = roles
    renderRoleOptions()

    if (roleCount) {
      roleCount.textContent = `${roleCatalog.length} role lanes`
    }

    await loadSavedPlans(pendingPlannerReturnContext?.studyPlanId || null)
  } catch (error) {
    console.error("Failed to load prep planner", error)
    if (roleCount) {
      roleCount.textContent = "Catalog unavailable"
    }
    setBanner("The role catalog could not be loaded for the prep planner.", "error")
  }
}

if (plannerForm) {
  plannerForm.addEventListener("submit", createPlan)
}

renderSavedPlans()
loadPage()
