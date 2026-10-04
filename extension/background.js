// background.js

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "fetchSuggestions") {
        fetch('http://127.0.0.1:5000/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: request.message })
        })
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                if (data && data.replies) {
                    sendResponse({ replies: data.replies });
                } else {
                    sendResponse({ replies: null });
                }
            })
            .catch(error => {
                console.warn("API not accessible or failed:", error);
                sendResponse({ replies: null, error: error.message });
            });

        return true; // Indicates async response
    }
});
