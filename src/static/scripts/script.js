function disableSubmit(parent) {
    if (parent.checkValidity()) {
        parent.querySelector("button").disabled = false;
    } else {
        parent.querySelector("button").disabled = true;
    }
}

function inputFn() {
    disableSubmit(this.parentNode);
    if (this.value != '') {
        if (this.checkValidity()) {
            this.classList.add("valid");
            this.classList.remove("invalid");
        } else {
            this.classList.add("invalid");
            this.classList.remove("valid");
        }
    } else {
        this.classList.remove("valid");
        this.classList.remove("invalid");
    }
}

for (let i of document.querySelectorAll('.vi')) {
    disableSubmit(i.parentNode);
    i.addEventListener('input', inputFn);
}

function SetOpa(Opa) {
    element.style.opacity = Opa;
    // Code for older browsers below
    element.style.MozOpacity = Opa;
    element.style.KhtmlOpacity = Opa;
    element.style.filter = 'alpha(opacity=' + (Opa * 100) + ');';
}

function fadeOut() {
    for (i = 0; i <= 1; i += 0.01) {
        setTimeout("SetOpa(" + (1 - i) + ")", i * duration);
    }
    setTimeout("fadeIn()", (duration + hidtime));
}

function fadeToggle() {
    for (let j of document.getElementsByTagName('form')) {
        if (window.getComputedStyle(j).display == 'none') {
            j.style.display = 'block';
        } else {
            j.style.display = 'none';
        }
    }
}

for (let i of document.querySelectorAll('.message a')) {
    i.addEventListener('click', fadeToggle)
}