const STORAGE_KEY = "ui-theme-preference"
const DEFAULT_THEME = "nebula"

const THEMES = [
  {
    id: "nebula",
    title: "Nebula",
    copy: "Cool editorial blue with clean glass contrast.",
    swatches: ["#8bbcff", "#73e0d1", "#f1b27f"]
  },
  {
    id: "aurora",
    title: "Aurora",
    copy: "Bright cyan and mint with a futuristic glow.",
    swatches: ["#7dc8ff", "#6cf0d0", "#a6a4ff"]
  },
  {
    id: "sunset",
    title: "Sunset",
    copy: "Warm pink-orange gradients with a softer dramatic feel.",
    swatches: ["#ff8f72", "#ffc46c", "#ff79af"]
  },
  {
    id: "ember",
    title: "Ember",
    copy: "Deep burnt tones with stronger warmth and contrast.",
    swatches: ["#ff865c", "#ffb45e", "#ffd872"]
  }
]

let cleanupThemeMenu = null

function ensureThemeSlot() {
  const existingSlot = document.getElementById("theme-menu-slot")
  if (existingSlot) return existingSlot
  return null
}

function getSavedTheme() {
  const savedTheme = localStorage.getItem(STORAGE_KEY)
  return THEMES.some(theme => theme.id === savedTheme) ? savedTheme : DEFAULT_THEME
}

function createSwatchMarkup(swatches) {
  return `
    <div class="ui-theme-swatch" aria-hidden="true">
      ${swatches.map(color => `<i style="background:${color}"></i>`).join("")}
    </div>
  `
}

function applyTheme(themeId) {
  const activeTheme = THEMES.find(theme => theme.id === themeId) || THEMES[0]
  document.body.dataset.uiTheme = activeTheme.id
  document.documentElement.dataset.uiTheme = activeTheme.id
  localStorage.setItem(STORAGE_KEY, activeTheme.id)
  document.querySelectorAll(".ui-theme-option").forEach(button => {
    const isActive = button.dataset.theme === activeTheme.id
    button.classList.toggle("is-active", isActive)
    button.setAttribute("aria-pressed", isActive ? "true" : "false")
    const tag = button.querySelector(".ui-theme-option-tag")
    if (tag) {
      tag.textContent = isActive ? "Active" : "Theme"
    }
  })

  const triggerLabel = document.querySelector("#ui-theme-menu-trigger strong")
  const triggerNote = document.querySelector("#ui-theme-menu-trigger .ui-theme-menu-trigger-label")
  const triggerSwatch = document.querySelector("#ui-theme-menu-trigger .ui-theme-swatch")
  const activeTitle = document.getElementById("ui-theme-menu-active-title")
  if (triggerLabel) {
    triggerLabel.textContent = activeTheme.title
  }
  if (triggerNote) {
    triggerNote.textContent = "UI theme"
  }
  if (triggerSwatch) {
    triggerSwatch.innerHTML = activeTheme.swatches.map(color => `<i style="background:${color}"></i>`).join("")
  }
  if (activeTitle) {
    activeTitle.textContent = activeTheme.title
  }
}

function closeThemeMenu() {
  const trigger = document.getElementById("ui-theme-menu-trigger")
  const dropdown = document.getElementById("ui-theme-menu-dropdown")

  if (!trigger || !dropdown) return

  trigger.setAttribute("aria-expanded", "false")
  dropdown.hidden = true
}

function setupThemeMenu(root) {
  const trigger = document.getElementById("ui-theme-menu-trigger")
  const dropdown = document.getElementById("ui-theme-menu-dropdown")

  if (!root || !trigger || !dropdown) return

  closeThemeMenu()

  const onDocumentClick = (event) => {
    if (!root.contains(event.target)) {
      closeThemeMenu()
    }
  }

  const onEscape = (event) => {
    if (event.key === "Escape") {
      closeThemeMenu()
    }
  }

  trigger.addEventListener("click", (event) => {
    event.preventDefault()
    const nextState = trigger.getAttribute("aria-expanded") !== "true"
    trigger.setAttribute("aria-expanded", String(nextState))
    dropdown.hidden = !nextState
  })

  dropdown.querySelectorAll(".ui-theme-option").forEach(button => {
    button.addEventListener("click", () => {
      applyTheme(button.dataset.theme || DEFAULT_THEME)
      closeThemeMenu()
    })
  })

  document.addEventListener("click", onDocumentClick)
  document.addEventListener("keydown", onEscape)

  cleanupThemeMenu = () => {
    document.removeEventListener("click", onDocumentClick)
    document.removeEventListener("keydown", onEscape)
  }
}

function mountThemeMenu() {
  const slot = ensureThemeSlot()
  if (!slot) return

  if (typeof cleanupThemeMenu === "function") {
    cleanupThemeMenu()
    cleanupThemeMenu = null
  }

  const currentTheme = getSavedTheme()
  const activeTheme = THEMES.find(theme => theme.id === currentTheme) || THEMES[0]

  slot.innerHTML = `
    <div class="ui-theme-menu" id="ui-theme-menu-root">
      <button
        type="button"
        class="secondary-action appbar-link ui-theme-menu-trigger"
        id="ui-theme-menu-trigger"
        aria-haspopup="menu"
        aria-expanded="false"
      >
        <span class="ui-theme-menu-trigger-chip">
          <span class="ui-theme-menu-trigger-copy">
            <span class="ui-theme-menu-trigger-label">UI Theme</span>
            <strong>${activeTheme.title}</strong>
          </span>
          ${createSwatchMarkup(activeTheme.swatches)}
        </span>
      </button>
      <div class="ui-theme-menu-dropdown" id="ui-theme-menu-dropdown" role="menu" hidden>
        <div class="ui-theme-menu-head">
          <div class="ui-theme-menu-badge">
            <p class="section-kicker">UI Theme</p>
            <strong id="ui-theme-menu-active-title">${activeTheme.title}</strong>
          </div>
          <p class="ui-theme-menu-copy">Apply a richer color atmosphere across the app and keep the whole workspace visually aligned.</p>
        </div>
        <div class="ui-theme-grid">
          ${THEMES.map(theme => `
            <button type="button" class="ui-theme-option" data-theme="${theme.id}" aria-pressed="false">
              <span class="ui-theme-option-header">
                <strong>${theme.title}</strong>
                <span class="ui-theme-option-tag">${theme.id === activeTheme.id ? "Active" : "Theme"}</span>
              </span>
              <span>${theme.copy}</span>
              ${createSwatchMarkup(theme.swatches)}
            </button>
          `).join("")}
        </div>
      </div>
    </div>
  `

  setupThemeMenu(document.getElementById("ui-theme-menu-root"))
  applyTheme(currentTheme)
}

const initialTheme = getSavedTheme()
document.body.dataset.uiTheme = initialTheme
document.documentElement.dataset.uiTheme = initialTheme
applyTheme(initialTheme)
mountThemeMenu()
window.addEventListener("mock-appbar-rendered", mountThemeMenu)
