const chatWindow = document.getElementById('chat-window');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const statusLine = document.getElementById('status-line');
const welcomeContainer = document.getElementById('welcome-container');
const restartBtn = document.getElementById('restart-chat-btn');

const SOURCE_DISPLAY_MAP = {
  'upi_guide.md': 'NPCI UPI Safety Directive',
  'scam_awareness.md': 'RBI Cybersecurity Advisory',
  'budgeting_basics.md': 'National Financial Literacy Guideline',
  'interest_and_loans.md': 'RBI Banking Regulation',
  '9781464822049.pdf': 'World Bank Financial Literacy Report',
  'English_16042021.pdf': 'NCFE Financial Education Material',
  'Final_Report_MTE_NSFE-1.pdf': 'NCFE Strategy Evaluation Report',
  'NCFE-2019_Final_Report.pdf': 'NCFE Financial Survey Report',
  'NSFE_20-25_ENG.pdf': 'RBI National Strategy for Financial Education (2020-25)'
};

function getSourceDisplayName(filename) {
  return SOURCE_DISPLAY_MAP[filename] || filename.replace('.md', '').replace('.pdf', '').replace(/_/g, ' ');
}

function addMessage(text, sender, meta) {
  // Hide welcome bento on first query
  if (welcomeContainer && welcomeContainer.style.display !== 'none') {
    welcomeContainer.style.display = 'none';
  }

  const row = document.createElement('div');
  row.className = `msg msg-${sender}`;

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.textContent = text;
  row.appendChild(bubble);

  if (meta) {
    if (meta.sources && meta.sources.length) {
      const src = document.createElement('div');
      src.className = 'sources-line';
      
      const label = document.createElement('div');
      label.className = 'source-label';
      label.textContent = 'Grounded Sources';
      src.appendChild(label);

      const container = document.createElement('div');
      container.className = 'source-chips-container';
      meta.sources.forEach(s => {
        const chip = document.createElement('span');
        chip.className = 'source-chip';
        chip.textContent = getSourceDisplayName(s);
        container.appendChild(chip);
      });
      src.appendChild(container);
      bubble.appendChild(src);
    }
    
    if (meta.demo_mode) {
      const flag = document.createElement('div');
      flag.className = 'demo-flag';
      flag.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        <span>Demo mode — connect watsonx.ai Granite for full AI answers</span>
      `;
      bubble.appendChild(flag);
    }
  }

  chatWindow.appendChild(row);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function showTyping() {
  const row = document.createElement('div');
  row.className = 'msg msg-bot';
  row.id = 'typing-indicator';

  const indicator = document.createElement('div');
  indicator.className = 'typing-indicator';
  indicator.innerHTML = '<span></span><span></span><span></span>';
  row.appendChild(indicator);

  chatWindow.appendChild(row);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function removeTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

function renderMetadata(bubble, sources, used_fallback) {
  if (sources && sources.length) {
    const src = document.createElement('div');
    src.className = 'sources-line';
    
    const label = document.createElement('div');
    label.className = 'source-label';
    label.textContent = 'Grounded Sources';
    src.appendChild(label);

    const container = document.createElement('div');
    container.className = 'source-chips-container';
    sources.forEach(s => {
      const chip = document.createElement('span');
      chip.className = 'source-chip';
      chip.textContent = getSourceDisplayName(s);
      container.appendChild(chip);
    });
    src.appendChild(container);
    bubble.appendChild(src);
  }
  
  if (used_fallback) {
    const flag = document.createElement('div');
    flag.className = 'demo-flag';
    flag.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      <span>Demo mode — connect watsonx.ai Granite for full AI answers</span>
    `;
    bubble.appendChild(flag);
  }
}

async function sendMessage(text) {
  // Add user message
  addMessage(text, 'user');
  
  sendBtn.disabled = true;
  chatInput.disabled = true;
  statusLine.textContent = 'FinGuide-Ai is thinking...';
  showTyping();

  // Create Bot Message container (hidden initially)
  const botRow = document.createElement('div');
  botRow.className = 'msg msg-bot';
  const botBubble = document.createElement('div');
  botBubble.className = 'msg-bubble';
  
  const textContent = document.createElement('span');
  botBubble.appendChild(textContent);
  botRow.appendChild(botBubble);

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });

    if (!res.ok) {
      throw new Error(`Server returned status ${res.status}`);
    }

    removeTyping();
    chatWindow.appendChild(botRow);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      
      // Save last incomplete line back to buffer
      buffer = lines.pop();

      for (const line of lines) {
        const cleaned = line.trim();
        if (!cleaned || !cleaned.startsWith('data: ')) continue;
        
        try {
          const event = JSON.parse(cleaned.substring(6));
          if (event.type === 'metadata') {
            renderMetadata(botBubble, event.sources, event.used_fallback);
          } else if (event.type === 'token') {
            textContent.textContent += event.text;
            chatWindow.scrollTop = chatWindow.scrollHeight;
          } else if (event.type === 'error') {
            textContent.textContent = 'Error: ' + event.error;
          }
        } catch (e) {
          console.error('Failed to parse SSE:', cleaned, e);
        }
      }
    }

  } catch (err) {
    removeTyping();
    if (!botRow.parentNode) {
      chatWindow.appendChild(botRow);
    }
    if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
      textContent.textContent = 'Network error — is the server running?';
    } else {
      textContent.textContent = 'Error: ' + err.message;
    }
  } finally {
    statusLine.textContent = '';
    sendBtn.disabled = false;
    chatInput.disabled = false;
    chatInput.focus();
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }
}

chatForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;
  chatInput.value = '';
  sendMessage(text);
});

// Setup click handlers for all suggestion buttons (sidebar and welcome chips)
function setupTriggerElements(selector) {
  document.querySelectorAll(selector).forEach(btn => {
    btn.addEventListener('click', () => {
      const q = btn.getAttribute('data-q');
      if (q) {
        chatInput.value = q;
        chatForm.dispatchEvent(new Event('submit'));
      }
    });
  });
}

setupTriggerElements('.sidebar-item');
setupTriggerElements('.prompt-chip');

// Restart chat session action
if (restartBtn) {
  restartBtn.addEventListener('click', () => {
    const msgs = chatWindow.querySelectorAll('.msg');
    msgs.forEach(m => m.remove());
    if (welcomeContainer) {
      welcomeContainer.style.display = 'flex';
    }
    statusLine.textContent = '';
  });
}

