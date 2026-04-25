import { authenticatedFetch, getCurrentUser } from "./session.js"

const summaryRaw = localStorage.getItem("interviewSummary")
let summary = null

try {
  summary = summaryRaw ? JSON.parse(summaryRaw) : null
} catch (error) {
  console.error("Failed to parse interview summary", error)
}

const ratingButtons = Array.from(document.querySelectorAll("[data-rating]"))
const ratingSummaryPill = document.getElementById("rating-summary-pill")
const ratingHelper = document.getElementById("rating-helper")
const returnToPlanButton = document.getElementById("return-to-plan-btn")
const chartRegistry = []
const PLANNER_RETURN_STORAGE_KEY = "plannerReturnContext"

const num = value => {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

const clamp = (value, min, max) => Math.min(max, Math.max(min, value))
const avg = values => values.length ? Math.round(values.reduce((sum, value) => sum + num(value), 0) / values.length) : 0
const sum = values => values.reduce((total, value) => total + num(value), 0)

function stddev(values) {
  if (values.length <= 1) return 0
  const mean = values.reduce((total, value) => total + value, 0) / values.length
  const variance = values.reduce((total, value) => total + ((value - mean) ** 2), 0) / values.length
  return Math.sqrt(variance)
}

function title(value) {
  return String(value || "")
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ")
}

function textForQuestion(question) {
  return question.question || question.question_text || question.q || "Interview question"
}

function durationLabel(seconds) {
  const total = Math.max(0, Math.round(num(seconds)))
  const minutes = Math.floor(total / 60)
  const rest = total % 60
  return minutes ? `${minutes}m ${String(rest).padStart(2, "0")}s` : `${rest}s`
}

function truncate(text, limit = 220) {
  const value = String(text || "").trim()
  if (!value) return "No transcript available for this answer."
  return value.length <= limit ? value : `${value.slice(0, limit).trim()}...`
}

function setText(id, value) {
  const node = document.getElementById(id)
  if (node) node.textContent = value
}

function setPills(id, values) {
  const node = document.getElementById(id)
  if (node) node.innerHTML = values.map(value => `<span>${value}</span>`).join("")
}

function sessionLabel(data) {
  if (!data) return "-"
  return data.sessionTitle || (data.topic ? title(data.topic) : "Interview Session")
}

function isRateable(data) {
  return Boolean(data && data.sessionMode === "topic" && data.topic)
}

function inferQuestions(data) {
  const count = Math.max(
    data.questionsTotal || 0,
    data.confidenceHistory?.length || 0,
    data.contentScoreHistory?.length || 0,
    data.deliveryScoreHistory?.length || 0,
    data.wpmHistory?.length || 0,
    data.fillerHistory?.length || 0,
  )

  return Array.from({ length: count }, (_, index) => ({
    question_id: `q_${index + 1}`,
    question: `Question ${index + 1}`,
    transcript: "",
    confidence: num(data.confidenceHistory?.[index]),
    content_score: num(data.contentScoreHistory?.[index]),
    delivery_score: num(data.deliveryScoreHistory?.[index]),
    wpm: num(data.wpmHistory?.[index]),
    duration: num(data.durationHistory?.[index]),
    filler_count: num(data.fillerHistory?.[index]),
    filler_words: [],
    target_seconds: num(data.targetSecondsHistory?.[index]),
    time_target_status: data.timeStatusHistory?.[index] || "not_set",
    time_target_delta_seconds: num(data.timeDeltaHistory?.[index]),
    difficulty: "mixed",
    weight: 1,
    feedback: {
      overall_score: num(data.overallScoreHistory?.[index]) || num(data.confidenceHistory?.[index]),
    },
  }))
}

function normalizeSummary(source) {
  if (!source) return null

  const inputQuestions = source.questionDetails || source.questions || []
  const questionDetails = inputQuestions.map((question, index) => ({
    ...question,
    question_id: question.question_id || `q_${index + 1}`,
    question: textForQuestion(question),
    transcript: question.transcript || question.answer || "",
    confidence: num(question.confidence),
    content_score: num(question.content_score),
    delivery_score: num(question.delivery_score),
    wpm: num(question.wpm),
    duration: num(question.duration),
    filler_count: num(question.filler_count ?? question.filler_words?.length ?? source.fillerHistory?.[index]),
    filler_words: Array.isArray(question.filler_words) ? question.filler_words : [],
    target_seconds: num(question.target_seconds ?? source.targetSecondsHistory?.[index]),
    time_target_status: question.time_target_status || source.timeStatusHistory?.[index] || "not_set",
    time_target_delta_seconds: num(question.time_target_delta_seconds ?? source.timeDeltaHistory?.[index]),
    difficulty: question.difficulty || "mixed",
    weight: num(question.weight || 1) || 1,
    feedback: question.feedback || {},
  }))

  const derivedQuestions = questionDetails.length ? questionDetails : inferQuestions(source)

  return {
    topic: source.topic || "Interview Session",
    sessionTitle: source.sessionTitle || source.session_title || "Interview Session",
    sessionMode: source.sessionMode || source.session_mode || "topic",
    roleId: source.roleId || source.role_id || null,
    customTemplateId: source.customTemplateId || source.custom_template_id || null,
    durationMinutes: num(source.durationMinutes || source.duration_minutes || 30) || 30,
    finalScore: num(source.finalScore ?? source.final_score),
    questionsTotal: num(source.questionsTotal || source.questions_total || derivedQuestions.length),
    confidenceHistory: (source.confidenceHistory || source.confidence_history || derivedQuestions.map(question => question.confidence)).map(num),
    contentScoreHistory: (source.contentScoreHistory || source.content_score_history || derivedQuestions.map(question => question.content_score)).map(num),
    deliveryScoreHistory: (source.deliveryScoreHistory || source.delivery_score_history || derivedQuestions.map(question => question.delivery_score)).map(num),
    overallScoreHistory: (source.overallScoreHistory || derivedQuestions.map(question => num(question.feedback?.overall_score) || question.confidence)).map(num),
    wpmHistory: (source.wpmHistory || source.wpm_history || derivedQuestions.map(question => question.wpm)).map(num),
    fillerHistory: (source.fillerHistory || source.filler_history || derivedQuestions.map(question => question.filler_count)).map(num),
    durationHistory: (source.durationHistory || source.duration_history || derivedQuestions.map(question => question.duration)).map(num),
    targetSecondsHistory: (source.targetSecondsHistory || source.target_seconds_history || derivedQuestions.map(question => question.target_seconds)).map(num),
    timeDeltaHistory: (source.timeDeltaHistory || source.time_delta_history || derivedQuestions.map(question => question.time_target_delta_seconds)).map(num),
    timeStatusHistory: source.timeStatusHistory || source.time_status_history || derivedQuestions.map(question => question.time_target_status || "not_set"),
    sessionId: source.sessionId || source.session_id || localStorage.getItem("sessionId") || null,
    userId: source.userId || source.user_id || null,
    studyPlanId: source.studyPlanId || source.study_plan_id || null,
    studyStepId: source.studyStepId || source.study_step_id || null,
    questionDetails: derivedQuestions,
  }
}

function buildSummaryFromSession(session) {
  const details = session.complete_data || {}
  return normalizeSummary({
    topic: session.topic || details.topic || "Interview Session",
    sessionTitle: details.session_title || details.role_title || session.topic || "Interview Session",
    sessionMode: details.session_mode || session.session_mode || "topic",
    roleId: details.role_id || session.role_id || null,
    customTemplateId: details.custom_template_id || null,
    durationMinutes: details.duration_minutes || 30,
    finalScore: session.final_score ?? details.final_score ?? 0,
    questionsTotal: details.questions_total || details.questions?.length || 0,
    confidenceHistory: details.confidence_history || [],
    contentScoreHistory: details.content_score_history || [],
    deliveryScoreHistory: details.delivery_score_history || [],
    wpmHistory: details.wpm_history || [],
    fillerHistory: details.filler_history || [],
    durationHistory: details.duration_history || details.questions?.map(question => question.duration || 0) || [],
    targetSecondsHistory: details.target_seconds_history || details.questions?.map(question => question.target_seconds || 0) || [],
    timeDeltaHistory: details.time_delta_history || details.questions?.map(question => question.time_target_delta_seconds || 0) || [],
    timeStatusHistory: details.time_status_history || details.questions?.map(question => question.time_target_status || "not_set") || [],
    questionDetails: details.questions || [],
    sessionId: session.session_id,
    userId: session.user_id || details.user_id || null,
    studyPlanId: details.study_plan_id || null,
    studyStepId: details.study_step_id || null,
  })
}

function configurePrepPathReturn(data) {
  if (!returnToPlanButton) return

  if (!data?.studyPlanId || !data?.studyStepId) {
    returnToPlanButton.hidden = true
    returnToPlanButton.onclick = null
    return
  }

  returnToPlanButton.hidden = false
  returnToPlanButton.onclick = () => {
    localStorage.setItem(PLANNER_RETURN_STORAGE_KEY, JSON.stringify({
      studyPlanId: data.studyPlanId,
      studyStepId: data.studyStepId,
      finalScore: data.finalScore || 0,
      sessionId: data.sessionId || null,
    }))
    const params = new URLSearchParams({
      plan: data.studyPlanId,
      step: data.studyStepId,
    })
    window.location.href = `/prep-paths?${params.toString()}`
  }
}
function buildMetrics(data) {
  const fillerWords = data.questionDetails.flatMap(question => Array.isArray(question.filler_words) ? question.filler_words : [])
  const statuses = data.timeStatusHistory.filter(Boolean)
  const targetAwareCount = statuses.filter(status => status !== "not_set").length
  const onTargetCount = statuses.filter(status => status === "on_target").length
  const paceControl = data.wpmHistory.length
    ? Math.round((data.wpmHistory.filter(value => value >= 120 && value <= 165).length / data.wpmHistory.length) * 100)
    : 0
  const overall = data.questionDetails.map(question =>
    num(question.feedback?.overall_score) || question.confidence || Math.round((question.content_score + question.delivery_score + question.confidence) / 3)
  )
  const strongest = [
    { label: "Confidence", value: avg(data.confidenceHistory) },
    { label: "Content", value: avg(data.contentScoreHistory) },
    { label: "Delivery", value: avg(data.deliveryScoreHistory) },
    { label: "Pace Control", value: paceControl },
    { label: "Timing", value: targetAwareCount ? Math.round((onTargetCount / targetAwareCount) * 100) : 0 },
  ].sort((left, right) => right.value - left.value)[0] || { label: "Confidence", value: 0 }

  return {
    avgConfidence: avg(data.confidenceHistory),
    avgContent: avg(data.contentScoreHistory),
    avgDelivery: avg(data.deliveryScoreHistory),
    avgWpm: avg(data.wpmHistory),
    avgDuration: avg(data.durationHistory),
    totalFillers: sum(data.fillerHistory),
    paceControl,
    consistency: overall.length ? clamp(Math.round(100 - (stddev(overall) * 1.8)), 0, 100) : 0,
    targetAwareCount,
    onTargetCount,
    strongest,
    fillerWords,
    bestQuestion: [...data.questionDetails].sort((a, b) => (num(b.feedback?.overall_score) || b.confidence) - (num(a.feedback?.overall_score) || a.confidence))[0],
    weakestQuestion: [...data.questionDetails].sort((a, b) => (num(a.feedback?.overall_score) || a.confidence) - (num(b.feedback?.overall_score) || b.confidence))[0],
  }
}

function buildAnalysis(data, metrics) {
  const strengths = []
  const risks = []
  if (metrics.avgConfidence >= 75) strengths.push("Confident openings")
  if (metrics.avgContent >= 72) strengths.push("Technical depth")
  if (metrics.avgDelivery >= 72) strengths.push("Delivery control")
  if (metrics.paceControl >= 70) strengths.push("Steady pacing")
  if (metrics.targetAwareCount && metrics.onTargetCount / metrics.targetAwareCount >= 0.6) strengths.push("Time discipline")
  if (metrics.totalFillers <= data.questionDetails.length * 2) strengths.push("Low filler load")
  if (!strengths.length) strengths.push("Baseline completion")

  if (metrics.avgConfidence < 60) risks.push("Low confidence")
  if (metrics.avgContent < 60) risks.push("Thin technical depth")
  if (metrics.avgDelivery < 60) risks.push("Delivery inconsistency")
  if (metrics.paceControl < 55) risks.push("Unsteady pacing")
  if (metrics.targetAwareCount && metrics.onTargetCount / metrics.targetAwareCount < 0.45) risks.push("Timing drift")
  if (metrics.totalFillers > data.questionDetails.length * 3) risks.push("Heavy filler usage")
  if (metrics.consistency < 65) risks.push("Question-to-question volatility")
  if (!risks.length) risks.push("Keep stretching answer depth")

  const paceTrend = data.wpmHistory.length > 2
    ? data.wpmHistory.at(-1) > data.wpmHistory[0] + 8 ? "accelerated" : data.wpmHistory.at(-1) < data.wpmHistory[0] - 8 ? "slowed down" : "stayed fairly stable"
    : "stayed fairly stable"

  let performance = `Across ${data.questionsTotal || data.questionDetails.length} questions, your strongest signal was ${metrics.strongest.label.toLowerCase()} at ${metrics.strongest.value}. `
  performance += `Consistency landed at ${metrics.consistency}/100, and speaking pace ${paceTrend} through the round. `
  performance += metrics.targetAwareCount
    ? `${metrics.onTargetCount} of ${metrics.targetAwareCount} answers landed near the intended timing window.`
    : `Average speech speed was ${metrics.avgWpm} WPM with ${metrics.totalFillers} filler words across the session.`

  let quality = "Your answers were strongest when you paired delivery with clearer reasoning."
  if (metrics.avgContent >= 70 && metrics.avgDelivery >= 70) {
    quality = "This session sounded interview-ready in multiple places: delivery was controlled and the reasoning usually held together."
  } else if (metrics.avgContent < 60 && metrics.avgDelivery >= 65) {
    quality = "Delivery was often better than the technical depth. The next upgrade is adding fuller reasoning, examples, and tradeoffs."
  } else if (metrics.avgDelivery < 60 && metrics.avgContent >= 65) {
    quality = "The ideas were often there, but the delivery did not always make them land cleanly. Better pacing and cleaner sentence boundaries would help quickly."
  }

  const tips = []
  if (metrics.avgContent < 65) tips.push("Push each answer one layer deeper with reasoning, tradeoffs, or a concrete example.")
  if (metrics.avgDelivery < 65) tips.push("Tighten answer structure so your main point lands in the first sentence.")
  if (metrics.paceControl < 60) tips.push("Bring your speaking pace closer to the 120-165 WPM control band.")
  if (metrics.totalFillers > data.questionDetails.length * 3) tips.push("Replace filler words with short pauses between ideas.")
  if (metrics.targetAwareCount && metrics.onTargetCount / metrics.targetAwareCount < 0.5) tips.push("Practice landing closer to the target answer window instead of drifting long or short.")
  if (metrics.consistency < 65) tips.push("Rehearse weak question types until the round feels more even from start to finish.")

  return {
    performance,
    quality,
    recommendations: tips.join(" ") || "Keep the same format, but focus on making every answer sound as strong as your best one.",
    strengths: strengths.slice(0, 5),
    risks: risks.slice(0, 5),
  }
}

function palette() {
  const styles = getComputedStyle(document.body)
  const primary = styles.getPropertyValue("--ambient-primary").trim() || "94, 168, 255"
  const secondary = styles.getPropertyValue("--ambient-secondary").trim() || "94, 230, 209"
  const tertiary = styles.getPropertyValue("--ambient-tertiary").trim() || "255, 192, 136"
  return {
    text: "#d9e6f3",
    grid: "rgba(255,255,255,0.06)",
    primary: `rgba(${primary}, 1)`,
    primaryFill: `rgba(${primary}, 0.16)`,
    secondary: `rgba(${secondary}, 1)`,
    secondaryFill: `rgba(${secondary}, 0.16)`,
    warm: `rgba(${tertiary}, 0.95)`,
  }
}

function chartOptions() {
  const colors = palette()
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: colors.text } },
      tooltip: {
        backgroundColor: "rgba(10, 18, 28, 0.94)",
        borderColor: "rgba(255,255,255,0.08)",
        borderWidth: 1,
        titleColor: "#f7fbff",
        bodyColor: colors.text,
      },
    },
    scales: {
      x: { ticks: { color: colors.text }, grid: { color: colors.grid } },
      y: { ticks: { color: colors.text }, grid: { color: colors.grid }, suggestedMin: 0, suggestedMax: 100 },
    },
  }
}

function destroyCharts() {
  while (chartRegistry.length) chartRegistry.pop()?.destroy()
}

function pushChart(id, config) {
  const canvas = document.getElementById(id)
  if (!canvas || typeof Chart === "undefined") return
  chartRegistry.push(new Chart(canvas.getContext("2d"), config))
}

function createCharts(data, metrics) {
  destroyCharts()
  const colors = palette()
  const labels = data.questionDetails.map((_, index) => `Q${index + 1}`)

  pushChart("performanceBlendChart", {
    type: "line",
    data: {
      labels,
      datasets: [
        { label: "Confidence", data: data.confidenceHistory, borderColor: colors.primary, backgroundColor: colors.primaryFill, fill: true, tension: 0.35 },
        { label: "Content", data: data.contentScoreHistory, borderColor: colors.secondary, backgroundColor: colors.secondaryFill, tension: 0.35 },
        { label: "Delivery", data: data.deliveryScoreHistory, borderColor: colors.warm, backgroundColor: "rgba(255,255,255,0)", tension: 0.35 },
      ],
    },
    options: chartOptions(),
  })

  pushChart("questionBreakdownChart", {
    type: "bar",
    data: {
      labels,
      datasets: [
        { label: "Overall", data: data.overallScoreHistory, backgroundColor: colors.primary, borderRadius: 10 },
        { label: "Content", data: data.contentScoreHistory, backgroundColor: colors.secondary, borderRadius: 10 },
        { label: "Delivery", data: data.deliveryScoreHistory, backgroundColor: colors.warm, borderRadius: 10 },
      ],
    },
    options: chartOptions(),
  })

  pushChart("deliveryRadarChart", {
    type: "radar",
    data: {
      labels: ["Confidence", "Content", "Delivery", "Pace", "Timing", "Clarity"],
      datasets: [{
        label: "Session Shape",
        data: [
          metrics.avgConfidence,
          metrics.avgContent,
          metrics.avgDelivery,
          metrics.paceControl,
          metrics.targetAwareCount ? Math.round((metrics.onTargetCount / metrics.targetAwareCount) * 100) : 0,
          clamp(100 - ((metrics.totalFillers / Math.max(data.questionDetails.length, 1)) * 12), 0, 100),
        ],
        borderColor: colors.primary,
        backgroundColor: colors.primaryFill,
        pointBackgroundColor: colors.warm,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        r: {
          angleLines: { color: colors.grid },
          grid: { color: colors.grid },
          pointLabels: { color: colors.text },
          ticks: { color: colors.text, backdropColor: "transparent" },
          suggestedMin: 0,
          suggestedMax: 100,
        },
      },
    },
  })
  const fillerCounts = {}
  metrics.fillerWords.forEach(word => {
    const key = word || "unspecified"
    fillerCounts[key] = (fillerCounts[key] || 0) + 1
  })
  if (!Object.keys(fillerCounts).length) fillerCounts["No fillers"] = 1

  pushChart("fillerChart", {
    type: "doughnut",
    data: {
      labels: Object.keys(fillerCounts),
      datasets: [{
        data: Object.values(fillerCounts),
        backgroundColor: [colors.primary, colors.secondary, colors.warm, "#ff7c73", "#9e8cff", "#f7d27b"],
        borderWidth: 0,
      }],
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom", labels: { color: colors.text } } } },
  })

  const timingCounts = data.timeStatusHistory.reduce((bucket, status) => {
    const key = status || "not_set"
    bucket[key] = (bucket[key] || 0) + 1
    return bucket
  }, {})
  if (!Object.keys(timingCounts).length) timingCounts.not_set = data.questionDetails.length || 1

  pushChart("timingMixChart", {
    type: "doughnut",
    data: {
      labels: Object.keys(timingCounts).map(title),
      datasets: [{
        data: Object.values(timingCounts),
        backgroundColor: [colors.secondary, colors.warm, colors.primary, "rgba(255,255,255,0.16)"],
        borderWidth: 0,
      }],
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom", labels: { color: colors.text } } } },
  })

  pushChart("scoreGaugeChart", {
    type: "doughnut",
    data: {
      labels: ["Score", "Remaining"],
      datasets: [{ data: [data.finalScore || 0, Math.max(0, 100 - (data.finalScore || 0))], backgroundColor: [colors.warm, "rgba(255,255,255,0.08)"], borderWidth: 0 }],
    },
    options: { responsive: true, maintainAspectRatio: false, cutout: "74%", plugins: { legend: { display: false } } },
  })
}

function renderHeroTags(data) {
  const node = document.getElementById("result-hero-tags")
  if (!node) return
  const tags = [title(data.sessionMode), `${data.durationMinutes || 30} min round`]
  if (data.studyStepId) tags.push("Prep path linked")
  if (data.roleId) tags.push(title(data.roleId))
  else if (data.topic && data.topic !== "custom") tags.push(title(data.topic))
  node.innerHTML = tags.map(tag => `<span>${tag}</span>`).join("")
}

function renderQuestionReview(data) {
  const node = document.getElementById("question-review-root")
  if (!node) return
  if (!data.questionDetails.length) {
    node.innerHTML = `<div class="question-review-empty"><p>Question-level analytics are not available for this session yet.</p></div>`
    return
  }

  node.innerHTML = data.questionDetails.map((question, index) => {
    const overall = num(question.feedback?.overall_score) || question.confidence
    const timing = question.target_seconds
      ? `${title(question.time_target_status)} | ${Math.abs(num(question.time_target_delta_seconds))}s delta`
      : "No target timing"
    return `
      <article class="question-review-item">
        <div class="question-review-head">
          <span class="question-review-order">${String(index + 1).padStart(2, "0")}</span>
          <div>
            <p class="section-kicker">${title(question.difficulty || "mixed")}</p>
            <h4>${textForQuestion(question)}</h4>
          </div>
        </div>
        <div class="question-review-metrics">
          <span>Overall ${overall}</span>
          <span>Content ${question.content_score}</span>
          <span>Delivery ${question.delivery_score}</span>
        </div>
        <div class="question-review-meta">
          <span>${question.wpm} WPM</span>
          <span>${question.filler_count} fillers</span>
          <span>${durationLabel(question.duration)}</span>
        </div>
        <div class="question-review-transcript"><p>${truncate(question.transcript || question.answer)}</p></div>
        <div class="question-review-meta">
          <span>${timing}</span>
          <span>Weight ${question.weight}</span>
        </div>
      </article>
    `
  }).join("")
}

function renderMissing() {
  ;[
    "result-topic", "result-mode", "result-score", "result-strongest-signal", "result-questions", "result-consistency",
    "result-avg-duration", "result-pace-control", "result-avg-confidence", "result-avg-content", "result-avg-delivery",
    "result-avg-wpm", "result-total-fillers", "result-timing-adherence", "result-duration", "result-target-timing",
    "result-best-question", "result-weakest-question",
  ].forEach(id => setText(id, "-"))
  setText("result-title", "No Interview Summary Found")
  setText("result-subtitle", "Finish an interview first, then this page will show your transcript analytics and final report.")
  setText("performance-trends", "No completed session is available yet.")
  setText("answer-quality", "Run a mock interview to generate answer quality feedback.")
  setText("recommendations", "Start a topic, answer all questions, and come back here for the report.")
  setText("result-tips", "Your next step is to complete one interview session.")
  renderHeroTags({ sessionMode: "Unavailable", durationMinutes: 0, topic: "" })
  setPills("result-strengths", ["No data yet"])
  setPills("result-risks", ["Complete a session first"])
  renderQuestionReview({ questionDetails: [] })
  document.getElementById("pdf-btn")?.setAttribute("disabled", "true")
  if (returnToPlanButton) returnToPlanButton.hidden = true
  ratingButtons.forEach(button => { button.disabled = true })
  if (ratingSummaryPill) {
    ratingSummaryPill.textContent = "Unavailable"
    ratingSummaryPill.dataset.tone = "error"
  }
  if (ratingHelper) ratingHelper.textContent = "Ratings unlock after a completed interview session."
}
async function loadDetailedSummary() {
  const baseSummary = normalizeSummary(summary)
  if (!baseSummary?.sessionId) return baseSummary
  try {
    const response = await authenticatedFetch(`/get-session/${baseSummary.sessionId}`)
    if (!response.ok) return baseSummary
    const result = await response.json()
    if (!result.success || !result.data) return baseSummary
    const detailedSummary = buildSummaryFromSession(result.data)
    return normalizeSummary({
      ...detailedSummary,
      studyPlanId: detailedSummary?.studyPlanId || baseSummary.studyPlanId || null,
      studyStepId: detailedSummary?.studyStepId || baseSummary.studyStepId || null,
    })
  } catch (error) {
    console.error("Failed to load full session details", error)
    return baseSummary
  }
}

async function generatePDFReport() {
  if (!summary?.sessionId) {
    alert("No session ID found. Cannot generate PDF report.")
    return
  }
  const button = document.getElementById("pdf-btn")
  const original = button?.innerHTML || "Generate PDF Report"
  try {
    if (button) {
      button.innerHTML = "Generating PDF..."
      button.disabled = true
    }
    const response = await authenticatedFetch(`/generate-pdf/${summary.sessionId}`)
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    const blob = await response.blob()
    const header = response.headers.get("content-disposition") || ""
    const filename = header.match(/filename=\"(.+)\"/)?.[1] || `interview_report_${summary.sessionId}.pdf`
    const url = window.URL.createObjectURL(blob)
    const anchor = document.createElement("a")
    anchor.href = url
    anchor.download = filename
    document.body.appendChild(anchor)
    anchor.click()
    document.body.removeChild(anchor)
    window.URL.revokeObjectURL(url)
    if (button) button.innerHTML = "PDF Downloaded"
  } catch (error) {
    console.error("PDF generation failed:", error)
    if (button) button.innerHTML = "PDF Failed"
  } finally {
    window.setTimeout(() => {
      if (button) {
        button.innerHTML = original
        button.disabled = false
      }
    }, 2000)
  }
}

window.generatePDFReport = generatePDFReport

async function loadTopicRatings(data) {
  if (!isRateable(data)) return
  try {
    const response = await fetch("/api/ratings/topics")
    const result = await response.json()
    if (!result.success) return
    const current = (result.ratings || []).find(entry => entry.topic_id === data.topic)
    if (!current?.rating_count) {
      ratingSummaryPill.textContent = "No ratings yet"
      ratingSummaryPill.dataset.tone = "working"
      return
    }
    ratingSummaryPill.textContent = `${current.average_rating}/5 from ${current.rating_count} ratings`
    ratingSummaryPill.dataset.tone = "success"
  } catch (error) {
    console.error("Failed to load topic ratings", error)
    if (ratingSummaryPill) ratingSummaryPill.dataset.tone = "error"
  }
}

async function submitRating(data, ratingValue) {
  if (!isRateable(data)) return
  const currentUser = getCurrentUser()
  try {
    const response = await authenticatedFetch("/api/ratings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: data.sessionId,
        topic_id: data.topic,
        rating: ratingValue,
        user_id: currentUser?.user_id || null,
      }),
    })
    const result = await response.json()
    if (!result.success) throw new Error(result.error || "Failed to save rating")
    ratingButtons.forEach(button => {
      button.dataset.active = button.dataset.rating === String(ratingValue) ? "true" : "false"
      button.disabled = true
    })
    if (result.summary?.average_rating && result.summary?.rating_count) {
      ratingSummaryPill.textContent = `${result.summary.average_rating}/5 from ${result.summary.rating_count} ratings`
    }
    ratingSummaryPill.dataset.tone = "success"
    ratingHelper.textContent = currentUser
      ? "Thanks. Your rating is now included in the topic average."
      : "Thanks. Your session rating is saved, even though you are currently in guest mode."
  } catch (error) {
    console.error("Rating submission failed", error)
    ratingSummaryPill.dataset.tone = "error"
    ratingHelper.textContent = "We could not save your rating right now. Please try again."
  }
}

function renderResults(data) {
  const metrics = buildMetrics(data)
  const analysis = buildAnalysis(data, metrics)
  const timing = metrics.targetAwareCount ? `${Math.round((metrics.onTargetCount / metrics.targetAwareCount) * 100)}% on target` : "No target timing"

  setText("result-topic", sessionLabel(data))
  setText("result-mode", title(data.sessionMode))
  setText("result-title", `${sessionLabel(data)} Interview Summary`)
  setText("result-subtitle", data.studyStepId
    ? "This round came from your prep path. The results below now matter for both session review and planner progress."
    : data.sessionMode === "role"
      ? `This was a ${data.durationMinutes || 30}-minute role round. Use the breakdown below to see where the round stayed strong and where it slipped.`
      : data.sessionMode === "custom"
        ? `This was a ${data.durationMinutes || 30}-minute custom interview. The report emphasizes timing, structure, delivery, and answer control.`
        : "This report expands the actual round: score shape, question review, pacing, fillers, timing, and stronger analytics.")

  setText("result-score", `${data.finalScore}/100`)
  setText("result-strongest-signal", `${metrics.strongest.label} ${metrics.strongest.value}`)
  setText("result-questions", String(data.questionsTotal || data.questionDetails.length))
  setText("result-consistency", `${metrics.consistency}/100`)
  setText("result-avg-duration", durationLabel(metrics.avgDuration))
  setText("result-pace-control", `${metrics.paceControl}% in range`)
  setText("result-avg-confidence", `${metrics.avgConfidence}/100`)
  setText("result-avg-content", `${metrics.avgContent}/100`)
  setText("result-avg-delivery", `${metrics.avgDelivery}/100`)
  setText("result-avg-wpm", `${metrics.avgWpm} WPM`)
  setText("result-total-fillers", String(metrics.totalFillers))
  setText("result-timing-adherence", timing)
  setText("performance-trends", analysis.performance)
  setText("answer-quality", analysis.quality)
  setText("recommendations", analysis.recommendations)
  setText("result-tips", metrics.avgContent < 65
    ? "Make each answer one layer deeper. Add reasoning, tradeoffs, and a concrete example instead of stopping at the first correct idea."
    : metrics.avgDelivery < 65
      ? "Focus on cleaner openings and endings so the quality of your ideas comes through more strongly."
      : metrics.paceControl < 60
        ? "Your next gain is delivery control. Keep the answer energy, but stay closer to a stable pace band."
        : "The baseline is strong. The next jump comes from making weak questions sound as complete as the best ones.")
  setText("result-duration", `${data.durationMinutes || 30} min planned`)
  setText("result-target-timing", metrics.targetAwareCount ? `${metrics.onTargetCount}/${metrics.targetAwareCount} on target` : "No target timing")
  setText("result-best-question", metrics.bestQuestion ? truncate(textForQuestion(metrics.bestQuestion), 44) : "-")
  setText("result-weakest-question", metrics.weakestQuestion ? truncate(textForQuestion(metrics.weakestQuestion), 44) : "-")

  renderHeroTags(data)
  configurePrepPathReturn(data)
  setPills("result-strengths", analysis.strengths)
  setPills("result-risks", analysis.risks)
  renderQuestionReview(data)
  createCharts(data, metrics)

  if (isRateable(data)) {
    ratingButtons.forEach(button => {
      button.addEventListener("click", () => submitRating(data, Number(button.dataset.rating)), { once: true })
    })
    loadTopicRatings(data)
  } else {
    document.querySelector(".rating-card")?.setAttribute("hidden", "true")
  }
}

async function initializeResults() {
  summary = await loadDetailedSummary()
  if (!summary) {
    renderMissing()
    return
  }
  renderResults(summary)
}

initializeResults()
