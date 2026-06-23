document.addEventListener('DOMContentLoaded', function () {
    const submitButton = document.getElementById('submitButton');
    if (!submitButton) {
        return;
    }

    const showButtonAfterMs = 1 * 60 * 1000;
    const autoSubmitAfterMs = 3 * 60 * 1000;

    setTimeout(function () {
        submitButton.style.display = '';
        if (window.feedInteractionGate && typeof window.feedInteractionGate.setProceedVisible === 'function') {
            window.feedInteractionGate.setProceedVisible(true);
        }
    }, showButtonAfterMs);

    setTimeout(function () {
        if (window.feedInteractionGate && typeof window.feedInteractionGate.hasMinimumInteractions === 'function') {
            window.feedInteractionGate.setProceedVisible(true);
            if (window.feedInteractionGate.hasMinimumInteractions()) {
                submitButton.click();
            }
            return;
        }

        submitButton.click();
    }, autoSubmitAfterMs);
});
