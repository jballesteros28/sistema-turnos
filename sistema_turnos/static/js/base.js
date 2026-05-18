(() => {
    const body = document.body;
    const copyButtons = document.querySelectorAll("[data-copy-text]");
    const sidebar = document.querySelector("[data-sidebar]");
    const toggle = document.querySelector("[data-sidebar-toggle]");
    const closeControls = document.querySelectorAll("[data-sidebar-close]");
    const pageTitle = document.querySelector("[data-page-title]");
    const contentTitle = document.querySelector(".page-header h1, main h1");

    const copyText = (text) => {
        if (navigator.clipboard && window.isSecureContext) {
            return navigator.clipboard.writeText(text);
        }

        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "fixed";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();

        try {
            document.execCommand("copy");
            return Promise.resolve();
        } catch (error) {
            return Promise.reject(error);
        } finally {
            textarea.remove();
        }
    };

    copyButtons.forEach((button) => {
        const label = button.querySelector("[data-copy-label]") || button;
        const originalText = label.textContent;

        button.addEventListener("click", () => {
            const value = button.getAttribute("data-copy-text") || "";
            if (!value) {
                return;
            }

            copyText(value)
                .then(() => {
                    label.textContent = "Copiado";
                })
                .catch(() => {
                    label.textContent = "No se pudo copiar";
                })
                .finally(() => {
                    window.setTimeout(() => {
                        label.textContent = originalText;
                    }, 1800);
                });
        });
    });

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
