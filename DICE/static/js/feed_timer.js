document.addEventListener('DOMContentLoaded', function () {
    const submitButton = document.getElementById('submitButton');
    if (!submitButton) {
        return;
    }

    const showButtonAfterMs = 1 * 60 * 1000;
    const autoSubmitAfterMs = 3 * 60 * 1000;

    setTimeout(function () {
        submitButton.style.display = '';
    }, showButtonAfterMs);

    setTimeout(function () {
        submitButton.click();
    }, autoSubmitAfterMs);
});
