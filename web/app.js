const TOKENS = {
  reception: "demo-reception-token",
  housekeeping: "demo-housekeeping-token",
  manager: "demo-manager-token",
};

let sessionId = null;

const messages = document.getElementById("messages");
const form = document.getElementById("chat-form");
const input = document.getElementById("message");
const role = document.getElementById("role");
const shift = document.getElementById("shift");
const capabilities = document.getElementById("capabilities");
const status = document.getElementById("status");

function addMessage(text, kind = "bot") {
  const bubble = document.createElement("div");
  bubble.className = `message ${kind}`;
  bubble.textContent = text;
  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
}

function addMeta(text) {
  const meta = document.createElement("div");
  meta.className = "message meta";
  meta.textContent = text;
  messages.appendChild(meta);
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
    status.textContent = "PMS connected · AI optional";
  } catch (error) {
    status.textContent = "Connection error";
    capabilities.textContent = "Unable to load capabilities";
  }
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
    if (result.command) addMeta(`Command: ${result.command}`);
  } catch (error) {
    addMessage(`The request could not be completed: ${error.message}`, "bot");
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(input.value);
});

document.querySelectorAll(".quick").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.dataset.message));
});

role.addEventListener("change", () => {
  sessionId = null;
  messages.innerHTML = "";
  addMessage("New staff session started. What do you need?", "bot");
  loadCapabilities();
});

shift.addEventListener("change", () => {
  sessionId = null;
  addMessage(`Shift context: ${shift.options[shift.selectedIndex].text}`, "meta");
});

addMessage("Welcome. I am the hotel staff assistant. Ask about arrivals, rooms, incidents, FAQs, or approved automation.", "bot");
loadCapabilities();
input.focus();
