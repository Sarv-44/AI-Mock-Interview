// ===============================
// GLOBAL CONFIGURATION (MUTABLE STATE OBJECT)
// ===============================
//
export const state = {
  recorder: null,
  audioChunks: [],
  timerInterval: null,
  seconds: 0,
  isRecording: false,
  isProcessing: false,
  currentQuestionAnalyzed: false,
  currentQuestion: 0,
  currentDifficulty: "medium",
  sessionPlan: null,
  plannedWeight: 0,
  // scoring variables
  weightedScore: 0,
  totalWeight: 0,
  // analytics history
  confidenceHistory: [],
  wpmHistory: [],
  fillerHistory: [],
  fillerListHistory: [],
  durations: [],
  transcripts: [],
  questionConfidence: [],
  contentScoreHistory: [],
  deliveryScoreHistory: [],
  answerFeedbackHistory: []
}
//
// difficulty weights
export const weights = {
  easy: 18,
  medium: 25,
  hard: 32
}

