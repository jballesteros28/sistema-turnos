(() => {
    const body = document.body;
    const sidebar = document.querySelector("[data-sidebar]");
    const toggle = document.querySelector("[data-sidebar-toggle]");
    const closeControls = document.querySelectorAll("[data-sidebar-close]");
    const pageTitle = document.querySelector("[data-page-title]");
    const contentTitle = document.querySelector(".page-header h1, main h1");

    if (pageTitle && contentTitle) {
        pageTitle.textContent = contentTitle.textContent.trim();
    }

    if (!sidebar || !toggle) {
        return;
    }

    body.classList.add("has-sidebar-js");

    const setOpen = (isOpen) => {
        body.classList.toggle("sidebar-open", isOpen);
        toggle.setAttribute("aria-expanded", String(isOpen));
    };

    toggle.addEventListener("click", () => {
        setOpen(!body.classList.contains("sidebar-open"));
    });

    closeControls.forEach((control) => {
        control.addEventListener("click", () => setOpen(false));
    });

    sidebar.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => {
            if (window.innerWidth <= 1100) {
                setOpen(false);
            }
        });
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            setOpen(false);
        }
    });

    window.addEventListener("resize", () => {
        if (window.innerWidth > 1100) {
            setOpen(false);
        }
    });
})();
