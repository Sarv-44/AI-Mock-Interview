// ===============================
// AI VOICE SYSTEM
// ===============================

export function speak(text){

window.speechSynthesis.cancel()

const speech = new SpeechSynthesisUtterance(text)

// smoother voice settings
speech.rate = 0.9
speech.pitch = 1
speech.volume = 1

// choose best available voice
const voices = speechSynthesis.getVoices()

const preferred = voices.find(v =>
v.name.includes("Google") ||
v.name.includes("Natural") ||
v.name.includes("Microsoft")
)

if(preferred) speech.voice = preferred

document.getElementById("status").innerText="AI reading question..."

speechSynthesis.speak(speech)

speech.onend = () => {
document.getElementById("status").innerText=""
}

}