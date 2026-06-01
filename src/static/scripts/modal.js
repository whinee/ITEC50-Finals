import { bodyScrollPrevent } from "/static/scripts/utils.js";

// Constants
const modals = ["settings", "info"];

// Document Selectors
const closeModal = document.getElementById("close-modal");
const modalArea = document.getElementById("modal-area");
const modalBg = document.querySelector(".modal-bg");

for (let i of modals) {
    const iBtn = document.getElementById(`${i}-modal-button`);
    const iModal = document.getElementById(`${i}-modal`);

    iBtn.addEventListener("click", function () {
        modalArea.classList.add("is-show");
        iModal.classList.add("is-show");
        bodyScrollPrevent(true);
    });

    for (let j of [closeModal, modalBg]) {
        j.addEventListener("click", function () {
            modalArea.classList.remove("is-show");
            iModal.classList.remove("is-show");
            bodyScrollPrevent(false, modalArea);
        });
    }
}
