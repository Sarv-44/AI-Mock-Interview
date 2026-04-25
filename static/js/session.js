const PRIMARY_STORAGE_KEY = "mockInterviewCurrentUser";
const AUTH_TOKEN_STORAGE_KEY = "mockInterviewAuthToken";
const ADMIN_ACCESS_STORAGE_KEY = "mockInterviewAdminAccess";
const LEGACY_STORAGE_KEYS = [
    PRIMARY_STORAGE_KEY,
    "interviewCurrentUser",
    "currentUser",
    "user"
];

function parseUser(rawValue) {
    if (!rawValue) {
        return null;
    }

    try {
        const parsed = JSON.parse(rawValue);
        if (parsed && typeof parsed === "object") {
            return parsed;
        }
    } catch (error) {
        return null;
    }

    return null;
}

function readStoredToken() {
    return localStorage.getItem(AUTH_TOKEN_STORAGE_KEY) || localStorage.getItem("authToken");
}

let adminAccessRequest = null;

function ensureHeaderStyles() {
    if (document.getElementById("shared-account-menu-styles")) {
        return;
    }

    const style = document.createElement("style");
    style.id = "shared-account-menu-styles";
    style.textContent = `
        .platform-appbar {
            padding: clamp(0.55rem, 1.2vw, 0.9rem) 0;
            border-bottom: 1px solid rgba(126, 147, 172, 0.14);
        }

        .platform-appbar .appbar-inner {
            width: min(1280px, calc(100vw - clamp(1.5rem, 5vw, 3.5rem)));
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: clamp(0.75rem, 1.4vw, 1rem);
            flex-wrap: wrap;
        }

        .platform-appbar .appbar-brand {
            display: flex;
            align-items: center;
            gap: clamp(0.7rem, 1.2vw, 1rem);
            flex: 1 1 24rem;
            min-width: 0;
        }

        .platform-appbar .appbar-brand-copy {
            min-width: 0;
        }

        .platform-appbar .appbar-controls {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: clamp(0.6rem, 1vw, 0.8rem);
            flex: 0 1 auto;
            min-width: 0;
        }

        .platform-appbar .appbar-actions {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: clamp(0.6rem, 1vw, 0.8rem);
        }

        .appbar-ghost-link {
            min-height: clamp(2.5rem, 4.8vw, 2.85rem);
            padding: clamp(0.55rem, 0.9vw, 0.7rem) clamp(0.8rem, 1.2vw, 1rem);
            border-radius: clamp(0.8rem, 1.4vw, 1rem);
        }

        .profile-menu {
            position: relative;
        }

        .account-menu-trigger {
            display: inline-flex;
            align-items: center;
            gap: clamp(0.55rem, 1vw, 0.75rem);
            min-height: clamp(2.75rem, 5vw, 3.15rem);
            min-width: clamp(9.5rem, 16vw, 12rem);
            padding: clamp(0.45rem, 0.8vw, 0.62rem) clamp(0.7rem, 1.1vw, 0.9rem);
            border-radius: clamp(0.9rem, 1.4vw, 1.1rem);
            text-align: left;
            background: var(--panel-glass-soft);
            border: 1px solid var(--panel-border);
            box-shadow: 0 14px 30px rgba(2, 8, 18, 0.18);
        }

        .account-menu-avatar {
            width: clamp(2rem, 3vw, 2.3rem);
            height: clamp(2rem, 3vw, 2.3rem);
            border-radius: clamp(0.7rem, 1vw, 0.85rem);
            display: grid;
            place-items: center;
            flex: 0 0 auto;
            background: linear-gradient(135deg, var(--button-primary-start), var(--button-primary-mid) 56%, var(--button-primary-end));
            color: #07131f;
            font-size: clamp(1rem, 1.5vw, 1.1rem);
            font-weight: 800;
            box-shadow: 0 16px 36px rgba(var(--ambient-primary), 0.18);
        }

        .account-menu-copy {
            display: grid;
            gap: 0.12rem;
            min-width: 0;
        }

        .account-menu-label {
            margin: 0;
            color: var(--text-muted);
            font-size: clamp(0.62rem, 0.8vw, 0.68rem);
            font-weight: 700;
            letter-spacing: 0.18em;
            text-transform: uppercase;
        }

        .account-menu-copy strong {
            color: var(--text-strong);
            font-size: clamp(0.86rem, 1vw, 0.94rem);
            font-weight: 800;
            line-height: 1.2;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .profile-menu-dropdown {
            position: absolute;
            top: calc(100% + 0.5rem);
            right: 0;
            min-width: clamp(11rem, 16vw, 13rem);
            padding: 0.45rem;
            border-radius: 1rem;
            border: 1px solid rgba(var(--ambient-primary), 0.16);
            background:
                radial-gradient(circle at top left, rgba(var(--ambient-primary), 0.18), transparent 28%),
                linear-gradient(180deg, rgba(8, 16, 29, 0.98), rgba(7, 13, 24, 0.96));
            box-shadow: var(--theme-shadow-strong);
            z-index: 40;
        }

        .profile-menu-dropdown[hidden] {
            display: none !important;
        }

        .profile-menu-dropdown a,
        .profile-menu-dropdown button {
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            padding: 0.72rem 0.85rem;
            border: 0;
            border-radius: 0.82rem;
            background: transparent;
            color: var(--text-strong);
            font: inherit;
            font-weight: 700;
            text-decoration: none;
            cursor: pointer;
            transition: background 0.2s ease, color 0.2s ease;
        }

        .profile-menu-dropdown a:hover,
        .profile-menu-dropdown button:hover {
            background: rgba(var(--ambient-primary), 0.14);
            color: #ffffff;
        }

        .profile-menu-dropdown button {
            color: #ffb8b0;
        }

        .profile-menu-dropdown button:hover {
            background: rgba(255, 99, 99, 0.12);
            color: #ffd0ca;
        }

        .platform-appbar .hero-stat-grid,
        .platform-appbar .appbar-meta,
        .platform-appbar .appbar-summary-grid {
            display: none !important;
        }

        @media (max-width: 900px) {
            .platform-appbar .appbar-inner {
                align-items: flex-start;
            }

            .platform-appbar .appbar-controls,
            .platform-appbar .appbar-actions {
                width: 100%;
                justify-content: flex-start;
            }

            .account-menu-trigger {
                min-width: 0;
                width: 100%;
            }

            .profile-menu {
                width: 100%;
            }

            .profile-menu-dropdown {
                left: 0;
                right: auto;
                width: min(20rem, 100%);
            }
        }

    `;

    document.head.appendChild(style);
}

function readStoredUser() {
    for (const key of LEGACY_STORAGE_KEYS) {
        const parsed = parseUser(localStorage.getItem(key));
        if (parsed?.user_id || parsed?.username || parsed?.email) {
            if (key !== PRIMARY_STORAGE_KEY) {
                localStorage.setItem(PRIMARY_STORAGE_KEY, JSON.stringify(parsed));
            }
            return parsed;
        }
    }

    return null;
}

function getAccountInitial(user) {
    const value = user?.username || user?.email || "G";
    return value.trim().charAt(0).toUpperCase();
}

function closeProfileMenu() {
    const trigger = document.getElementById("profile-menu-trigger");
    const dropdown = document.getElementById("profile-menu-dropdown");

    if (!trigger || !dropdown) {
        return;
    }

    trigger.setAttribute("aria-expanded", "false");
    dropdown.hidden = true;
}

function removeQuickNav() {
    const existing = document.getElementById("quick-nav-root");
    if (existing) {
        existing.remove();
    }
}

function setupProfileMenu() {
    const root = document.getElementById("profile-menu-root");
    const trigger = document.getElementById("profile-menu-trigger");
    const dropdown = document.getElementById("profile-menu-dropdown");

    if (!root || !trigger || !dropdown) {
        return;
    }

    closeProfileMenu();

    const onDocumentClick = (event) => {
        if (!root.contains(event.target)) {
            closeProfileMenu();
        }
    };

    const onEscape = (event) => {
        if (event.key === "Escape") {
            closeProfileMenu();
        }
    };

    trigger.addEventListener("click", (event) => {
        event.preventDefault();
        const nextState = trigger.getAttribute("aria-expanded") !== "true";
        trigger.setAttribute("aria-expanded", String(nextState));
        dropdown.hidden = !nextState;
    });

    document.addEventListener("click", onDocumentClick);
    document.addEventListener("keydown", onEscape);

    window.__profileMenuCleanup = () => {
        document.removeEventListener("click", onDocumentClick);
        document.removeEventListener("keydown", onEscape);
    };
}

export function getCurrentUser() {
    const currentUser = readStoredUser();
    if (currentUser?.user_id && !getAuthToken()) {
        return null;
    }

    return currentUser;
}

export function getAuthToken() {
    return readStoredToken() || null;
}

export function getAuthHeaders(existingHeaders = {}) {
    const token = getAuthToken();
    if (!token) {
        return existingHeaders;
    }

    return {
        ...existingHeaders,
        Authorization: `Bearer ${token}`
    };
}

export function authenticatedFetch(url, options = {}) {
    return fetch(url, {
        ...options,
        headers: getAuthHeaders(options.headers || {})
    }).then((response) => {
        if (response.status === 401 && getAuthToken()) {
            clearCurrentUser();
            window.dispatchEvent(new CustomEvent("mock-auth-expired"));
        }

        return response;
    });
}

export async function getAdminAccess(forceRefresh = false) {
    const currentUser = getCurrentUser();
    if (!currentUser?.user_id || !getAuthToken()) {
        sessionStorage.removeItem(ADMIN_ACCESS_STORAGE_KEY);
        return false;
    }

    if (!forceRefresh) {
        const cachedValue = sessionStorage.getItem(ADMIN_ACCESS_STORAGE_KEY);
        if (cachedValue === "true") {
            return true;
        }
        if (cachedValue === "false") {
            return false;
        }
    }

    if (!forceRefresh && adminAccessRequest) {
        return adminAccessRequest;
    }

    adminAccessRequest = authenticatedFetch("/api/admin/access")
        .then(async (response) => {
            if (!response.ok) {
                sessionStorage.setItem(ADMIN_ACCESS_STORAGE_KEY, "false");
                return false;
            }

            const result = await response.json();
            const isAdmin = Boolean(result?.success && result?.is_admin);
            sessionStorage.setItem(ADMIN_ACCESS_STORAGE_KEY, String(isAdmin));
            return isAdmin;
        })
        .catch(() => {
            sessionStorage.setItem(ADMIN_ACCESS_STORAGE_KEY, "false");
            return false;
        })
        .finally(() => {
            adminAccessRequest = null;
        });

    return adminAccessRequest;
}

export function setCurrentUser(user, token = null) {
    if (!user) {
        clearCurrentUser();
        return;
    }

    sessionStorage.removeItem(ADMIN_ACCESS_STORAGE_KEY);
    adminAccessRequest = null;
    localStorage.setItem(PRIMARY_STORAGE_KEY, JSON.stringify(user));

    const resolvedToken = token || user?.token || user?.auth_token || null;
    if (resolvedToken) {
        localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, resolvedToken);
    } else {
        localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
    }
}

export function clearCurrentUser() {
    LEGACY_STORAGE_KEYS.forEach((key) => localStorage.removeItem(key));
    localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
    localStorage.removeItem("authToken");
    sessionStorage.removeItem(ADMIN_ACCESS_STORAGE_KEY);
    adminAccessRequest = null;
}

export function renderAppbarAccount() {
    ensureHeaderStyles();

    const container = document.getElementById("account-actions");
    if (!container) {
        return;
    }

    if (typeof window.__profileMenuCleanup === "function") {
        window.__profileMenuCleanup();
        window.__profileMenuCleanup = null;
    }

    const currentUser = getCurrentUser();

    if (!currentUser) {
        if (document.body.classList.contains("auth-page")) {
            container.innerHTML = `
                <a class="secondary-action appbar-link appbar-ghost-link" href="/">Back home</a>
            `;
            window.dispatchEvent(new CustomEvent("mock-appbar-rendered"));
            return;
        }

        container.innerHTML = `
            <a class="secondary-action appbar-link appbar-ghost-link" href="/auth">Sign in</a>
        `;
        window.dispatchEvent(new CustomEvent("mock-appbar-rendered"));
        return;
    }

    const safeUsername = currentUser.username || "Profile";
    const profileLabel = currentUser.user_id ? "/profile" : "/auth";

    container.innerHTML = `
        <div class="profile-menu" id="profile-menu-root">
            <button
                type="button"
                id="profile-menu-trigger"
                class="secondary-action appbar-link account-menu-trigger"
                aria-haspopup="menu"
                aria-expanded="false"
            >
                <span class="account-menu-avatar">${getAccountInitial(currentUser)}</span>
                <span class="account-menu-copy">
                    <span class="account-menu-label">Account</span>
                    <strong>${safeUsername}</strong>
                </span>
            </button>

            <div class="profile-menu-dropdown" id="profile-menu-dropdown" role="menu" hidden>
                <a href="${profileLabel}" role="menuitem">View profile</a>
                <a href="/leaderboards" role="menuitem">Leaderboards</a>
                <button type="button" id="header-logout-btn" role="menuitem">Sign out</button>
            </div>
        </div>
    `;

    setupProfileMenu();

    const logoutButton = document.getElementById("header-logout-btn");
    if (logoutButton) {
        logoutButton.addEventListener("click", () => {
            clearCurrentUser();
            closeProfileMenu();
            window.location.href = "/auth";
        });
    }

    getAdminAccess(true).then((isAdmin) => {
        if (!isAdmin) {
            return;
        }

        const dropdown = document.getElementById("profile-menu-dropdown");
        if (!dropdown || dropdown.querySelector("[data-admin-link]")) {
            return;
        }

        const adminLink = document.createElement("a");
        adminLink.href = "/admin";
        adminLink.role = "menuitem";
        adminLink.dataset.adminLink = "true";
        adminLink.textContent = "Admin panel";
        dropdown.insertBefore(adminLink, dropdown.lastElementChild || null);
    });

    window.dispatchEvent(new CustomEvent("mock-appbar-rendered"));
}

export function updateAuthCtas() {
    const currentUser = getCurrentUser();
    document.querySelectorAll("[data-auth-cta]").forEach((node) => {
        if (!currentUser) {
            node.textContent = "Sign in / Sign up";
            node.setAttribute("href", "/auth");
            node.hidden = false;
            return;
        }

        node.textContent = "View profile";
        node.setAttribute("href", "/profile");
        node.hidden = false;
    });
}

export function updateAdminCtas() {
    const currentUser = getCurrentUser();
    const adminNodes = Array.from(document.querySelectorAll("[data-admin-only]"));

    if (!adminNodes.length) {
        return Promise.resolve(false);
    }

    if (!currentUser?.user_id || !getAuthToken()) {
        adminNodes.forEach((node) => {
            node.hidden = true;
        });
        return Promise.resolve(false);
    }

    return getAdminAccess(true).then((isAdmin) => {
        adminNodes.forEach((node) => {
            node.hidden = !isAdmin;
        });
        return isAdmin;
    }).catch(() => {
        adminNodes.forEach((node) => {
            node.hidden = true;
        });
        return false;
    });
}

export function updateCurrentUser() {
    removeQuickNav();
    renderAppbarAccount();
    updateAuthCtas();
    updateAdminCtas();
}

document.addEventListener("DOMContentLoaded", () => {
    removeQuickNav();
    renderAppbarAccount();
    updateAuthCtas();
    updateAdminCtas();
});
