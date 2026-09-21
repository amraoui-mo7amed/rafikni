/**
 * JavaScript interactions for activation success template.
 * Handles app scheme opening and navigation.
 */
document.addEventListener("DOMContentLoaded", function () {
    const appBtn = document.getElementById("btn-open-app");
    if (appBtn) {
        appBtn.addEventListener("click", function (e) {
            const appUrl = appBtn.getAttribute("data-app-url") || appBtn.getAttribute("href") || "rafikni://login";
            // Allow default navigation or trigger window location
            window.location.href = appUrl;
        });
    }
});
