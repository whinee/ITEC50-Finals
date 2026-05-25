const THEME_COOKIE = "theme";
const THEME_MAX_AGE = 60 * 60 * 24 * 180;

function getCookie(name) {
    return document.cookie
        .split("; ")
        .find((row) => row.startsWith(`${name}=`))
        ?.split("=")[1];
}

function normalizeTheme(theme) {
    return theme === "dark" ? "dark" : "light";
}

function setThemeCookie(theme) {
    document.cookie = `${THEME_COOKIE}=${theme}; Max-Age=${THEME_MAX_AGE}; Path=/; SameSite=Lax`;
}

function applyTheme(theme) {
    const normalized = normalizeTheme(theme);
    document.documentElement.dataset.theme = normalized;
    document.querySelectorAll('input[name="theme"]').forEach((input) => {
        input.checked = input.value === normalized;
    });
}

async function syncTheme(theme) {
    try {
        const response = await fetch("/api/settings/theme", {
            method: "PUT",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ theme }),
        });
        if (!response.ok) return;
        const data = await response.json();
        applyTheme(data.theme);
        setThemeCookie(normalizeTheme(data.theme));
    } catch {
        return;
    }
}

async function loadTheme() {
    applyTheme(getCookie(THEME_COOKIE));
    try {
        const response = await fetch("/api/settings/theme", {
            headers: { Accept: "application/json" },
        });
        if (!response.ok) return;
        const data = await response.json();
        applyTheme(data.theme);
        setThemeCookie(normalizeTheme(data.theme));
    } catch {
        return;
    }
}

document.querySelectorAll('input[name="theme"]').forEach((input) => {
    input.addEventListener("change", () => {
        const theme = normalizeTheme(input.value);
        applyTheme(theme);
        setThemeCookie(theme);
        syncTheme(theme);
    });
});

loadTheme();
