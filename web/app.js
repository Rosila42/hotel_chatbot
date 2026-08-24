const TOKENS = {
  reception: "demo-reception-token",
  housekeeping: "demo-housekeeping-token",
  manager: "demo-manager-token",
};

const TOKENS = {
  reception: "demo-reception-token",
  housekeeping: "demo-housekeeping-token",
  manager: "demo-manager-token",
};

// Add this new mapping
const SHIFT_SUGGESTIONS = {
  morning: ["today's arrivals", "which rooms are not ready?"],
  afternoon: ["who is leaving today?", "show open incidents"],
  night: ["run automation NIGHT_AUDIT", "operational summary"]
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

function updateSuggestedPrompts(shiftValue) {
  const shiftKey = shiftValue ? shiftValue.toLowerCase() : "morning";
  const prompts = SHIFT_SUGGESTIONS[shiftKey] || SHIFT_SUGGESTIONS.morning;
  
  // Update the placeholder so the user knows what they can type
  input.placeholder = `Type freely... e.g., '${prompts[0]}'`;
  
  // If you have a container for clickable suggestions, populate it
  const suggestionsContainer = document.getElementById("suggested-prompts");
  if (suggestionsContainer) {
    suggestionsContainer.innerHTML = "";
    prompts.forEach(p => {
      const btn = document.createElement("button");
      btn.className = "quick"; // Reuse your existing quick button styling
      btn.textContent = p;
      btn.dataset.message = p;
      btn.addEventListener("click", () => sendMessage(p));
      suggestionsContainer.appendChild(btn);
    });
  }
}

function resetConversation(message = "New staff session started. What do you need?") {
  sessionId = null;
  messages.innerHTML = "";
  addMessage(message, "bot");
}

function activateReceptionMorningMode() {
  // 1. Reset the session (using the existing shift-UX fix)
  // Set the role to reception and shift to morning (if your select elements have these values)
  role.value = "reception";
  shift.value = "morning"; 
  
  // Clear the chat and session ID
  resetConversation("Reception — Morning session started. What do you need?");
  
  // Reload capabilities for the reception role
  loadCapabilities();
  
  // 2. Show the suggested next prompt
  // We add it as a meta message so it looks like a system hint
  addMeta("💡 Suggested next prompt: 'today's arrivals'");
  
  // Also set the placeholder text so they know they can type freely
  input.placeholder = "Type freely... e.g., 'today's arrivals' or 'status of room 214'";
  
  // 3. Let the user type freely
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

// Add this near your other event listeners
const morningBtn = document.getElementById("morning-mode-btn");
if (morningBtn) {
  morningBtn.addEventListener("click", activateReceptionMorningMode);
}

document.querySelectorAll(".quick").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.dataset.message));
});

role.addEventListener("change", () => {
  resetConversation();
  loadCapabilities();
});


shift.addEventListener("change", () => {
  // 1. Resets the session (existing behavior)
  resetConversation(`New ${shift.options[shift.selectedIndex].text.toLowerCase()} shift session started. What do you need?`);
  
  // 2. Does NOT change the available command set
  loadCapabilities(); 
  
  // 3. Adjusts the suggested-prompt list per shift
  updateSuggestedPrompts(shift.value);
});


addMessage("Welcome. I am the hotel staff assistant. Ask about arrivals, rooms, incidents, FAQs, or approved automation.", "bot");
loadCapabilities();
updateSuggestedPrompts(shift.value);
input.focus();
