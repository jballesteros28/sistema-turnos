document.documentElement.classList.add("agenda-js");

document.addEventListener("DOMContentLoaded", () => {
    const presets = {
        weekdays: ["0", "1", "2", "3", "4"],
        "week-saturday": ["0", "1", "2", "3", "4", "5"],
        all: ["0", "1", "2", "3", "4", "5", "6"],
        clear: [],
    };

    document.querySelectorAll("[data-weekday-picker]").forEach((picker) => {
        const checkboxes = Array.from(
            picker.querySelectorAll('input[type="checkbox"][name="dias_semana"]')
        );

        picker.querySelectorAll("[data-day-preset]").forEach((button) => {
            button.addEventListener("click", () => {
                const selectedDays = presets[button.dataset.dayPreset] || [];
                checkboxes.forEach((checkbox) => {
                    checkbox.checked = selectedDays.includes(checkbox.value);
                });
            });
        });
    });
});
