/**
 * Quiz countdown timer.
 * Starts from the remaining quiz time sent by the server.
 */
function startTimer(durationSeconds, displayElement, formElement) {
    let timeRemaining = durationSeconds;

    function updateDisplay() {
        const minutes = Math.floor(timeRemaining / 60);
        const seconds = timeRemaining % 60;
        displayElement.textContent =
            String(minutes).padStart(2, "0") + ":" +
            String(seconds).padStart(2, "0");

        if (timeRemaining <= 60) {
            displayElement.parentElement.classList.add("timer--warning");
        }
        if (timeRemaining <= 10) {
            displayElement.parentElement.classList.add("timer--critical");
        }
    }

    updateDisplay();

    const interval = setInterval(function () {
        timeRemaining--;

        if (timeRemaining <= 0) {
            clearInterval(interval);
            displayElement.textContent = "00:00";
            window.location.href = formElement.dataset.timeoutUrl || formElement.action;
        } else {
            updateDisplay();
        }
    }, 1000);
}
