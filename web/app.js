const TOKENS = {
  reception: "demo-reception-token",
  housekeeping: "demo-housekeeping-token",
  manager: "demo-manager-token",
};

const ROLE_SUGGESTIONS = {
  reception: {
    morning: [
      "Who is checking in today?",
      "Which rooms are not ready for today's arrivals?",
      "What is the status of room 214?",
    ],
    afternoon: [
      "Who is leaving today?",
      "Show open incidents",
      "What is the status of room 214?",
    ],
    night: [
      "Show operational summary",
      "Show open incidents",
      "List automations",
    ],
  },
  housekeeping: {
    default: [
      "Which rooms are not ready?",
      "Show open incidents",
      "What is the status of room 214?",
    ],
  },
  manager: {
    default: [
      "Show operational summary",
      "Show open incidents",
      "List automations",
    ],
  },
};

const ROLE_LABELS = {
  reception: "Reception",
  housekeeping: "Housekeeping",
  manager: "Management",
};

let sessionId = null;

const messages = document.getElementById("messages");
const form = document.getElementById("chat-form");
const input = document.getElementById("message");
const role = document.getElementById("role");
const shift = document.getElementById("shift");
const capabilities = document.getElementById("capabilities");
const status = document.getElementById("status");
const contextSummary = document.getElementById("context-summary");

function addMessage(text, kind = "bot") {
  const bubble = document.createElement("div");
  bubble.className = `message ${kind}`;
  bubble.textContent = text;
  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
}

function addMeta(text, tone = "default") {
  const meta = document.createElement("div");
  meta.className = `message meta ${tone}`;
  meta.textContent = text;
  messages.appendChild(meta);
}

/**
 * Adds a meta line only if the value is present and non‑empty.
 * Used for the observability gates.
 */
function addMetaLine(label, value, tone = "default") {
  if (value !== undefined && value !== null && String(value).trim() !== "") {
    addMeta(`${label}: ${value}`, tone);
  }
}

function currentSuggestions() {
  const roleKey = role.value;
  const roleConfig = ROLE_SUGGESTIONS[roleKey] || ROLE_SUGGESTIONS.reception;
  if (roleKey === "reception") {
    const shiftKey = shift.value || "morning";
    return roleConfig[shiftKey] || roleConfig.morning;
  }
  return roleConfig.default;
}

function updateContextSummary() {
  if (!contextSummary) return;
  const roleLabel = ROLE_LABELS[role.value] || "Staff";
  const shiftLabel = shift.value ? shift.options[shift.selectedIndex].text : "No shift specified";
  contextSummary.textContent = `${roleLabel} · ${shiftLabel}`;
}

function updateSuggestedPrompts() {
  const prompts = currentSuggestions();
  input.placeholder = `Ask naturally… e.g. '${prompts[0]}'`;

  const suggestionsContainer = document.getElementById("suggested-prompts");
  if (!suggestionsContainer) return;

  suggestionsContainer.innerHTML = "";
  prompts.forEach((prompt) => {
    const button = document.createElement("button");
    button.className = "quick";
    button.type = "button";
    button.textContent = prompt;
    button.dataset.message = prompt;
    button.addEventListener("click", () => sendMessage(prompt));
    suggestionsContainer.appendChild(button);
  });
}

function resetConversation(message = "New staff session started. What do you need?") {
  sessionId = null;
  messages.innerHTML = "";
  addMessage(message, "bot");
}

function activateReceptionMorningMode() {
  role.value = "reception";
  shift.value = "morning";
  resetConversation("Reception — Morning session started. Let's work through today's arrivals.");
  loadCapabilities();
  updateSuggestedPrompts();
  updateContextSummary();
  addMeta("Demo flow: arrivals → room readiness → incident → housekeeping → management");
  input.value = "";
  input.focus();
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${TOKENS[role.value]}`,
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return response.json();
}

async function loadCapabilities() {
  try {
    const [result, health] = await Promise.all([
      api("/capabilities"),
      api("/health"),
    ]);
    capabilities.innerHTML = "";
    for (const name of result.commands) {
      const tag = document.createElement("span");
      tag.className = "capability";
      tag.textContent = name;
      capabilities.appendChild(tag);
    }
    const version = health.version ? `v${health.version}` : "version unknown";
    status.textContent = `Connected · ${version} · deterministic core · AI optional`;
    updateContextSummary();
  } catch (error) {
    status.textContent = "Connection error";
    capabilities.textContent = "Unable to load capabilities";
  }
}

/**
 * Builds an array of observability meta items from the backend response.
 * Each item is { label, value, tone } and will be displayed by addMetaLine.
 */
function buildObservabilityMeta(result) {
  const meta = [];

  // Gate 1: Input observability
  if (result.command) {
    const params = result.parameters
      ? Object.entries(result.parameters)
          .map(([k, v]) => `${k}=${v}`)
          .join(", ")
      : "";
    const commandText = params ? `${result.command} ${params}` : result.command;
    meta.push({ label: "Command", value: commandText, tone: "default" });
    if (result.parser_source) {
      meta.push({ label: "Parser", value: result.parser_source, tone: "default" });
    }
  }

  // Gate 2: Permission observability
  if (result.permission) {
    const perm = result.permission;
    if (perm.allowed) {
      meta.push({
        label: "Permission",
        value: `allowed · ${perm.role}`,
        tone: "allowed",
      });
    } else {
      const allowedRoles = perm.allowed_roles?.join(", ") || "none";
      meta.push({
        label: "Permission",
        value: `denied · ${perm.role} (allowed: ${allowedRoles})`,
        tone: "denied",
      });
    }
  }

  // Gate 3: Confirmation observability
  if (result.confirmation) {
    const conf = result.confirmation;
    if (conf.state === "pending") {
      meta.push({
        label: "Confirmation",
        value: "PENDING — no PMS write yet",
        tone: "write",
      });
    } else if (conf.state === "confirmed") {
      meta.push({
        label: "Confirmation",
        value: "confirmed",
        tone: "allowed",
      });
    } else if (conf.state === "cancelled") {
      meta.push({
        label: "Confirmation",
        value: "cancelled — no PMS write",
        tone: "denied",
      });
    }
  }

  // Gate 4: PMS boundary observability
  if (result.pms_adapter) {
    meta.push({
      label: "PMS",
      value: result.pms_adapter,
      tone: "default",
    });
  }

  // Gate 5: Audit/state observability
  if (result.state_before !== undefined && result.state_after !== undefined) {
    meta.push({
      label: "State",
      value: `${result.state_before} → ${result.state_after}`,
      tone: "default",
    });
  }
  if (result.audit_recorded !== undefined) {
    meta.push({
      label: "Audit",
      value: result.audit_recorded ? "recorded" : "not recorded",
      tone: result.audit_recorded ? "allowed" : "denied",
    });
  }

  return meta;
}

async function sendMessage(text) {
  const clean = text.trim();
  if (!clean) return;

  addMessage(clean, "user");
  input.value = "";

  try {
    const result = await api("/chat", {
      method: "POST",
      body: JSON.stringify({
        message: clean,
        session_id: sessionId,
        shift: shift.value || null,
      }),
    });

    sessionId = result.session_id;
    addMessage(result.message, "bot");

    // Display observability gates (Input, Permission, Confirmation, PMS, Audit/State)
    const observabilityMeta = buildObservabilityMeta(result);
    observabilityMeta.forEach((item) => {
      addMetaLine(item.label, item.value, item.tone);
    });
  } catch (error) {
    addMessage(`The request could not be completed: ${error.message}`, "bot");
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(input.value);
});

const morningBtn = document.getElementById("morning-mode-btn");
if (morningBtn) {
  morningBtn.addEventListener("click", activateReceptionMorningMode);
}

document.querySelectorAll(".quick").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.dataset.message));
});

role.addEventListener("change", () => {
  if (role.value !== "reception") shift.value = "";
  resetConversation(`${ROLE_LABELS[role.value] || "Staff"} session started. What do you need?`);
  loadCapabilities();
  updateSuggestedPrompts();
  updateContextSummary();
});

shift.addEventListener("change", () => {
  const label = shift.options[shift.selectedIndex].text.toLowerCase();
  resetConversation(`New ${label} shift session started. What do you need?`);
  loadCapabilities();
  updateSuggestedPrompts();
  updateContextSummary();
});

addMessage("Welcome. I am the hotel staff assistant. I can help with arrivals, departures, rooms, guests, incidents, FAQs, and approved automation.", "bot");
addMeta("The deterministic core is authoritative; AI is optional and cannot execute PMS operations.");
updateContextSummary();
loadCapabilities();
updateSuggestedPrompts();
input.focus();