document.addEventListener("DOMContentLoaded", function () {
    var page = document.querySelector("[data-color-primario]");
    if (!page) {
        return;
    }

    var color = (page.getAttribute("data-color-primario") || "").trim();
    if (/^#[0-9a-fA-F]{6}$/.test(color)) {
        document.documentElement.style.setProperty("--reservas-primary", color);
    }
});
