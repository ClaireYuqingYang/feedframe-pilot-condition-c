document.addEventListener('DOMContentLoaded', function () {
    const submitButton = document.getElementById('submitButton');
    if (!submitButton) {
        return;
    }

    const showButtonAfterMs = 2 * 60 * 1000;
    const autoSubmitAfterMs = 4 * 60 * 1000;

    setTimeout(function () {
        submitButton.style.display = '';
    }, showButtonAfterMs);

    setTimeout(function () {
        submitButton.click();
    }, autoSubmitAfterMs);
});
