const chat = document.getElementById("chat");
const form = document.getElementById("form");
const input = document.getElementById("input");
const statusEl = document.getElementById("status");

function addBubble(role, content) {
  const row = document.createElement("div");
  row.className = `row ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = content;

  row.appendChild(bubble);
  chat.appendChild(row);
  chat.scrollTop = chat.scrollHeight;
}

async function loadHistory() {
  const r = await fetch("/api/history");
  if (!r.ok) return;
  const items = await r.json();

  chat.innerHTML = "";
  for (const it of items) addBubble(it.role, it.content);
}

let sending = false;

async function sendMessage(text) {
  if (sending) return;
  sending = true;

  try {
    const r = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    if (!r.ok) {
      addBubble("assistant", "Server error.");
      return;
    }

    const data = await r.json();
    if (data.ok && data.reply) addBubble("assistant", data.reply);
  } finally {
    sending = false;
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const text = input.value.trim();
  if (!text) return;

  input.value = "";
  addBubble("user", text);
  await sendMessage(text);
});

statusEl.textContent = "Online";
loadHistory();
