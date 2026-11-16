const form = document.getElementById("query-form");
const questionInput = document.getElementById("question");
const sendButton = document.getElementById("send-button");
const messages = document.getElementById("messages");
const welcome = document.getElementById("welcome");
const chatArea = document.getElementById("chat-area");
const newChatButton = document.getElementById("new-chat");

let isBusy = false;

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[char]);
}

function renderMarkdown(text) {
  if (typeof marked === "undefined") return escapeHtml(text);
  const html = marked.parse(text, { gfm: true, breaks: true });
  // Sanitize the rendered HTML to keep the assistant response safe.
  return typeof DOMPurify !== "undefined" ? DOMPurify.sanitize(html) : html;
}

function addMessage(role, text, meta = "") {
  const row = document.createElement("div");
  row.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "T" : "F";

  const content = document.createElement("div");
  content.className = "bubble";
  if (role === "assistant") {
    // Only the assistant response is rendered as Markdown.
    content.innerHTML = renderMarkdown(text);
  } else {
    // User input stays as plain text to avoid XSS.
    content.textContent = text;
  }

  if (meta) {
    const metadata = document.createElement("div");
    metadata.className = "message-meta";
    metadata.textContent = meta;
    content.appendChild(metadata);
  }

  row.append(avatar, content);
  messages.appendChild(row);
  chatArea.scrollTop = chatArea.scrollHeight;
  return row;
}

function setBusy(value) {
  isBusy = value;
  sendButton.disabled = value;
  questionInput.disabled = value;
  sendButton.innerHTML = value ? '<span>…</span>' : '<span>↑</span>';
}

async function submitQuestion(question) {
  const cleanQuestion = question.trim();
  if (!cleanQuestion || isBusy) return;

  welcome.hidden = true;
  addMessage("user", cleanQuestion);
  questionInput.value = "";
  questionInput.style.height = "auto";

  const typing = document.createElement("div");
  typing.className = "typing";
  typing.setAttribute("role", "status");
  typing.setAttribute("aria-label", "El asistente está preparando una respuesta");
  typing.innerHTML =
    '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
  messages.appendChild(typing);
  chatArea.scrollTop = chatArea.scrollHeight;

  setBusy(true);
  try {
    const response = await fetch("/api/v1/assistant/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: cleanQuestion }),
    });

    const data = await response.json();
    typing.remove();

    if (!response.ok) {
      const detail = typeof data.detail === "string"
        ? data.detail
        : "No se pudo procesar la consulta.";
      addMessage("assistant", detail, "Error de servicio");
      return;
    }

    addMessage("assistant", data.answer, `Modelo: ${data.model} · Fuente: ${data.source}`);
  } catch (error) {
    typing.remove();
    addMessage(
      "assistant",
      "No se pudo conectar con la API. Verifica que el servidor FastAPI esté activo e intenta nuevamente.",
      "Error de conexión"
    );
  } finally {
    setBusy(false);
    questionInput.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  submitQuestion(questionInput.value);
});

questionInput.addEventListener("input", () => {
  questionInput.style.height = "auto";
  questionInput.style.height = `${Math.min(questionInput.scrollHeight, 150)}px`;
});

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    submitQuestion(button.dataset.question);
  });
});

newChatButton.addEventListener("click", () => {
  if (isBusy) return;
  messages.replaceChildren();
  welcome.hidden = false;
  questionInput.value = "";
  questionInput.focus();
});

questionInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});
