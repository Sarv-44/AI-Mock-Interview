import { setCurrentUser, updateCurrentUser } from "./session.js";

const SIGNIN_MODE = "signin";
const SIGNUP_MODE = "signup";

function setMessage(message, type = "info") {
    const node = document.getElementById("auth-message");
    if (!node) {
        return;
    }

    if (!message) {
        node.hidden = true;
        node.textContent = "";
        node.classList.remove("is-error", "is-success");
        return;
    }

    node.hidden = false;
    node.textContent = message;
    node.classList.toggle("is-error", type === "error");
    node.classList.toggle("is-success", type === "success");
}

function setAuthMode(mode) {
    document.querySelectorAll("[data-auth-mode]").forEach((button) => {
        const isActive = button.dataset.authMode === mode;
        button.setAttribute("aria-selected", String(isActive));
    });

    document.querySelectorAll("[data-auth-panel]").forEach((panel) => {
        panel.hidden = panel.dataset.authPanel !== mode;
    });

    setMessage("");
}

function normalizeAuthPayload(payload) {
    if (!payload || typeof payload !== "object") {
        return null;
    }

    return payload.user || payload.data || payload;
}

function extractAuthToken(payload) {
    if (!payload || typeof payload !== "object") {
        return null;
    }

    return payload.token || payload.auth_token || payload.access_token || null;
}

async function submitJson(url, body) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok || data.success === false) {
        throw new Error(data.error || data.message || "Something went wrong. Please try again.");
    }

    return data;
}

async function handleSignin(event) {
    event.preventDefault();

    const email = document.getElementById("signin-email")?.value.trim();
    const password = document.getElementById("signin-password")?.value || "";

    try {
        setMessage("Signing you in...");
        const response = await submitJson("/api/auth/login", { identifier: email, email, password });
        const user = normalizeAuthPayload(response);

        if (!user) {
            throw new Error("Signed in, but no user data came back.");
        }

        setCurrentUser(user, extractAuthToken(response));
        updateCurrentUser();
        setMessage("Signed in successfully. Redirecting to your profile...", "success");
        window.setTimeout(() => {
            window.location.href = "/profile";
        }, 500);
    } catch (error) {
        setMessage(error.message || "Unable to sign in.", "error");
    }
}

async function handleSignup(event) {
    event.preventDefault();

    const username = document.getElementById("signup-username")?.value.trim();
    const email = document.getElementById("signup-email")?.value.trim();
    const password = document.getElementById("signup-password")?.value || "";

    try {
        setMessage("Creating your account...");
        const response = await submitJson("/api/auth/signup", { username, email, password });
        const user = normalizeAuthPayload(response);

        if (!user) {
            throw new Error("Account created, but no user data came back.");
        }

        setCurrentUser(user, extractAuthToken(response));
        updateCurrentUser();
        setMessage("Account created. Redirecting to your profile...", "success");
        window.setTimeout(() => {
            window.location.href = "/profile";
        }, 500);
    } catch (error) {
        setMessage(error.message || "Unable to create account.", "error");
    }
}

function bindModeSwitch() {
    document.querySelectorAll("[data-auth-mode]").forEach((button) => {
        button.addEventListener("click", () => setAuthMode(button.dataset.authMode));
    });
}

function bindForms() {
    const signinForm = document.getElementById("signin-form");
    const signupForm = document.getElementById("signup-form");

    signinForm?.addEventListener("submit", handleSignin);
    signupForm?.addEventListener("submit", handleSignup);
}

document.addEventListener("DOMContentLoaded", () => {
    setAuthMode(SIGNIN_MODE);
    bindModeSwitch();
    bindForms();
});
