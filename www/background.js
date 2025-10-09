// Background service worker for LightRAG Preprocessor Extension

chrome.runtime.onInstalled.addListener(() => {
  console.log('LightRAG Preprocessor Extension installed');
});

// Handle extension icon click
chrome.action.onClicked.addListener((tab) => {
  // Open the extension popup
  chrome.action.openPopup();
});

// Handle messages from content scripts or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'openTab') {
    chrome.tabs.create({ url: request.url });
  }
  
  if (request.action === 'getActiveTab') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      sendResponse({ tab: tabs[0] });
    });
    return true; // Keep the message channel open for async response
  }
});