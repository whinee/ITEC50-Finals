const validators = {
    identifier: (val) => {
        if (!val) return { ok: false, msg: "This field is required." };
        const isEmail = val.includes("@");
        if (isEmail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val))
            return {
                ok: false,
                msg: "Looks like an email but it's not valid.",
            };
        if (!isEmail && val.length < 3)
            return {
                ok: false,
                msg: "Username must be at least 3 characters.",
            };
        return { ok: true, msg: "Looks good!" };
    },
    email: (val) => {
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) {
            return {
                ok: false,
                msg: "Invalid E-mail.",
            };
        }
        return { ok: true, msg: "Looks good!" };
    },
    username: (val) => {
        if (val.length < 3)
            return {
                ok: false,
                msg: "Username must be at least 3 characters.",
            };
        return { ok: true, msg: "Looks good!" };
    },
    password: (val) => {
        if (!val) return { ok: false, msg: "This field is required." };
        if (val.length < 8)
            return {
                ok: false,
                msg: "Password must be at least 8 characters.",
            };
        return { ok: true, msg: "Looks good!" };
    },
};

document.querySelectorAll(".field").forEach((field) => {
    const formBox = field.querySelector(".form-box");
    const input = formBox.querySelector(".input");
    const eraseInputButton = formBox.querySelector(".erase-input");
    const validationMessage = field.querySelector(".validation-msg");

    function validate() {
        const val = input.value;
        eraseInputButton.style.visibility = val ? "visible" : "hidden";

        if (!val) {
            validationMessage.textContent = "";
            input.classList.remove("valid", "invalid");
            return;
        }

        const result = validators[input.name]?.(val) ?? { ok: true, msg: "" };
        input.classList.toggle("valid", result.ok);
        input.classList.toggle("invalid", !result.ok);

        validationMessage.textContent = result.msg;
        validationMessage.className =
            "validation-msg" + (result.ok ? " ok" : "");
    }

    if (validationMessage) {
        input.addEventListener("input", validate);
    }

    eraseInputButton.addEventListener("click", () => {
        input.value = "";
        input.classList.remove("valid", "invalid");
        eraseInputButton.style.visibility = "hidden";
        if (validationMessage) {
            validationMessage.textContent = "";
        }
        input.focus();
    });
});
