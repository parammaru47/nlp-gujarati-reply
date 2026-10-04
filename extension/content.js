// content.js
console.log("Gujarati Smart Reply Extension Loaded.");

function getLastReceivedMessage() {
    let lastText = "";
    const dataIdMsgs = Array.from(document.querySelectorAll("div[data-id^=\"false_\"]"));
    if (dataIdMsgs.length > 0) {
        const lastMsg = dataIdMsgs[dataIdMsgs.length - 1];
        let textSpan = lastMsg.querySelector("span.copyable-text") || lastMsg.querySelector("span.selectable-text[dir=\"ltr\"]");
        if (textSpan) {
            lastText = textSpan.innerText.trim();
        } else {
            const spans = Array.from(lastMsg.querySelectorAll("span[dir=\"ltr\"]"));
            if (spans.length > 0) {
                const longest = spans.reduce((a, b) => a.innerText.length > b.innerText.length ? a : b);
                lastText = longest.innerText.trim();
            } else {
                lastText = lastMsg.innerText.trim();
            }
        }
        lastText = lastText.replace(/\d{1,2}:\d{2}\s*(am|pm|AM|PM)?$/, "").trim();
    }
    return lastText || "UI_FORCE_SHOW";
}

function fetchSuggestions(messageText) {
    return new Promise((resolve) => {
        try {
            chrome.runtime.sendMessage({ action: "fetchSuggestions", message: messageText }, (response) => {
                if (chrome.runtime.lastError) {
                    console.warn("Error sending:", chrome.runtime.lastError);
                    resolve([
                        { text: "હા, બરાબર છે.", isDeflect: false },
                        { text: "હું થોડીવારમાં ફોન કરું.", isDeflect: false },
                        { text: "અહીં કહેવું મુશ્કેલ છે.", isDeflect: true }
                    ]);
                } else if (response && response.replies) {
                    resolve(response.replies);
                } else {
                    resolve([
                        { text: "હા, બરાબર છે.", isDeflect: false },
                        { text: "હું થોડીવારમાં ફોન કરું.", isDeflect: false },
                        { text: "અહીં કહેવું મુશ્કેલ છે.", isDeflect: true }
                    ]);
                }
            });
        } catch (e) {
            resolve([
                { text: "હા, બરાબર છે.", isDeflect: false },
                { text: "હું થોડીવારમાં ફોન કરું.", isDeflect: false },
                { text: "અહીં કહેવું મુશ્કેલ છે.", isDeflect: true }
            ]);
        }
    });
}

function getChatInput() {
    return document.querySelector("#main div[contenteditable=\"true\"]") ||
        document.querySelector("#main footer div[contenteditable=\"true\"]") ||
        document.querySelector("div[title=\"Type a message\"]");
}

function getChatFooter() {
    return document.querySelector("#main footer") || document.querySelector("footer");
}

function handleSuggestionClick(suggestionText) {
    const inputEl = getChatInput();
    if (!inputEl) return;
    inputEl.focus();
    const success = document.execCommand("insertText", false, suggestionText);
    if (!success) {
        const dataTransfer = new DataTransfer();
        dataTransfer.setData("text/plain", suggestionText);
        const clipboardEvent = new ClipboardEvent("paste", {
            clipboardData: dataTransfer, bubbles: true, cancelable: true
        });
        inputEl.dispatchEvent(clipboardEvent);
    }
    setTimeout(() => {
        const enterEvent = new KeyboardEvent("keydown", {
            bubbles: true, cancelable: true, key: "Enter", code: "Enter", keyCode: 13, which: 13
        });
        inputEl.dispatchEvent(enterEvent);
        const sendBtnIcon = document.querySelector("span[data-icon=\"send\"]");
        if (sendBtnIcon) {
            const sendBtn = sendBtnIcon.closest("button") || sendBtnIcon.parentElement;
            if (sendBtn) sendBtn.click();
        }
    }, 100);
}

let isInjecting = false;
let lastProcessedMessage = null;

async function injectReplyChips() {
    if (isInjecting) return;
    const footer = getChatFooter();
    if (!footer) return;

    const currentMessage = getLastReceivedMessage();
    if (!currentMessage) return;

    const existingContainer = footer.querySelector(".smart-reply-container");
    if (existingContainer && lastProcessedMessage === currentMessage) return;

    isInjecting = true;
    try {
        console.log(`Generating replies for: "${currentMessage}"`);
        const suggestions = await fetchSuggestions(currentMessage);

        lastProcessedMessage = currentMessage;

        const currentFooter = getChatFooter();
        if (!currentFooter) return;

        let container = currentFooter.querySelector(".smart-reply-container");
        if (!container) {
            currentFooter.style.position = "relative";
            currentFooter.style.paddingTop = "80px";
            container = document.createElement("div");
            container.className = "smart-reply-container";
            currentFooter.appendChild(container);
        } else {
            container.innerHTML = "";
        }

        // Render Chips safely
        suggestions.forEach(suggestionObj => {
            const textValue = typeof suggestionObj === "string" ? suggestionObj : suggestionObj.text;
            const deflect = typeof suggestionObj === "object" && suggestionObj.isDeflect;

            const chip = document.createElement("button");
            chip.className = "smart-reply-chip";
            if (deflect) {
                chip.classList.add("deflect-chip");
            }
            chip.textContent = textValue;
            chip.addEventListener("mousedown", (e) => e.preventDefault());
            chip.addEventListener("click", () => {
                handleSuggestionClick(textValue);
            });
            container.appendChild(chip);
        });
    } finally {
        isInjecting = false;
    }
}

let pollingInterval = null;
const observer = new MutationObserver(() => injectReplyChips());

window.addEventListener("load", () => {
    observer.observe(document.body, { childList: true, subtree: true });
    pollingInterval = setInterval(() => injectReplyChips(), 2000);
});

