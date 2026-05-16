/* English Secretary — Frontend Controller */

const state = {
  currentAgent: 'victoria',
  messages: {},
  history: [],
  voiceEnabled: true,
  isListening: false,
  recognition: null,
};

const AGENT_NAMES = { victoria: 'Victoria', edmund: 'Edmund', charlie: 'Charlie', beatrice: 'Beatrice' };

// ── DOM refs ──────────────────────────────────────────────────────
const $ = (s) => document.querySelector(s);
const chatArea = $('#messages');
const msgInput = $('#msg-input');
const sendBtn = $('#btn-send');
const voiceBtn = $('#btn-voice');
const vocabBtn = $('#btn-vocab');
const briefingBtn = $('#btn-briefing');
const statsBtn = $('#btn-stats');
const panel = $('#right-panel');
const panelTitle = $('#panel-title');
const panelContent = $('#panel-content');
const panelClose = $('#panel-close');
const voiceIndicator = $('#voice-indicator');
const currentAgentLabel = $('#current-agent');
const currentAgentTitle = $('#current-agent-title');

// ── Init ──────────────────────────────────────────────────────────
async function init() {
  loadAgents();
  await loadVocabularySummary();
  addSystemMessage('Welcome! Select an agent to start. Type a message or click the microphone for voice input.');
}

// ── Agent Switching ───────────────────────────────────────────────
function loadAgents() {
  document.querySelectorAll('.agent-item').forEach(el => {
    el.addEventListener('click', () => switchAgent(el.dataset.agent));
  });
}

function switchAgent(agent) {
  state.currentAgent = agent;
  document.querySelectorAll('.agent-item').forEach(el => {
    el.classList.toggle('active', el.dataset.agent === agent);
  });
  currentAgentLabel.textContent = AGENT_NAMES[agent] || agent;
  const titles = { victoria: 'Learning Director', edmund: 'Vocabulary Butler', charlie: 'Speaking Partner', beatrice: 'News Anchor' };
  currentAgentTitle.textContent = titles[agent] || '';
  chatArea.innerHTML = '';
  state.history = [];
  addSystemMessage(`Now chatting with ${AGENT_NAMES[agent]}. How can I help you?`);
}

// ── Chat ──────────────────────────────────────────────────────────
function addMessage(text, role) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.textContent = text;
  chatArea.appendChild(div);
  chatArea.scrollTop = chatArea.scrollHeight;
  return div;
}

function addSystemMessage(text) {
  const div = document.createElement('div');
  div.className = 'message system';
  div.textContent = text;
  chatArea.appendChild(div);
  chatArea.scrollTop = chatArea.scrollHeight;
}

function showTyping() {
  const div = document.createElement('div');
  div.className = 'typing-indicator';
  div.id = 'typing-indicator';
  div.innerHTML = '<span></span><span></span><span></span>';
  chatArea.appendChild(div);
  chatArea.scrollTop = chatArea.scrollHeight;
}

function hideTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

async function sendMessage(text) {
  if (!text.trim()) return;
  addMessage(text, 'user');
  msgInput.value = '';
  msgInput.style.height = 'auto';
  showTyping();

  state.history.push({ role: 'user', content: text });

  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent: state.currentAgent,
        message: text,
        history: state.history.slice(-10),
      }),
    });
    const data = await resp.json();
    hideTyping();

    addMessage(data.reply, 'agent');
    state.history.push({ role: 'assistant', content: data.reply });

    // Auto voice output
    if (state.voiceEnabled && data.voice_text) {
      speakText(data.voice_text);
    }
  } catch (err) {
    hideTyping();
    addSystemMessage(`Error: ${err.message}. Make sure the server is running.`);
  }
}

// ── Voice Output (TTS) ────────────────────────────────────────────
function speakText(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'en-US';
  utterance.rate = 0.95;
  window.speechSynthesis.speak(utterance);
}

function toggleVoice() {
  state.voiceEnabled = !state.voiceEnabled;
  voiceIndicator.textContent = state.voiceEnabled ? '🔊 ON' : '🔇 OFF';
  voiceIndicator.style.color = state.voiceEnabled ? '#34a853' : '#999';
}

// ── Voice Input ───────────────────────────────────────────────────
function initVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    voiceBtn.title = 'Voice input not supported in this browser';
    voiceBtn.style.opacity = '0.4';
    return;
  }
  state.recognition = new SpeechRecognition();
  state.recognition.lang = 'en-US';
  state.recognition.continuous = false;
  state.recognition.interimResults = false;

  state.recognition.onresult = (event) => {
    const text = event.results[0][0].transcript;
    voiceBtn.classList.remove('listening');
    state.isListening = false;
    sendMessage(text);
  };

  state.recognition.onerror = () => {
    voiceBtn.classList.remove('listening');
    state.isListening = false;
  };

  state.recognition.onend = () => {
    voiceBtn.classList.remove('listening');
    state.isListening = false;
  };

  voiceBtn.addEventListener('click', () => {
    if (state.isListening) {
      state.recognition.stop();
      voiceBtn.classList.remove('listening');
      state.isListening = false;
      return;
    }
    try {
      state.recognition.start();
      voiceBtn.classList.add('listening');
      state.isListening = true;
    } catch (e) {
      console.warn('Voice input error:', e);
    }
  });
}

// ── Input Handler ─────────────────────────────────────────────────
msgInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage(msgInput.value);
  }
});

sendBtn.addEventListener('click', () => sendMessage(msgInput.value));

msgInput.addEventListener('input', () => {
  msgInput.style.height = 'auto';
  msgInput.style.height = Math.min(msgInput.scrollHeight, 120) + 'px';
});

voiceIndicator.addEventListener('click', toggleVoice);

// ── Right Panel: Vocabulary ───────────────────────────────────────
async function loadVocabularySummary() {
  try {
    const resp = await fetch('/api/vocabulary');
    const data = await resp.json();
    document.querySelector('#sidebar-footer #vocab-summary').textContent =
      `Vocabulary: ${data.total} words`;
  } catch (e) {}
}

async function showVocabulary() {
  panelTitle.textContent = 'Vocabulary Library';
  panel.classList.remove('hidden');
  panelContent.innerHTML = '<p>Loading...</p>';

  try {
    const resp = await fetch('/api/vocabulary');
    const data = await resp.json();

    if (data.words.length === 0) {
      panelContent.innerHTML = '<p>No words yet. Start learning!</p>';
      return;
    }

    let html = `<p style="margin-bottom:12px;color:var(--text-secondary)">${data.total} words total</p>`;
    html += '<table class="vocab-table"><thead><tr><th>Word</th><th>Domain</th><th>CEFR</th><th>Status</th></tr></thead><tbody>';

    data.words.forEach(w => {
      const statusClass = w.status === 'productive' ? 'status-productive' : 'status-receptive';
      html += `<tr>
        <td><strong>${w.word}</strong></td>
        <td>${w.domain}</td>
        <td>${w.cefr || '—'}</td>
        <td class="${statusClass}">${w.status}</td>
      </tr>`;
    });
    html += '</tbody></table>';
    panelContent.innerHTML = html;
  } catch (e) {
    panelContent.innerHTML = `<p style="color:red">Error: ${e.message}</p>`;
  }
}

async function showBriefing() {
  panelTitle.textContent = "Today's Briefing";
  panel.classList.remove('hidden');
  panelContent.innerHTML = '<p>Loading...</p>';

  try {
    const resp = await fetch('/api/briefing');
    const data = await resp.json();
    panelContent.innerHTML = `<div class="briefing-content">${data.content || 'No briefing available.'}</div>`;
  } catch (e) {
    panelContent.innerHTML = `<p style="color:red">Error: ${e.message}</p>`;
  }
}

async function showStats() {
  panelTitle.textContent = 'Learning Stats';
  panel.classList.remove('hidden');
  panelContent.innerHTML = '<p>Loading...</p>';

  try {
    const resp = await fetch('/api/stats');
    const data = await resp.json();
    panelContent.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card"><div class="stat-value">${data.total_vocabulary || 0}</div><div class="stat-label">Words</div></div>
        <div class="stat-card"><div class="stat-value">${data.current_streak || 0}</div><div class="stat-label">Day Streak</div></div>
        <div class="stat-card"><div class="stat-value">${data.productive || 0}</div><div class="stat-label">Productive</div></div>
        <div class="stat-card"><div class="stat-value">${data.sessions_completed || 0}</div><div class="stat-label">Sessions</div></div>
      </div>`;
  } catch (e) {
    panelContent.innerHTML = `<p style="color:red">Error: ${e.message}</p>`;
  }
}

// ── Panel controls ────────────────────────────────────────────────
vocabBtn.addEventListener('click', showVocabulary);
briefingBtn.addEventListener('click', showBriefing);
statsBtn.addEventListener('click', showStats);
panelClose.addEventListener('click', () => panel.classList.add('hidden'));

// ── Keyboard shortcuts ────────────────────────────────────────────
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') panel.classList.add('hidden');
});

// ── Start ─────────────────────────────────────────────────────────
init();
initVoiceInput();
