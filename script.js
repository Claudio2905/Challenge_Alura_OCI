// ============================================================
// BimBam Buy · Asistente de Atención al Cliente
// Frontend estático (HTML + CSS + Bootstrap 5 + JS puro)
// Consume el backend FastAPI: POST {API_URL} con { texto }
// ============================================================

// Cambia esta URL si tu backend corre en otro host/puerto.
const API_URL = "http://127.0.0.1:8000/preguntar";

const SUGGESTED_QUESTIONS = [
  "¿Cuáles son los tipos de envíos disponibles?",
  "¿Cuál es la cobertura general de la garantía?",
  "¿Cuánto tiempo tengo para solicitar un reembolso?",
  "¿Cuáles son los métodos de pago disponibles?",
];

const GREETING =
  "¡Hola! Soy el asistente virtual de BimBam Buy. Puedo ayudarte con dudas sobre envíos, garantías, reembolsos y métodos de pago. ¿En qué te ayudo hoy?";

// ---------- Referencias del DOM ----------
const chatScroll = document.getElementById("chatScroll");
const composerForm = document.getElementById("composerForm");
const composerInput = document.getElementById("composerInput");
const composerSend = document.getElementById("composerSend");

const suggestedListDesktop = document.getElementById("suggestedListDesktop");
const suggestedListMobile = document.getElementById("suggestedListMobile");

const statusDotDesktop = document.getElementById("statusDotDesktop");
const statusTextDesktop = document.getElementById("statusTextDesktop");
const statusDotMobile = document.getElementById("statusDotMobile");

let isSending = false;

// ---------- Utilidades de render ----------
function scrollToBottom() {
  chatScroll.scrollTop = chatScroll.scrollHeight;
}

function appendMessage(role, text) {
  const wrapper = document.createElement("div");
  wrapper.className = `msg ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = role === "user" ? "Tú" : "BB";

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  bubble.textContent = text;

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  chatScroll.appendChild(wrapper);
  scrollToBottom();

  return bubble;
}

function appendTypingIndicator() {
  const wrapper = document.createElement("div");
  wrapper.className = "msg bot";
  wrapper.id = "typingIndicator";

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = "BB";

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  bubble.innerHTML = '<span class="typing-dots"><span></span><span></span><span></span></span>';

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  chatScroll.appendChild(wrapper);
  scrollToBottom();
}

function removeTypingIndicator() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

function setStatus(online) {
  const dots = [statusDotDesktop, statusDotMobile];
  dots.forEach((d) => {
    if (!d) return;
    d.classList.toggle("online", online);
    d.classList.toggle("offline", !online);
  });
  if (statusTextDesktop) {
    statusTextDesktop.textContent = online ? "En línea" : "Sin conexión";
  }
}

// ---------- Preguntas sugeridas ----------
function renderSuggestedQuestions() {
  [suggestedListDesktop, suggestedListMobile].forEach((container) => {
    if (!container) return;
    container.innerHTML = "";
    SUGGESTED_QUESTIONS.forEach((question) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "suggested-btn";
      btn.textContent = question;
      btn.addEventListener("click", () => {
        composerInput.value = question;
        // Cierra el offcanvas en mobile antes de enviar
        const offcanvasEl = document.getElementById("sidebarOffcanvas");
        const instance = bootstrap.Offcanvas.getInstance(offcanvasEl);
        if (instance) instance.hide();
        sendQuestion(question);
      });
      container.appendChild(btn);
    });
  });
}

// ---------- Envío de preguntas ----------
async function sendQuestion(text) {
  const pregunta = text.trim();
  if (!pregunta || isSending) return;

  isSending = true;
  composerSend.disabled = true;
  composerInput.value = "";

  appendMessage("user", pregunta);
  appendTypingIndicator();

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto: pregunta }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    removeTypingIndicator();
    appendMessage("bot", data.respuesta || "No lo sé");
    setStatus(true);
  } catch (err) {
    removeTypingIndicator();
    appendMessage(
      "error",
      "No pude conectarme con el asistente. Verifica que el servidor esté activo e inténtalo de nuevo."
    );
    setStatus(false);
    console.error("Error al consultar el backend:", err);
  } finally {
    isSending = false;
    composerSend.disabled = false;
    composerInput.focus();
  }
}

// ---------- Eventos ----------
composerForm.addEventListener("submit", (event) => {
  event.preventDefault();
  sendQuestion(composerInput.value);
});

// ---------- Inicialización ----------
document.addEventListener("DOMContentLoaded", () => {
  renderSuggestedQuestions();
  appendMessage("bot", GREETING);
  setStatus(true); // estado optimista; se corrige si una petición falla
  composerInput.focus();
});