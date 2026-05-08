(() => {
    const dashboard = document.querySelector("[data-dashboard]");

    if (!dashboard) {
        return;
    }

    dashboard.dataset.ready = "true";
})();
