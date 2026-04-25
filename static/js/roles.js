import {
  createRoleCard,
  loadInterviewCatalog,
  startRoleInterview,
} from "./catalog.js"

const roleGrid = document.getElementById("role-grid")
const roleSummaryEl = document.getElementById("role-summary")
const roleDurationSelect = document.getElementById("role-duration-select")
const spotlightTitle = document.getElementById("spotlight-title")
const spotlightDescription = document.getElementById("spotlight-description")
const spotlightDuration = document.getElementById("spotlight-duration")
const spotlightFocus = document.getElementById("spotlight-focus")
const spotlightStartButton = document.getElementById("spotlight-start-btn")
const rolesRoleCount = document.getElementById("roles-role-count")
const rolesDurationDisplay = document.getElementById("roles-duration-display")

let roleCatalog = []

function attachRoleActions() {
  roleGrid.querySelectorAll("[data-role-id]").forEach(button => {
    button.addEventListener("click", () => {
      startRoleInterview(button.dataset.roleId, Number(roleDurationSelect?.value || 30))
    })
  })
}

function getRecommendedRole() {
  if (!roleCatalog.length) return null

  const duration = Number(roleDurationSelect?.value || 30)
  const exactMatch = roleCatalog.find(role => (role.available_durations || []).includes(duration))
  return exactMatch || roleCatalog[0]
}

function renderRoleSpotlight() {
  const recommendedRole = getRecommendedRole()
  const selectedDuration = Number(roleDurationSelect?.value || 30)

  if (rolesDurationDisplay) {
    rolesDurationDisplay.innerText = `${selectedDuration} minute round`
  }

  if (!recommendedRole) {
    if (spotlightTitle) spotlightTitle.innerText = "No recommended lane yet"
    if (spotlightDescription) spotlightDescription.innerText = "Once the backend catalog loads, we will highlight a role round here."
    if (spotlightDuration) spotlightDuration.innerText = `${selectedDuration} min flow`
    if (spotlightFocus) spotlightFocus.innerText = "Catalog loading"
    if (spotlightStartButton) {
      spotlightStartButton.disabled = true
      spotlightStartButton.onclick = null
    }
    return
  }

  if (spotlightTitle) spotlightTitle.innerText = recommendedRole.title
  if (spotlightDescription) {
    spotlightDescription.innerText = `${recommendedRole.description} This lane fits a ${selectedDuration}-minute round and emphasizes ${(recommendedRole.focus_topics || []).slice(0, 3).map(topic => topic.title).join(", ")}.`
  }
  if (spotlightDuration) spotlightDuration.innerText = `${selectedDuration} min flow`
  if (spotlightFocus) {
    spotlightFocus.innerText = `${(recommendedRole.focus_topics || []).slice(0, 2).map(topic => topic.title).join(" + ")}`
  }
  if (spotlightStartButton) {
    spotlightStartButton.disabled = false
    spotlightStartButton.onclick = () => startRoleInterview(recommendedRole.role_id, selectedDuration)
  }
}

function renderRoles() {
  if (!roleCatalog.length) {
    if (roleSummaryEl) {
      roleSummaryEl.innerText = "Role lanes unavailable right now"
    }

    roleGrid.innerHTML = `
      <div class="topic-empty-state">
        <h4>No role tracks available</h4>
        <p>The backend catalog did not return any role-wise interview lanes yet. Refresh once after the server finishes loading.</p>
      </div>
    `

    renderRoleSpotlight()
    return
  }

  roleGrid.innerHTML = roleCatalog.map(createRoleCard).join("")
  attachRoleActions()
  renderRoleSpotlight()

  if (roleSummaryEl) {
    roleSummaryEl.innerText = `${roleCatalog.length} role-based interview lanes ready`
  }

  if (rolesRoleCount) {
    rolesRoleCount.innerText = `${roleCatalog.length} role rounds`
  }
}

async function loadRolesPage() {
  try {
    const { roles } = await loadInterviewCatalog()
    roleCatalog = roles
    renderRoles()
  } catch (error) {
    console.error("Failed to load roles page", error)

    roleGrid.innerHTML = `
      <div class="topic-empty-state">
        <h4>Role interviews unavailable</h4>
        <p>The backend role catalog could not be loaded right now.</p>
      </div>
    `

    if (roleSummaryEl) {
      roleSummaryEl.innerText = "Catalog unavailable"
    }
  }
}

if (roleDurationSelect) {
  roleDurationSelect.addEventListener("change", () => {
    renderRoleSpotlight()
  })
}

loadRolesPage()
