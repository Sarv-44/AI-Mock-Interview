// ===============================
// AUDIO RECORDING SYSTEM
// ===============================

import {state} from "./config.js"

const scoreRingConfig = [
{key: "overall", field: "overall_score", fallbackField: "confidence", color: "#5ea2ff"},
{key: "content", field: "content_score", color: "#64e4d3"},
{key: "delivery", field: "delivery_score", fallbackField: "confidence", color: "#27d17f"},
{key: "structure", field: "answer_structure_score", color: "#ffbf5c"},
{key: "correctness", field: "correctness_score", color: "#ff7f73"},
]

function isCustomMode(){
return state.sessionPlan?.mode === "custom"
}

function setNodeText(id, value){
const node = document.getElementById(id)
if(node) node.innerText = value
}

function applyReviewModeCopy(){
if(isCustomMode()){
setNodeText("review-hub-title", "Transcript, delivery review, and timing")
setNodeText("review-tab-transcript-label", "Transcript")
setNodeText("review-tab-correction-label", "Review")
setNodeText("review-tab-reference-label", "Timing")
setNodeText("correction-kicker", "Delivery Review")
setNodeText("correction-title", "How the answer landed")
setNodeText("score-ring-overall-label", "Overall")
setNodeText("score-ring-content-label", "Focus")
setNodeText("score-ring-delivery-label", "Delivery")
setNodeText("score-ring-structure-label", "Structure")
setNodeText("score-ring-correctness-label", "Timing")
setNodeText("strengths-title", "Strong signals")
setNodeText("missing-title", "Adjust next")
setNodeText("sample-answer-title", "Delivery recap")
setNodeText("reference-kicker", "Timing Guide")
setNodeText("reference-title", "Target vs actual")
setNodeText("reference-answer-title", "Timing summary")
setNodeText("reference-explanation-title", "Why this timing readout matters")
setNodeText("improvement-steps-title", "Next timing moves")
return
}

setNodeText("review-hub-title", "Transcript, answer check, and benchmark")
setNodeText("review-tab-transcript-label", "Transcript")
setNodeText("review-tab-correction-label", "Review")
setNodeText("review-tab-reference-label", "Guide")
setNodeText("correction-kicker", "Answer Check")
setNodeText("correction-title", "What the system found")
setNodeText("score-ring-overall-label", "Overall")
setNodeText("score-ring-content-label", "Content")
setNodeText("score-ring-delivery-label", "Delivery")
setNodeText("score-ring-structure-label", "Structure")
setNodeText("score-ring-correctness-label", "Correctness")
setNodeText("strengths-title", "What went well")
setNodeText("missing-title", "Missing or weak points")
setNodeText("sample-answer-title", "Suggested stronger answer")
setNodeText("reference-kicker", "Benchmark Answer")
setNodeText("reference-title", "What a strong answer can sound like")
setNodeText("reference-answer-title", "Benchmark answer")
setNodeText("reference-explanation-title", "Why this answer works")
setNodeText("improvement-steps-title", "Improve next")
}

function setInterviewPhase(phase){
document.body.dataset.interviewPhase = phase
}

export function activateReviewPane(pane){
document.querySelectorAll(".review-tab").forEach(tab => {
tab.classList.toggle("is-active", tab.dataset.reviewPane === pane)
})

document.querySelectorAll(".review-pane").forEach(panel => {
panel.classList.toggle("is-active", panel.id === `review-pane-${pane}`)
})
}

function setControlState({canStart = true, canStop = false, canNext = false} = {}) {
const startBtn = document.querySelector(".start-btn")
const stopBtn = document.querySelector(".stop-btn")
const nextBtn = document.querySelector(".next-btn")
const totalQuestions = state.sessionPlan?.questions?.length || 0
const isLastQuestion = totalQuestions > 0 && state.currentQuestion >= totalQuestions - 1

if(startBtn) startBtn.disabled = !canStart
if(stopBtn) stopBtn.disabled = !canStop
if(nextBtn) nextBtn.disabled = !canNext
if(nextBtn){
nextBtn.innerText = isLastQuestion && canNext ? "View Results" : "Next Question"
}
}

function resetLiveReadout(){
applyReviewModeCopy()
setInterviewPhase("live")
activateReviewPane("transcript")
updateReadout("timer", "00:00")
updateReadout("transcript", "Start recording to capture your answer. Your transcript will appear here once analysis is complete.")
updateReadout("words", "0")
updateReadout("fillers", "0")
updateReadout("duration", "0s")
updateReadout("wpm", "0")
updateReadout("confidence", "0/100")

const transcriptBadge = document.getElementById("transcript-badge")
const responseState = document.getElementById("response-state")
const stageLabel = document.getElementById("stage-label")
const coachTip = document.getElementById("coach-tip")
const analysisSummary = document.getElementById("analysis-summary")
const answerQualityBadge = document.getElementById("answer-quality-badge")
const answerQualitySummary = document.getElementById("answer-quality-summary")
const missingConcepts = document.getElementById("missing-concepts")
const sampleAnswer = document.getElementById("sample-answer")
const idealAnswer = document.getElementById("ideal-answer")
const referenceExplanation = document.getElementById("reference-explanation")
const referenceSourceBadge = document.getElementById("reference-source-badge")

if(transcriptBadge) transcriptBadge.innerText = "Awaiting recording"
if(responseState) responseState.innerText = "Ready to answer"
if(stageLabel) stageLabel.innerText = "Prompt delivered"
if(coachTip) coachTip.innerText = "Aim for a confident opening, deliberate pacing, and a clear finish."
if(analysisSummary) analysisSummary.innerText = isCustomMode()
? "Once you stop recording, the system will score delivery, structure, filler usage, and timing against the target."
: "Once you stop recording, the system will score confidence, pace, duration, and filler usage."
if(answerQualityBadge){
answerQualityBadge.innerText = "Awaiting analysis"
answerQualityBadge.dataset.quality = ""
}
if(answerQualitySummary){
answerQualitySummary.innerText = isCustomMode()
? "Finish one response and the system will show how the answer landed, how well it stayed structured, and how close it was to the target time."
: "Finish one response and the system will show what worked, what was weak, and a stronger version of your answer."
}
renderScoreRings()
renderBulletList("answer-strengths", ["We will highlight the strongest parts of your response here."])
if(missingConcepts) missingConcepts.innerText = isCustomMode() ? "No delivery adjustments yet." : "No missing concepts yet."
if(sampleAnswer) sampleAnswer.innerText = isCustomMode()
? "The system will summarize your delivery and structure here after analysis."
: "The system will build a stronger version of your answer here after analysis."
if(idealAnswer) idealAnswer.innerText = isCustomMode()
? "The target-time summary will appear here after analysis."
: "The fuller benchmark answer will appear here when the system has a grounded reference for this question."
if(referenceExplanation){
referenceExplanation.innerText = isCustomMode()
? "The timing panel will explain how close the answer was to the target and whether the pacing matched the question."
: "The explanation will highlight the structure, technical points, and tradeoffs that make this benchmark answer interview-ready."
}
if(referenceSourceBadge) referenceSourceBadge.innerText = isCustomMode() ? "Timing target" : "Question bank benchmark"
renderBulletList("improvement-steps", [isCustomMode() ? "Your timing and delivery suggestions will appear here after analysis." : "Your next-step suggestions will appear here after analysis."])

setStatus("Waiting for your response", "idle")
setControlState({canStart:true, canStop:false, canNext:false})
}

function setStatus(message, stateName = "idle", allowHtml = false){
const statusEl = document.getElementById("status")
if(!statusEl) return

statusEl.dataset.state = stateName

if(allowHtml){
statusEl.innerHTML = message
return
}

statusEl.innerText = message
}

function updateReadout(id, value){
const el = document.getElementById(id)
if(el) el.innerText = value
}

function clampScore(value){
const parsed = Number(value)
if(Number.isNaN(parsed)) return 0
return Math.max(0, Math.min(100, Math.round(parsed)))
}

function renderScoreRings(data = {}){
scoreRingConfig.forEach(config => {
const score = clampScore(data[config.field] ?? data[config.fallbackField] ?? 0)
const ring = document.getElementById(`score-ring-${config.key}`)
const value = document.getElementById(`score-ring-${config.key}-value`)

if(ring){
ring.style.setProperty("--score-angle", `${(score / 100) * 360}deg`)
ring.style.setProperty("--score-color", config.color)
}

if(value){
value.innerText = String(score)
}
})
}

function renderBulletList(id, items){
const list = document.getElementById(id)
if(!list) return

list.innerHTML = ""

items.forEach(item => {
const li = document.createElement("li")
li.innerText = item
list.appendChild(li)
})
}

function buildReferenceExplanation(data){
if(data.response_validity !== "valid"){
return "The system did not use this as a strong benchmark yet because the response needs a clearer original explanation first."
}

const coveredCount = (data.covered_points || []).length
const missingCount = (data.missing_points || []).length
const incorrectCount = (data.incorrect_points || []).length

const lines = []
if(coveredCount){
lines.push(`You already covered ${coveredCount} key point${coveredCount === 1 ? "" : "s"} from the benchmark answer.`)
}
if(missingCount){
lines.push(`The benchmark answer adds ${missingCount} important point${missingCount === 1 ? "" : "s"} that make the explanation feel more complete.`)
}
if(incorrectCount){
lines.push(`It also avoids ${incorrectCount} accuracy issue${incorrectCount === 1 ? "" : "s"} that weakened the original response.`)
}

return lines.length
? lines.join(" ")
: "This benchmark answer works because it opens directly, covers the core concept cleanly, and closes with the tradeoff or use-case the interviewer expects."
}

function renderAnswerCorrection(data){
if(isCustomMode()){
renderCustomAnalysis(data)
return
}

const answerQualityBadge = document.getElementById("answer-quality-badge")
const answerQualitySummary = document.getElementById("answer-quality-summary")
const missingConcepts = document.getElementById("missing-concepts")
const sampleAnswer = document.getElementById("sample-answer")
const idealAnswer = document.getElementById("ideal-answer")
const referenceExplanation = document.getElementById("reference-explanation")
const referenceSourceBadge = document.getElementById("reference-source-badge")
const needsRetry = data.answer_quality_label === "retry" || data.response_validity !== "valid"

if(answerQualityBadge){
answerQualityBadge.innerText = data.answer_quality_label || "Analyzed"
answerQualityBadge.dataset.quality = data.answer_quality_label || ""
}

if(answerQualitySummary){
answerQualitySummary.innerText = data.correctness_summary || data.answer_quality_summary || "The answer has been analyzed."
}

renderScoreRings(data)

renderBulletList(
"answer-strengths",
(data.covered_points && data.covered_points.length)
? data.covered_points
: (data.strengths && data.strengths.length)
? data.strengths
: ["The system did not find enough original answer content yet."]
)

if(missingConcepts){
if(needsRetry){
missingConcepts.innerText = "Not scored yet because the response needs a clearer original explanation."
}else{
const parts = []
if(data.incorrect_points && data.incorrect_points.length){
parts.push(`Possible inaccuracies: ${data.incorrect_points.join(", ")}`)
}
if(data.missing_points && data.missing_points.length){
parts.push(`Missing points: ${data.missing_points.join(", ")}`)
}
missingConcepts.innerText = parts.length
? parts.join(" ")
: (data.missing_concepts && data.missing_concepts.length)
? data.missing_concepts.join(", ")
: "No major missing concepts were detected."
}
}

if(sampleAnswer){
sampleAnswer.innerText = data.sample_answer || "A suggested stronger answer is not available yet."
}

if(idealAnswer){
idealAnswer.innerText = data.ideal_answer || "A grounded benchmark answer is not available for this question yet."
}

if(referenceExplanation){
referenceExplanation.innerText = buildReferenceExplanation(data)
}

if(referenceSourceBadge){
referenceSourceBadge.innerText = data.reference_source === "database"
? "Question bank benchmark"
: "Generated benchmark"
}

renderBulletList(
"improvement-steps",
(data.improvement_steps && data.improvement_steps.length)
? data.improvement_steps
: ["No specific next-step suggestions are available yet."]
)
}

function buildCustomTimingBadge(data){
if(data.time_target_status === "on_target") return "On target"
if(data.time_target_status === "under") return `${Math.abs(data.time_target_delta_seconds || 0)}s early`
if(data.time_target_status === "over") return `${Math.abs(data.time_target_delta_seconds || 0)}s over`
return "No target"
}

function buildCustomDeliveryRecap(data){
return `You spoke ${data.word_count || 0} words in ${data.duration || 0}s at ${data.wpm || 0} WPM with ${data.filler_words || 0} filler word${data.filler_words === 1 ? "" : "s"}.`
}

function renderCustomAnalysis(data){
const answerQualityBadge = document.getElementById("answer-quality-badge")
const answerQualitySummary = document.getElementById("answer-quality-summary")
const missingConcepts = document.getElementById("missing-concepts")
const sampleAnswer = document.getElementById("sample-answer")
const idealAnswer = document.getElementById("ideal-answer")
const referenceExplanation = document.getElementById("reference-explanation")
const referenceSourceBadge = document.getElementById("reference-source-badge")

if(answerQualityBadge){
answerQualityBadge.innerText = data.answer_quality_label || "Analyzed"
answerQualityBadge.dataset.quality = data.answer_quality_label || ""
}

if(answerQualitySummary){
answerQualitySummary.innerText = data.answer_quality_summary || "The custom answer has been analyzed."
}

renderScoreRings(data)

renderBulletList(
"answer-strengths",
(data.strengths && data.strengths.length)
? data.strengths
: ["The system captured a usable delivery sample from your answer."]
)

if(missingConcepts){
missingConcepts.innerText = (data.improvements && data.improvements.length)
? data.improvements.join(" ")
: "No immediate delivery adjustments were detected."
}

if(sampleAnswer){
sampleAnswer.innerText = buildCustomDeliveryRecap(data)
}

if(idealAnswer){
idealAnswer.innerText = data.time_target_seconds
? `Target ${data.time_target_seconds}s. Actual ${data.duration}s. Status: ${String(data.time_target_status || "not_set").replaceAll("_", " ")}.`
: "No target time was set for this question."
}

if(referenceExplanation){
referenceExplanation.innerText = data.correctness_summary || "Timing feedback will appear here after analysis."
}

if(referenceSourceBadge){
referenceSourceBadge.innerText = buildCustomTimingBadge(data)
}

renderBulletList(
"improvement-steps",
(data.improvement_steps && data.improvement_steps.length)
? data.improvement_steps
: ["Keep the next answer controlled, concise, and close to the target time."]
)
}

function updateCoachInsight(data){
const transcriptBadge = document.getElementById("transcript-badge")
const responseState = document.getElementById("response-state")
const stageLabel = document.getElementById("stage-label")
const coachTip = document.getElementById("coach-tip")
const analysisSummary = document.getElementById("analysis-summary")

if(transcriptBadge) transcriptBadge.innerText = "Transcript captured"
if(responseState) responseState.innerText = state.currentQuestion >= (state.sessionPlan?.questions?.length || 1) - 1 ? "Ready to view results" : "Answer analyzed"
if(stageLabel) stageLabel.innerText = state.currentQuestion >= (state.sessionPlan?.questions?.length || 1) - 1 ? "Interview complete" : "Awaiting next step"

let tip = "Solid baseline. Keep your answer direct and composed."
if(isCustomMode()){
if(data.time_target_status === "over"){
tip = "You went over the target time. Tighten repetition and land the answer earlier."
}else if(data.time_target_status === "under"){
tip = "You finished early. Add one more supporting detail so the answer feels fuller."
}else if(data.filler_words > 6){
tip = "Filler usage is climbing. Replace verbal fillers with short pauses."
}else if(data.wpm > 170){
tip = "You are moving fast. Slow down slightly so the answer sounds more deliberate."
}else if(data.answer_structure_score < 55){
tip = "The structure is loose. Open with the answer, then move through one or two clean points."
}
}else if(data.answer_quality_label === "retry" || data.response_validity !== "valid"){
tip = data.response_validity_reason || "That response needs a clearer original explanation. Try again with a direct answer in your own words."
}else if((data.content_score || 0) < 55){
tip = "The answer needs stronger concept coverage. State the core idea first, then support it with the right technical terms."
}else if(data.confidence < 60){
tip = "Confidence is reading low. Slow down, open with the answer, and avoid apologetic phrasing."
}else if(data.filler_words > 6){
tip = "Filler usage is climbing. Replace verbal fillers with short pauses between ideas."
}else if(data.wpm > 170){
tip = "You are moving fast. Add a breath between points so the answer sounds more deliberate."
}else if(data.wpm < 110){
tip = "The pacing is a bit slow. Try shorter sentences and a stronger opening statement."
}

if(coachTip) coachTip.innerText = tip

if(analysisSummary){
if(isCustomMode()){
analysisSummary.innerText =
`Latest answer: ${data.overall_score || data.confidence}/100 overall, ${data.content_score || 0}/100 focus, ${data.delivery_score || data.confidence}/100 delivery, ${data.answer_structure_score || 0}/100 structure, and ${data.correctness_score || 0}/100 timing.`
}else if(data.answer_quality_label === "retry" || data.response_validity !== "valid"){
analysisSummary.innerText =
`${data.response_validity_reason || "This response should be retried with a direct explanation in your own words."}`
}else{
analysisSummary.innerText =
`Latest answer: ${data.overall_score || data.confidence}/100 overall, ${data.correctness_score || 0}/100 correctness, ${data.content_score || 0}/100 content, ${data.delivery_score || data.confidence}/100 delivery, and a ${String(data.correctness_verdict || "reviewed").replaceAll("_", " ")} verdict.`
}
}
}

export async function startRecording(){

if(state.isRecording || state.isProcessing) return

if(!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia){
alert("This browser does not support microphone recording over this connection. Try using Chrome on desktop.")
return
}

try{

const stream = await navigator.mediaDevices.getUserMedia({audio:true})

// create recorder and wire events BEFORE starting
state.recorder = new MediaRecorder(stream)
state.audioChunks = []

state.recorder.ondataavailable = e => state.audioChunks.push(e.data)

state.recorder.onstop = async () => {

if(!state.audioChunks.length){
state.isProcessing = false
state.currentQuestionAnalyzed = false
setStatus("No audio captured", "error")
setControlState({canStart:true, canStop:false, canNext:false})
return
}

const blob = new Blob(state.audioChunks,{type:"audio/webm"})
const formData = new FormData()
const activeQuestion = state.sessionPlan?.questions?.[state.currentQuestion] || {}
formData.append("file", blob, "answer.webm")
formData.append("difficulty", state.currentDifficulty || "medium")
formData.append("topic", activeQuestion.topic_id || state.sessionPlan?.primary_topic_id || localStorage.getItem("selectedTopic") || "")
formData.append("question", activeQuestion.q || document.getElementById("question")?.innerText || "")
formData.append("sample_answer", activeQuestion.sample_answer || "")
formData.append("ideal_answer", activeQuestion.ideal_answer || "")
formData.append("analytics_mode", state.sessionPlan?.analytics_mode || "full")
formData.append("target_seconds", String(activeQuestion.target_seconds || 0))
formData.append("question_weight", String(activeQuestion.weight || 0))

try{

const res = await fetch("/transcribe",{
method:"POST",
body:formData
})

const data = await res.json()

if(data.error){
throw new Error(data.error)
}

updateReadout("transcript", data.transcript)
updateReadout("words", data.word_count)
updateReadout("fillers", data.filler_words)
updateReadout("duration", data.duration + "s")
updateReadout("wpm", data.wpm)
const answerScore = data.overall_score || data.confidence
updateReadout("confidence", answerScore + "/100")

state.confidenceHistory[state.currentQuestion] = answerScore
state.wpmHistory[state.currentQuestion] = data.wpm
state.fillerHistory[state.currentQuestion] = data.filler_words
state.fillerListHistory[state.currentQuestion] = data.filler_list || []
state.durations[state.currentQuestion] = data.duration
state.transcripts[state.currentQuestion] = data.transcript
state.contentScoreHistory[state.currentQuestion] = data.content_score || 0
state.deliveryScoreHistory[state.currentQuestion] = data.delivery_score || answerScore
state.answerFeedbackHistory[state.currentQuestion] = {
overall_score: answerScore,
content_score: data.content_score || 0,
delivery_score: data.delivery_score || answerScore,
keyword_coverage: data.keyword_coverage || 0,
answer_structure_score: data.answer_structure_score || 0,
technical_depth: data.technical_depth || 0,
matched_keywords: data.matched_keywords || [],
covered_answer_elements: data.covered_answer_elements || [],
strengths: data.strengths || [],
improvements: data.improvements || [],
response_validity: data.response_validity || "valid",
response_validity_reason: data.response_validity_reason || "",
answer_quality_label: data.answer_quality_label || "",
answer_quality_summary: data.answer_quality_summary || "",
correctness_score: data.correctness_score || 0,
correctness_verdict: data.correctness_verdict || "",
correctness_summary: data.correctness_summary || "",
covered_points: data.covered_points || [],
missing_points: data.missing_points || [],
incorrect_points: data.incorrect_points || [],
improvement_steps: data.improvement_steps || [],
missing_concepts: data.missing_concepts || [],
sample_answer: data.sample_answer || "",
ideal_answer: data.ideal_answer || "",
question_type: data.question_type || "",
language_mode: data.language_mode || "english",
language_feedback: data.language_feedback || "",
reference_source: data.reference_source || "generated"
,
analytics_mode: data.analytics_mode || "full",
time_target_seconds: data.time_target_seconds || 0,
time_target_delta_seconds: data.time_target_delta_seconds || 0,
time_target_status: data.time_target_status || "not_set",
time_target_score: data.time_target_score || 0
}

state.currentQuestionAnalyzed = true
state.isProcessing = false

state.weightedScore += answerScore * data.weight
state.totalWeight += data.weight

setStatus("Analysis updated", "idle")
setInterviewPhase("review")
updateCoachInsight(data)
renderAnswerCorrection(data)
activateReviewPane(isCustomMode() ? "correction" : (data.response_validity === "valid" ? "correction" : "transcript"))
setControlState({canStart:true, canStop:false, canNext:true})

}catch(err){

console.error(err)
state.isProcessing = false
state.currentQuestionAnalyzed = false
setStatus("Error analyzing audio", "error")
setControlState({canStart:true, canStop:false, canNext:false})

}

}

state.recorder.start()
state.isRecording = true
state.isProcessing = false
state.currentQuestionAnalyzed = false
setInterviewPhase("recording")

state.seconds = 0
document.getElementById("timer").innerText = "00:00"
const transcriptBadge = document.getElementById("transcript-badge")
const responseState = document.getElementById("response-state")
const stageLabel = document.getElementById("stage-label")

if(transcriptBadge) transcriptBadge.innerText = "Recording in progress"
if(responseState) responseState.innerText = "Listening now"
if(stageLabel) stageLabel.innerText = "Candidate answering"

state.timerInterval = setInterval(()=>{

state.seconds++

const m = String(Math.floor(state.seconds/60)).padStart(2,"0")
const s = String(state.seconds%60).padStart(2,"0")

document.getElementById("timer").innerText = `${m}:${s}`

},1000)

setStatus('<span class="recording-dot"></span> Recording...', "recording", true)
setControlState({canStart:false, canStop:true, canNext:false})

}
catch(err){

console.error("startRecording error", err.name, err.message)
setStatus(
"Unable to access microphone. Please check browser permissions and try again.",
"error"
)
setControlState({canStart:true, canStop:false, canNext:false})

}

}


export function stopRecording(){

if(!state.isRecording || !state.recorder) return

state.isRecording = false
state.isProcessing = true
clearInterval(state.timerInterval)
setInterviewPhase("processing")
setStatus("Analyzing your answer. First run can take a little longer on CPU.", "processing")

const transcriptBadge = document.getElementById("transcript-badge")
const responseState = document.getElementById("response-state")
const stageLabel = document.getElementById("stage-label")

if(transcriptBadge) transcriptBadge.innerText = "Processing answer"
if(responseState) responseState.innerText = "Analyzing response"
if(stageLabel) stageLabel.innerText = "Scoring answer"

state.recorder.stop()
setControlState({canStart:false, canStop:false, canNext:false})

}

export { resetLiveReadout, setControlState }
