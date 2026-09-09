(function () {
    "use strict";

    function syncDogSizeAvailability(form) {
        const petSelect = form.querySelector("[data-pet-table-type]");
        const sizeSelect = form.querySelector(".pet-table-size-select");
        if (!petSelect || !sizeSelect) return;

        const isCat = petSelect.value === "cat";
        sizeSelect.disabled = isCat;
        sizeSelect.setAttribute("aria-disabled", String(isCat));
    }

    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll("[data-pet-table-form]").forEach((form) => {
            const petSelect = form.querySelector("[data-pet-table-type]");
            if (!petSelect) return;

            syncDogSizeAvailability(form);
            petSelect.addEventListener("change", () => syncDogSizeAvailability(form));
        });
    });
}());
