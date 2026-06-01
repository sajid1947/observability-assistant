document.addEventListener('DOMContentLoaded', () => {
  // Load existing settings
  chrome.storage.local.get(['apiUrl', 'apiKey'], (result) => {
    if (result.apiUrl) document.getElementById('apiUrl').value = result.apiUrl;
    if (result.apiKey) document.getElementById('apiKey').value = result.apiKey;
    
    // Set default API key if empty for easy demo
    if (!result.apiKey) document.getElementById('apiKey').value = 'dev-key-change-me-in-production';
  });

  // Save settings
  document.getElementById('saveBtn').addEventListener('click', () => {
    const apiUrl = document.getElementById('apiUrl').value;
    const apiKey = document.getElementById('apiKey').value;

    chrome.storage.local.set({ apiUrl, apiKey }, () => {
      const status = document.getElementById('status');
      status.style.display = 'block';
      setTimeout(() => {
        status.style.display = 'none';
      }, 2000);
    });
  });
});
