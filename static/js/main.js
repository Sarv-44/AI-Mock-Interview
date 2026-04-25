import { state, weights } from "./config.js"
import { speak } from "./voice.js"
import { activateReviewPane, resetLiveReadout, setControlState, startRecording, stopRecording } from "./recording.js"
import { getAuthHeaders, getCurrentUser } from "./session.js"

const difficultyDisplay = {
  easy: "Easy",
  medium: "Medium",
  hard: "Hard",
  custom: "Custom",
}

const aiFocusCopy = {
  easy: "The interviewer is checking baseline clarity, communication, and whether you can answer directly.",
  medium: "The interviewer is checking structure, technical depth, and how clearly you connect ideas.",
  hard: "The interviewer is checking depth, tradeoffs, edge cases, and whether you stay composed under pressure.",
  custom: "This round is checking speaking clarity, pacing, answer structure, and whether you stay inside the target time.",
}

const promptNoteCopy = {
  easy: "Keep it crisp. Give the direct answer first, then support it with one clear example.",
  medium: "Explain the reasoning step by step and make the answer feel teachable, not rushed.",
  hard: "Lead with a strong position, then defend it with tradeoffs, assumptions, and edge cases.",
  custom: "Answer clearly, stay structured, and land the response close to the target time for this question.",
}

const coachModeCopy = {
  easy: "Clear and steady",
  medium: "Balanced delivery",
  hard: "High-pressure mode",
  custom: "Custom interview mode",
}

function generateSessionId() {
  return "session_" + Date.now() + "_" + Math.random().toString(36).slice(2, 11)
}

function getQuestions() {
  return state.sessionPlan?.questions || []
}

function getSelectedInterviewMode() {
  return {
    interviewMode: localStorage.getItem("selectedInterviewMode") || "",
    roleId: localStorage.getItem("selectedRole") || "",
    topicId: localStorage.getItem("selectedTopic") || "",
    customTemplateId: localStorage.getItem("selectedCustomInterviewId") || "",
    studyPlanId: localStorage.getItem("selectedStudyPlanId") || "",
    studyStepId: localStorage.getItem("selectedStudyStepId") || "",
    durationMinutes: Number(localStorage.getItem("selectedDuration") || 30),
  }
}

function getStoredCustomPlan() {
  try {
    const parsed = JSON.parse(localStorage.getItem("customInterviewPlan") || "null")
    return parsed && typeof parsed === "object" ? parsed : null
  } catch (error) {
    return null
  }
}

function getQuestionWeight(question = {}) {
  const parsed = Number(question.weight)
  if (!Number.isNaN(parsed) && parsed > 0) return parsed
  return weights[question.difficulty] ?? weights.medium
}

function getQuestionTargetSeconds(question = {}) {
  const parsed = Number(question.target_seconds)
  if (!Number.isNaN(parsed) && parsed > 0) return parsed
  return 0
}

async function saveInterviewToDatabase(interviewData) {
  try {
    const response = await fetch("/save-interview", {
      method: "POST",
      keepalive: true,
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify(interviewData),
    })

    const result = await response.json()
    return result.success
  } catch (error) {
    console.error("Error saving to database:", error)
    return false
  }
}

function resetSessionState() {
  state.currentQuestion = 0
  state.currentDifficulty = "medium"
  state.plannedWeight = 0
  state.weightedScore = 0
  state.totalWeight = 0
  state.confidenceHistory = []
  state.wpmHistory = []
  state.fillerHistory = []
  state.fillerListHistory = []
  state.durations = []
  state.transcripts = []
  state.questionConfidence = []
  state.contentScoreHistory = []
  state.deliveryScoreHistory = []
  state.answerFeedbackHistory = []
}

function setTrackMeta(plan) {
  const trackLabel = document.getElementById("track-label")
  const topicEl = document.getElementById("topic")
  const heroTitle = document.querySelector(".hero-card h2")
  const heroDescription = document.getElementById("ai-focus")
  const studyContext = plan.study_context || {}

  if (trackLabel) {
    trackLabel.innerText = studyContext.study_step_id
      ? "Prep Step"
      : plan.mode === "role"
      ? "Role"
      : plan.mode === "custom"
      ? "Mode"
      : "Topic"
  }

  if (topicEl) {
    topicEl.innerText = plan.title || "Interview"
  }

  if (heroTitle) {
    heroTitle.innerText = studyContext.study_step_id
      ? `${plan.title} from your prep path with linked revision and score tracking.`
      : plan.mode === "role"
      ? `${plan.title} mock interview with mixed, role-aligned questions.`
      : plan.mode === "custom"
      ? `${plan.title} custom interview with delivery-focused analytics.`
      : `${plan.title} interview track with live scoring and coaching.`
  }

  if (heroDescription) {
    heroDescription.innerText = studyContext.study_step_id
      ? `${plan.subtitle} This prep-path step is mapped to ${studyContext.scheduled_label || "your current timeline"} and feeds progress back into the planner.`
      : plan.mode === "role"
      ? `${plan.subtitle} This round is paced as a ${plan.duration_minutes}-minute ${plan.blueprint_label.toLowerCase()}.`
      : plan.mode === "custom"
      ? `${plan.subtitle} This round is paced as a ${plan.duration_minutes}-minute custom interview.`
      : `${plan.subtitle} This round is paced as a ${plan.duration_minutes}-minute ${plan.blueprint_label.toLowerCase()}.`
  }
}

function updateInterviewChrome(diff) {
  const questions = getQuestions()
  const difficultyText = difficultyDisplay[diff] || "Medium"
  const currentDifficulty = document.getElementById("current-difficulty")
  const difficultyPill = document.getElementById("difficulty-pill")
  const aiPromptNote = document.getElementById("ai-prompt-note")
  const aiFocus = document.getElementById("ai-focus")
  const coachMode = document.getElementById("coach-mode")
  const progressText = document.getElementById("progress-text")
  const progressGuidance = document.getElementById("progress-guidance")
  const difficultyLabel = document.getElementById("difficulty-label")
  const activeQuestion = questions[state.currentQuestion] || {}

  if (currentDifficulty) currentDifficulty.innerText = difficultyText
  if (difficultyLabel) difficultyLabel.innerText = state.sessionPlan?.mode === "custom" ? "Mode" : "Difficulty"
  if (difficultyPill) {
    difficultyPill.innerText = state.sessionPlan?.mode === "custom"
      ? `${getQuestionWeight(activeQuestion)} weight`
      : `${difficultyText} difficulty`
  }
  if (aiPromptNote) aiPromptNote.innerText = promptNoteCopy[diff] || promptNoteCopy.medium
  if (aiFocus) {
    const prefix = aiFocusCopy[diff] || aiFocusCopy.medium
    const sessionCopy = state.sessionPlan?.mode === "role"
      ? ` This is part of a ${state.sessionPlan.duration_minutes}-minute ${state.sessionPlan.title} round.`
      : state.sessionPlan?.mode === "custom"
      ? ` This answer is being checked for delivery and time control, not content correction.`
      : ""
    aiFocus.innerText = `${prefix}${sessionCopy}`
  }
  if (coachMode) coachMode.innerText = coachModeCopy[diff] || coachModeCopy.medium
  if (progressText) progressText.innerText = `${state.currentQuestion + 1} / ${questions.length} complete`
  if (progressGuidance) {
    const targetSeconds = getQuestionTargetSeconds(activeQuestion)
    progressGuidance.innerText = state.sessionPlan?.mode === "custom" && targetSeconds
      ? `${targetSeconds}s target`
      : "Keep it concise"
  }
}

function displayQuestion(text) {
  const el = document.getElementById("question")
  if (el) el.innerText = text
}

function resetQuestionUI() {
  state.seconds = 0
  state.isProcessing = false
  state.currentQuestionAnalyzed = false
  resetLiveReadout()
}

function updatePromptMeta(question) {
  const questionIdChip = document.getElementById("question-id-chip")
  const questionTopicChip = document.getElementById("question-topic-chip")
  const questionWeightChip = document.getElementById("question-weight-chip")
  const questionTargetChip = document.getElementById("question-target-chip")

  if (questionIdChip) questionIdChip.innerText = `QID: ${question.question_id || "--"}`
  if (questionTopicChip) {
    questionTopicChip.innerText = state.sessionPlan?.mode === "custom"
      ? "Mode: custom"
      : `Topic: ${question.topic_id || state.sessionPlan?.primary_topic_id || "--"}`
  }

  if (questionWeightChip) {
    if (state.sessionPlan?.mode === "custom") {
      questionWeightChip.hidden = false
      questionWeightChip.innerText = `Weight: ${getQuestionWeight(question)}`
    } else {
      questionWeightChip.hidden = true
    }
  }

  if (questionTargetChip) {
    const targetSeconds = getQuestionTargetSeconds(question)
    if (state.sessionPlan?.mode === "custom" && targetSeconds) {
      questionTargetChip.hidden = false
      questionTargetChip.innerText = `Target: ${targetSeconds}s`
    } else {
      questionTargetChip.hidden = true
    }
  }
}

export function loadQuestion() {
  const questions = getQuestions()

  if (!questions.length) {
    displayQuestion("No questions are available for this interview configuration right now.")
    document.getElementById("status").innerText = "Question bank unavailable"
    setControlState({ canStart: false, canStop: false, canNext: false })
    return
  }

  const question = questions[state.currentQuestion]
  const diff = question.difficulty || "medium"
  state.currentDifficulty = diff

  displayQuestion(question.q)
  activateReviewPane("transcript")
  resetQuestionUI()

  document.getElementById("qnum").innerText = `Question ${state.currentQuestion + 1} of ${questions.length}`
  updatePromptMeta(question)

  const progress = ((state.currentQuestion + 1) / questions.length) * 100
  document.getElementById("progress-bar").style.width = progress + "%"
  document.getElementById("stage-label").innerText = question.section_label
    ? `${String(question.section_label).replaceAll("_", " ")} prompt`
    : "Prompt delivered"
  document.getElementById("response-state").innerText = "Ready to answer"

  updateInterviewChrome(diff)
  setControlState({ canStart: true, canStop: false, canNext: false })

  speak(question.q)
}

function setupInterviewChromeUI() {
  const reviewTabs = document.querySelectorAll("[data-review-pane]")

  reviewTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      activateReviewPane(tab.dataset.reviewPane)
    })
  })
}

export function nextQuestion() {
  const questions = getQuestions()

  if (state.isRecording || state.isProcessing) {
    document.getElementById("status").innerText =
      "Finish recording and wait for analysis before moving to the next question."
    return
  }

  if (!state.currentQuestionAnalyzed) {
    document.getElementById("status").innerText =
      "Answer this question and wait for analysis before moving on."
    return
  }

  state.currentQuestion++

  if (state.currentQuestion >= questions.length) {
    void showFinalScore()
    return
  }

  loadQuestion()
}

function buildSummary(plan, finalScore, confidenceHistory, contentScoreHistory, deliveryScoreHistory, wpmHistory, fillerHistory, sessionId, userId = null) {
  const timingFeedback = (state.answerFeedbackHistory || []).map(item => item || {})
  const studyContext = plan.study_context || {}
  return {
    topic: plan.mode === "custom" ? "custom" : (plan.primary_topic_id || plan.topic_id || plan.role_id || ""),
    sessionTitle: plan.title || "Interview Session",
    sessionMode: plan.mode || "topic",
    roleId: plan.role_id || null,
    customTemplateId: plan.template_id || null,
    durationMinutes: plan.duration_minutes || 30,
    finalScore,
    questionsTotal: getQuestions().length,
    confidenceHistory,
    contentScoreHistory,
    deliveryScoreHistory,
    wpmHistory,
    fillerHistory,
    targetSecondsHistory: timingFeedback.map(item => item.time_target_seconds || 0),
    timeDeltaHistory: timingFeedback.map(item => item.time_target_delta_seconds || 0),
    timeStatusHistory: timingFeedback.map(item => item.time_target_status || "not_set"),
    sessionId,
    userId,
    studyPlanId: studyContext.study_plan_id || null,
    studyStepId: studyContext.study_step_id || null,
    studyStepType: studyContext.step_type || null,
    studyRoundStage: studyContext.round_stage || null,
  }
}

async function showFinalScore() {
  const questions = getQuestions()
  const plan = state.sessionPlan || {}

  const transcripts = state.transcripts || []
  const confidenceHistory = state.confidenceHistory || []
  const wpmHistory = state.wpmHistory || []
  const durations = state.durations || []
  const fillerHistory = state.fillerHistory || []
  const fillerListHistory = state.fillerListHistory || []
  const contentScoreHistory = state.contentScoreHistory || []
  const deliveryScoreHistory = state.deliveryScoreHistory || []
  const answerFeedbackHistory = state.answerFeedbackHistory || []
  const targetSecondsHistory = answerFeedbackHistory.map(item => item?.time_target_seconds || 0)
  const timeDeltaHistory = answerFeedbackHistory.map(item => item?.time_target_delta_seconds || 0)
  const timeStatusHistory = answerFeedbackHistory.map(item => item?.time_target_status || "not_set")

  const weightedScore = questions.reduce((sum, question, index) => {
    const confidence = confidenceHistory[index]
    if (typeof confidence !== "number") return sum
    return sum + (confidence * getQuestionWeight(question))
  }, 0)

  const appliedWeight = questions.reduce((sum, question, index) => {
    return typeof confidenceHistory[index] === "number"
      ? sum + getQuestionWeight(question)
      : sum
  }, 0)

  const denom = appliedWeight || state.plannedWeight || 1
  const finalScore = Math.round(weightedScore / denom)

  const detailedQuestions = questions.map((question, index) => ({
    question_id: question.question_id,
    topic_id: question.topic_id,
    question: question.q,
    answer: transcripts[index] || "No recording available",
    transcript: transcripts[index] || "No transcript available",
    confidence: confidenceHistory[index] || 0,
    content_score: contentScoreHistory[index] || 0,
    delivery_score: deliveryScoreHistory[index] || 0,
    wpm: wpmHistory[index] || 0,
    duration: durations[index] || 0,
    filler_words: fillerListHistory[index] || [],
    filler_count: fillerHistory[index] || 0,
    feedback: answerFeedbackHistory[index] || {},
    difficulty: question.difficulty || "medium",
    weight: getQuestionWeight(question),
    target_seconds: getQuestionTargetSeconds(question),
    time_target_status: answerFeedbackHistory[index]?.time_target_status || "not_set",
    time_target_delta_seconds: answerFeedbackHistory[index]?.time_target_delta_seconds || 0,
    sample_answer: question.sample_answer || "",
    ideal_answer: question.ideal_answer || "",
    section_label: question.section_label || "",
  }))

  const sessionId = localStorage.getItem("sessionId") || generateSessionId()
  const studyContext = plan.study_context || {}
  const interviewData = {
    session_id: sessionId,
    topic: plan.mode === "custom" ? "custom" : (plan.primary_topic_id || plan.topic_id || plan.role_id || "general"),
    session_mode: plan.mode || "topic",
    role_id: plan.role_id || null,
    session_title: plan.title || "Interview Session",
    custom_template_id: plan.template_id || null,
    analytics_mode: plan.analytics_mode || "full",
    primary_topic_id: plan.primary_topic_id || plan.topic_id || null,
    duration_minutes: plan.duration_minutes || 30,
    final_score: finalScore,
    questions: detailedQuestions,
    questions_total: questions.length,
    confidence_history: confidenceHistory,
    content_score_history: contentScoreHistory,
    delivery_score_history: deliveryScoreHistory,
    wpm_history: wpmHistory,
    filler_history: fillerHistory,
    target_seconds_history: targetSecondsHistory,
    time_delta_history: timeDeltaHistory,
    time_status_history: timeStatusHistory,
    interview_date: new Date().toISOString(),
    study_plan_id: studyContext.study_plan_id || null,
    study_step_id: studyContext.study_step_id || null,
    study_step_type: studyContext.step_type || null,
    study_round_stage: studyContext.round_stage || null,
  }

  const currentUser = getCurrentUser()
  if (currentUser?.user_id) {
    interviewData.user_id = currentUser.user_id
  }

  const summary = buildSummary(
    plan,
    finalScore,
    confidenceHistory,
    contentScoreHistory,
    deliveryScoreHistory,
    wpmHistory,
    fillerHistory,
    sessionId,
    currentUser?.user_id || null,
  )

  localStorage.setItem("interviewSummary", JSON.stringify(summary))
  localStorage.setItem("sessionId", sessionId)
  localStorage.setItem("interviewSaveState", "pending")

  const statusNode = document.getElementById("status")
  if (statusNode) {
    statusNode.innerText = "Saving session and syncing prep-path progress..."
  }

  const saveSucceeded = await saveInterviewToDatabase(interviewData)
  localStorage.setItem("interviewSaveState", saveSucceeded ? "saved" : "failed")
  window.location.href = "/results"
}

async function initializeInterview() {
  const { roleId, topicId, durationMinutes, interviewMode, customTemplateId, studyPlanId, studyStepId } = getSelectedInterviewMode()
  const params = new URLSearchParams()

  try {
    let plan = null

    if (interviewMode === "study_step") {
      if (!studyPlanId || !studyStepId) {
        throw new Error("No study step was selected")
      }
      const response = await fetch(`/api/study-plans/${studyPlanId}/steps/${studyStepId}/session-plan`, {
        headers: getAuthHeaders(),
      })
      const result = await response.json()
      if (!result.success || !result.plan) {
        throw new Error(result.error || "Failed to load study step interview")
      }
      plan = result.plan
    } else if (interviewMode === "custom") {
      const storedPlan = getStoredCustomPlan()
      if (storedPlan?.questions?.length) {
        plan = storedPlan
      } else if (customTemplateId) {
        const response = await fetch(`/api/custom-interviews/${customTemplateId}/session-plan`, {
          headers: getAuthHeaders(),
        })
        const result = await response.json()
        if (!result.success || !result.plan) {
          throw new Error(result.error || "Failed to load custom interview plan")
        }
        plan = result.plan
      } else {
        throw new Error("No custom interview plan is available")
      }
    } else {
      if (roleId) {
        params.set("role_id", roleId)
      } else if (topicId) {
        params.set("topic_id", topicId)
      } else {
        params.set("topic_id", "graphs")
      }

      params.set("duration_minutes", String(durationMinutes || 30))

      const response = await fetch(`/api/interview/session-plan?${params.toString()}`)
      const result = await response.json()

      if (!result.success || !result.plan) {
        throw new Error(result.error || "Failed to build interview plan")
      }
      plan = result.plan
    }

    resetSessionState()
    state.sessionPlan = plan
    state.plannedWeight = getQuestions().reduce((sum, question) => (
      sum + getQuestionWeight(question)
    ), 0)

    setTrackMeta(plan)
    loadQuestion()
  } catch (error) {
    console.error("Failed to initialize interview", error)
    displayQuestion("We could not build your interview plan right now.")
    document.getElementById("status").innerText = "Interview plan unavailable"
    document.getElementById("response-state").innerText = "Unavailable"
    setControlState({ canStart: false, canStop: false, canNext: false })
  }
}

window.startRecording = startRecording
window.stopRecording = stopRecording
window.speakQuestion = () => {
  const questions = getQuestions()
  if (!questions.length) return
  speak(questions[state.currentQuestion].q)
}
window.nextQuestion = nextQuestion

setupInterviewChromeUI()
initializeInterview()
