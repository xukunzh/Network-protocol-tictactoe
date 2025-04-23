// Creat a new socket
const socket = io();

let playerId = "",
  room = "",
  roles = {},
  stats = {},
  history = [];

// Get element reference
const statusEl = document.getElementById("status");
const p1x = document.getElementById("p1x"),
  p1o = document.getElementById("p1o");
const p2x = document.getElementById("p2x"),
  p2o = document.getElementById("p2o");
const drawsEl = document.getElementById("draws");
const board = document.getElementById("board");
const msgEl = document.getElementById("messages");
const historyList = document.getElementById("history-list");

// Bind cell clicks
board.querySelectorAll(".cell").forEach(
  (c) =>
    (c.onclick = () => {
      const idx = +c.dataset.index;
      socket.emit("move", {
        playerId,
        room,
        index: idx,
        symbol: roles[playerId],
      });
    })
);

// Send chat
const input = document.getElementById("chat-input");
document.getElementById("send-btn").onclick = () => {
  const msg = input.value.trim();
  if (!msg) return;
  socket.emit("chat", { playerId, room, message: msg });
  input.value = "";
  log(`You: ${msg}`);
};

// Rematch
document.getElementById("rematch-btn").onclick = () => {
  socket.emit("rematch", { playerId, room });
  log("You requested a rematch");
};

// Join
socket.emit("join");
log("Emitted join event");

// Event Handlers triggered by server
socket.on("wait", (d) => {
  room = d.room;
  statusEl.innerText = "Waiting for opponent...";
  log(`Joined room ${room}, waiting for opponent`);
});

socket.on("start", (d) => {
  playerId = d.playerId;
  room = d.room;
  roles = d.roles;
  stats = d.stats;
  history = d.history;
  board.querySelectorAll(".cell").forEach((c) => (c.innerText = ""));
  renderHistory(history);
  updateStats(stats);
  statusEl.innerText = `You are P${playerId} (${roles[playerId]})`;
  document.getElementById("player1").innerText = `Player 1: (${roles["1"]})`;
  document.getElementById("player2").innerText = `Player 2: (${roles["2"]})`;
  log(`Game started. You are P${playerId} (${roles[playerId]})`);
});

// When the move is confirmed
socket.on("move", (d) => {
  board.querySelector(`[data-index="${d.index}"]`).innerText = d.symbol;
});

socket.on("stats", (s) => {
  stats = s;
  updateStats(s);
});

socket.on("game_over", (d) => {
  statusEl.innerText = d.message;
  log(`Game Over: ${d.message}`);
});

socket.on("chat", (c) => {
  const lbl = c.playerId === playerId ? "You" : `P${c.playerId}`;
  const div = document.createElement("div");
  div.innerText = `${lbl}: ${c.message}`;
  msgEl.appendChild(div);
  msgEl.scrollTop = msgEl.scrollHeight;
  log(`Chat received from ${lbl}: ${c.message}`);
});

socket.on("history", (h) => {
  history = h;
  renderHistory(h);
});

socket.on("rematch_pending", () => {
  statusEl.innerText = "Waiting for opponent...";
  log("Rematch request sent, waiting for opponent");
});

socket.on("rematch_request", () => {
  statusEl.innerText = "Your opponent is waiting for you.";
  log("Opponent requested a rematch");
});

function updateStats(s) {
  p1x.innerText = s["1"]["X"];
  p1o.innerText = s["1"]["O"];
  p2x.innerText = s["2"]["X"];
  p2o.innerText = s["2"]["O"];
  drawsEl.innerText = s["D"];
}

// Record the history
function renderHistory(hist) {
  historyList.innerHTML = "";
  hist.forEach((h, i) => {
    const li = document.createElement("li");
    if (h.winner === "D") li.innerText = `Game ${i + 1}: Draw`;
    else li.innerText = `Game ${i + 1}: Player ${h.winner} wins as ${h.symbol}`;
    historyList.appendChild(li);
  });
}

// Log function to print system logs to frontend panel
function log(message) {
  const logPanel = document.getElementById("log-panel");
  if (!logPanel) return;
  const entry = document.createElement("div");
  entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  logPanel.appendChild(entry);
  logPanel.scrollTop = logPanel.scrollHeight;
}
