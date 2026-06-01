chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'PING') {
    sendResponse({ status: 'alive' });
    return false;
  }
  
  if (request.type === 'ANALYZE_DATA') {
    
    // Get settings from storage
    chrome.storage.local.get(['apiUrl', 'apiKey'], async (settings) => {
      const apiUrl = settings.apiUrl || 'http://localhost:8080';
      const apiKey = settings.apiKey || 'dev-key-change-me-in-production';
      
      try {
        // We use summarize_logs endpoint because we are passing scraped text lines
        const response = await fetch(`${apiUrl}/summarize_logs`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': apiKey
          },
          body: JSON.stringify(request.payload)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
          sendResponse({ error: data.detail || 'API request failed' });
        } else {
          sendResponse({ data: data });
        }
      } catch (err) {
        sendResponse({ error: err.message });
      }
    });
    
    // Return true to indicate we will send a response asynchronously
    return true; 
  }
});
