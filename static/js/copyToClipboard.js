function copyToClipboard(elementId, feedbackId) {
    const textElement = document.getElementById(elementId);
    const feedbackElement = document.getElementById(feedbackId);
    const text = textElement.textContent;

    navigator.clipboard.writeText(text).then(() => {
        if (feedbackElement) {
            feedbackElement.classList.add("show");
            setTimeout(() => {
                feedbackElement.classList.remove("show");
            }, 2000);
        }
    }).catch(err => {
        console.error("Fehler beim Kopieren:", err);
    });
}