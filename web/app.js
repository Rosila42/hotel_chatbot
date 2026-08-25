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
    const result = await api("/capabilities");
    capabilities.innerHTML = "";
    for (const name of result.commands) {
      const tag = document.createElement("span");
      tag.className = "capability";
      tag.textContent = name;
      capabilities.appendChild(tag);
    }
    status.textContent = "Connected · deterministic core · AI optional";
    updateContextSummary();
  } catch (error) {
    status.textContent = "Connection error";
    capabilities.textContent = "Unable to load capabilities";
  }
}

function metaForCommand(command) {
  if (!command) return null;
  const writes = new Set([
    "MARK_ROOM_CLEAN",
    "CREATE_INCIDENT",
    "RESOLVE_INCIDENT",
    "ENABLE_AUTOMATION",
    "DISABLE_AUTOMATION",
    "RUN_AUTOMATION",
  ]);
  const tone = writes.has(command) ? "write" : "read";
  return {
    text: `${command} · ${tone === "write" ? "write / confirmation gate" : "read"}`,
    tone,
  };
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

    const commandMeta = metaForCommand(result.command);
    if (commandMeta) addMeta(`Command: ${commandMeta.text}`, commandMeta.tone);
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
