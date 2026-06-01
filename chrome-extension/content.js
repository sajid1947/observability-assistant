function createButton() {
  const btn = document.createElement('button');
  btn.id = 'obs-ai-extension-btn';
  btn.type = 'button';
  btn.innerHTML = '✨ AI Assistant';
  
  btn.addEventListener('click', toggleChat);
  document.body.appendChild(btn);
}

function createChatWindow() {
  const chat = document.createElement('div');
  chat.id = 'obs-ai-extension-chat';
  
  chat.innerHTML = `
    <div id="obs-ai-extension-chat-header">
      <h3>✨ SRE Copilot</h3>
      <button id="obs-ai-close-btn">&times;</button>
    </div>
    <div id="obs-ai-extension-chat-body">
      <div class="obs-ai-message bot">
        Hi! I'm your AI Observability Assistant. Click below to analyze the entire page, or select a specific panel (like CPU or Memory) on the screen!
      </div>
      <div style="display: flex; gap: 8px; margin-top: 8px;">
        <button id="obs-ai-analyze-all-btn" class="obs-ai-action-btn">Analyze Full Page</button>
        <button id="obs-ai-select-panel-btn" class="obs-ai-action-btn primary">Select Specific Panel</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(chat);
  
  document.getElementById('obs-ai-close-btn').addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    chat.classList.remove('open');
  });
  
  document.getElementById('obs-ai-analyze-all-btn').addEventListener('click', () => {
    startAnalysis(); // Uses full page
  });

  document.getElementById('obs-ai-select-panel-btn').addEventListener('click', () => {
    enableSelectMode();
  });
  
  return chat;
}

function toggleChat(event) {
  event.preventDefault();
  event.stopPropagation();

  let chat = document.getElementById('obs-ai-extension-chat');
  if (!chat) {
    chat = createChatWindow();
    setTimeout(() => {
      chat.classList.add('open');
    }, 10);
  } else {
    chat.classList.add('open');
  }
}

let isSelecting = false;

function enableSelectMode() {
  isSelecting = true;
  document.body.classList.add('obs-ai-selecting-mode');
  
  const chat = document.getElementById('obs-ai-extension-chat');
  if (chat) chat.style.opacity = '0.4'; // Dim chat window while selecting
  
  document.addEventListener('mouseover', handleMouseOver, true);
  document.addEventListener('mouseout', handleMouseOut, true);
  document.addEventListener('click', handlePanelClick, true);
}

function handleMouseOver(e) {
  if (!isSelecting) return;
  if (e.target.closest('#obs-ai-extension-chat') || e.target.closest('#obs-ai-extension-btn')) return;
  e.target.classList.add('obs-ai-selectable');
}

function handleMouseOut(e) {
  if (!isSelecting) return;
  e.target.classList.remove('obs-ai-selectable');
}

function handlePanelClick(e) {
  if (!isSelecting) return;
  if (e.target.closest('#obs-ai-extension-chat') || e.target.closest('#obs-ai-extension-btn')) return;
  
  e.preventDefault();
  e.stopPropagation();
  
  isSelecting = false;
  document.body.classList.remove('obs-ai-selecting-mode');
  
  const chat = document.getElementById('obs-ai-extension-chat');
  if (chat) chat.style.opacity = '1';
  
  document.removeEventListener('mouseover', handleMouseOver, true);
  document.removeEventListener('mouseout', handleMouseOut, true);
  document.removeEventListener('click', handlePanelClick, true);
  
  document.querySelectorAll('.obs-ai-selectable').forEach(el => el.classList.remove('obs-ai-selectable'));
  
  // Extract text specifically from the clicked panel
  startAnalysis(e.target.innerText);
}

function extractPageData(customText) {
  const ignoreList = [
    'skip to main content', 'grafana', 'home', 'bookmarks', 'starred',
    'dashboards', 'playlists', 'snapshots', 'library panels',
    'shared dashboards', 'explore', 'drilldown', 'new!', 'alerting',
    'alert rules', 'contact points', 'notification policies', 'silences',
    'active notifications', 'administration', 'search...', '⌘+k', 'edit',
    'export', 'share'
  ];

  // Use the custom selected text, or fallback to the whole page body
  const rawText = customText || document.body.innerText;
  const lines = rawText.split('\n')
    .map(l => l.trim())
    .filter(l => l.length > 0 && l.length < 200)
    .filter(l => !ignoreList.includes(l.toLowerCase())); // Skip UI boilerplate
    
  return lines.slice(0, 100);
}

function startAnalysis(customText = null) {
  const chatBody = document.getElementById('obs-ai-extension-chat-body');
  
  const pageText = extractPageData(customText);
  const logs = pageText.length > 0 ? pageText : [
    "No visible data found."
  ];
  
  // Add User Message
  const userMsg = document.createElement('div');
  userMsg.className = 'obs-ai-message user';
  userMsg.innerHTML = customText ? 'Analyze this specific panel for me.' : 'Analyze the whole dashboard for me.';
  chatBody.appendChild(userMsg);
  
  // Add Bot Loading Message
  const loadingMsg = document.createElement('div');
  loadingMsg.className = 'obs-ai-message bot';
  loadingMsg.innerHTML = `
    <div class="obs-ai-loading">
      <div class="obs-ai-spinner"></div>
      <span>Extracting & Analyzing...</span>
    </div>
  `;
  chatBody.appendChild(loadingMsg);
  
  // Scroll to bottom
  chatBody.scrollTop = chatBody.scrollHeight;

  const payload = {
    source: window.location.href.substring(0, 64),
    logs: logs.map(l => ({ message: l })),
    time_range: { start: 'now-1h', end: 'now' }
  };
  
  // Log payload to the browser console for developer inspection/improvement
  console.log("Observability AI - Sending Payload to Backend:", payload);

  // Chrome V3 Service Workers sleep after 30 seconds of inactivity.
  // Because local AI analysis takes a few minutes, we must ping the background script 
  // every 10 seconds to keep it awake!
  const keepAliveInterval = setInterval(() => {
    chrome.runtime.sendMessage({ type: 'PING' }, () => {
      if (chrome.runtime.lastError) { /* ignore */ }
    });
  }, 10000);

  chrome.runtime.sendMessage(
    { type: 'ANALYZE_DATA', payload },
    (response) => {
      clearInterval(keepAliveInterval); // Stop pinging once we get the real answer
      
      loadingMsg.remove();
      
      const responseMsg = document.createElement('div');
      responseMsg.className = 'obs-ai-message bot';
      
      if (chrome.runtime.lastError) {
        responseMsg.innerHTML = `<div class="obs-ai-error">Error: ${chrome.runtime.lastError.message}</div>`;
      } else if (response.error) {
        const errorText = typeof response.error === 'object' ? JSON.stringify(response.error) : response.error;
        responseMsg.innerHTML = `<div class="obs-ai-error">Backend Error: ${errorText}</div>`;
      } else {
        responseMsg.innerHTML = renderResultHtml(response.data);
      }
      
      chatBody.appendChild(responseMsg);
      chatBody.scrollTop = chatBody.scrollHeight;
    }
  );
}

function renderResultHtml(data) {
  const badgeClass = data.severity === 'high' ? 'high' : (data.severity === 'medium' ? 'medium' : 'low');
  
  let html = `
    <div>
      <span class="obs-ai-badge ${badgeClass}">${data.severity} SEVERITY</span>
    </div>
    <p style="font-size: 14px; font-weight: bold; margin: 0 0 8px 0;">${data.summary}</p>
    <p style="color: #e0e0e0; margin-bottom: 12px; font-size: 12px;"><strong>Root Cause:</strong> ${data.root_cause}</p>
  `;
  
  if (data.evidence && data.evidence.length > 0) {
    html += `
      <div class="obs-ai-section">
        <h4>Evidence</h4>
        <ul>
          ${data.evidence.map(e => `<li>${e}</li>`).join('')}
        </ul>
      </div>
    `;
  }
  
  if (data.recommendations && data.recommendations.length > 0) {
    html += `
      <div class="obs-ai-section">
        <h4>Recommendations</h4>
        <ul>
          ${data.recommendations.map(r => `<li>${r}</li>`).join('')}
        </ul>
      </div>
    `;
  }
  
  html += `
    <div style="margin-top: 12px; font-size: 10px; color: #666;">
      Model: ${data.model_used} | Processing Time: ${(data.processing_time_ms / 1000).toFixed(1)}s
    </div>
  `;
  
  return html;
}

function ensureUIExists() {
  if (!document.getElementById('obs-ai-extension-btn')) {
    createButton();
  }
}

// In Single Page Applications like Grafana/Kibana, the framework often destroys the DOM on load.
// We check every second to make sure our button stays on the screen.
setInterval(ensureUIExists, 1000);
ensureUIExists();
