//////////////////////////////
// SESSION MANAGEMENT
//////////////////////////////
let sessionId;

// Check if a session already exists in localStorage
if (localStorage.getItem("sessionId")) {
    sessionId = localStorage.getItem("sessionId");
} else {
    sessionId = crypto.randomUUID();
    localStorage.setItem("sessionId", sessionId);
}

//////////////////////////////
// DOM ELEMENTS
//////////////////////////////
const chatBox = document.getElementById("chatBox");
const messageInput = document.getElementById("messageInput");

//////////////////////////////
// LOAD CHAT HISTORY
//////////////////////////////
function loadHistory() {
    fetch(`http://127.0.0.1:8000/history/${sessionId}`)
        .then(res => res.json())
        .then(data => {
            if (data.chat_history) {
                data.chat_history.forEach(item => {
                    chatBox.innerHTML += `<div class="user">You: ${item.user}</div>`;
                    chatBox.innerHTML += `<div class="bot">Bot: ${item.bot}</div>`;
                });
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        })
        .catch(err => {
            console.log("No previous history or error:", err);
        });
}

// Call on page load
window.onload = loadHistory;

//////////////////////////////
// SEND MESSAGE FUNCTION
//////////////////////////////
function sendMessage() {
    let message = messageInput.value.trim();
    if (message === "") return; // ignore empty input

    // Append user message
    chatBox.innerHTML += `<div class="user">You: ${message}</div>`;
    messageInput.value = "";
    chatBox.scrollTop = chatBox.scrollHeight;

    // Send message to backend
    fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message, session_id: sessionId })
    })
    .then(res => res.json())
    .then(data => {
        // Append bot response
        chatBox.innerHTML += `<div class="bot">Bot: ${data.advice}</div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(err => console.error("Error sending message:", err));
}

//////////////////////////////
// ENTER KEY SUPPORT
//////////////////////////////
messageInput.addEventListener("keypress", function(e) {
    if (e.key === "Enter") sendMessage();
});