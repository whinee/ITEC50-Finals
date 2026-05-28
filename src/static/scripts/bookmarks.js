const API = {
    list: "/api/bookmarks",
    create: "/api/bookmarks",
    search: "/api/bookmarks/search",
    edit: "/api/bookmarks",
};

const root = document.querySelector("[data-bookmarks-page]");
const page = root?.dataset.bookmarksPage;

async function requestJson(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: { Accept: "application/json", ...(options.headers || {}) },
        });

        if (!response.ok) {
            throw new Error(`Request failed: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        return null;
    }
}

window.TagColorMap = new Map();
async function fetchTagColors() {
    const tags = await requestJson("/api/tags");
    if (Array.isArray(tags)) {
        tags.forEach((t) =>
            window.TagColorMap.set(t.title.toLowerCase(), {
                color: t.color,
                id: t.id,
            }),
        );
    }
}

function hexToHSL(hex) {
    let r = 0,
        g = 0,
        b = 0;
    if (hex.length === 4) {
        r = "0x" + hex[1] + hex[1];
        g = "0x" + hex[2] + hex[2];
        b = "0x" + hex[3] + hex[3];
    } else if (hex.length === 7) {
        r = "0x" + hex[1] + hex[2];
        g = "0x" + hex[3] + hex[4];
        b = "0x" + hex[5] + hex[6];
    }
    r /= 255;
    g /= 255;
    b /= 255;
    let cmin = Math.min(r, g, b),
        cmax = Math.max(r, g, b),
        delta = cmax - cmin,
        h = 0,
        s = 0,
        l = 0;

    if (delta == 0) h = 0;
    else if (cmax == r) h = ((g - b) / delta) % 6;
    else if (cmax == g) h = (b - r) / delta + 2;
    else h = (r - g) / delta + 4;

    h = Math.round(h * 60);
    if (h < 0) h += 360;
    l = (cmax + cmin) / 2;
    s = delta == 0 ? 0 : delta / (1 - Math.abs(2 * l - 1));
    s = +(s * 100).toFixed(1);
    l = +(l * 100).toFixed(1);
    return { h, s, l };
}

function applyTagColor(element, tagTitle) {
    const tagInfo = window.TagColorMap.get(tagTitle.toLowerCase());
    if (tagInfo && tagInfo.color) {
        const { h, s, l } = hexToHSL(tagInfo.color);
        element.style.setProperty("--tag-fg", tagInfo.color);
        // Make background a very faded version of the foreground
        element.style.setProperty("--tag-bg", `hsla(${h}, ${s}%, ${l}%, 0.15)`);

        // Add a click listener for the color picker if in edit mode, or just as a general feature
        element.dataset.tagId = tagInfo.id;
    }
}

async function getBookmarks() {
    const data = await requestJson(API.list);
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.bookmarks)) return data.bookmarks;
    return [];
}

function normalizeBookmark(bookmark) {
    const tags = Array.isArray(bookmark.tags)
        ? bookmark.tags
        : String(bookmark.tags || "")
              .split(",")
              .map((tag) => tag.trim())
              .filter(Boolean);

    const jdIds = Array.isArray(bookmark.jdIds)
        ? bookmark.jdIds
        : String(
              bookmark.jdIds ||
                  bookmark.jd_ids ||
                  bookmark.jdId ||
                  bookmark.jd_id ||
                  bookmark.jd ||
                  "",
          )
              .split(",")
              .map((jd) => jd.trim())
              .filter(Boolean);

    return {
        ...bookmark,
        jdIds,
        tags,
    };
}

function renderBookmarkCard(bookmark) {
    const item = normalizeBookmark(bookmark);
    const article = document.createElement("article");
    article.className = "bookmark-card";

    const heading = document.createElement("h3");
    const link = document.createElement("a");
    link.href = item.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = item.title;
    heading.append(link);

    const meta = document.createElement("div");
    meta.className = "bookmark-meta";

    const editLink = document.createElement("a");
    editLink.className = "pill edit-pill";
    editLink.href = `/bookmarks/edit?id=${item.id}`;
    editLink.textContent = "Edit";
    editLink.style.marginLeft = "auto";
    meta.append(editLink);

    item.jdIds.forEach((jd) => {
        const jdLink = document.createElement("a");
        jdLink.className = "pill";
        jdLink.href = `/bookmarks/jd?jdId=${encodeURIComponent(jd)}`;
        jdLink.textContent = jd;
        meta.append(jdLink);
    });

    const date = document.createElement("span");
    const rawDate = item.createdAt || item.created_at;
    if (rawDate) {
        let safeDate = rawDate.replace(" ", "T");
        if (
            !safeDate.endsWith("Z") &&
            !safeDate.includes("+") &&
            safeDate.indexOf("-", 11) === -1
        ) {
            safeDate += "Z";
        }
        const d = new Date(safeDate);
        date.textContent = d.toLocaleString(undefined, {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    } else {
        date.textContent = "";
    }
    meta.append(date);

    const tagRow = document.createElement("div");
    tagRow.className = "tag-row";
    item.tags.forEach((tag) => {
        const tagLink = document.createElement("a");
        tagLink.className = "tag-pill";
        tagLink.href = `/bookmarks/tag?tag=${encodeURIComponent(tag)}`;
        tagLink.textContent = "#" + tag;

        // Apply dynamic color
        if (window.TagColorMap && window.TagColorMap.has(tag.toLowerCase())) {
            applyTagColor(tagLink, tag);
        }

        tagRow.append(tagLink);
    });

    article.append(heading, meta, tagRow);

    if (item.notes) {
        const notes = document.createElement("p");
        notes.textContent = item.notes;
        article.append(notes);
    }

    return article;
}

function renderList(container, bookmarks) {
    if (!container) return;
    container.replaceChildren();

    if (!bookmarks.length) {
        const empty = document.createElement("div");
        empty.className = "empty-state";
        empty.textContent = "nothing here. sowwyyy :C ";
        container.append(empty);
        return;
    }

    bookmarks.forEach((bookmark) =>
        container.append(renderBookmarkCard(bookmark)),
    );
}

function renderSkeletonList(container, count = 3) {
    if (!container) return;
    container.replaceChildren();

    for (let i = 0; i < count; i++) {
        const card = document.createElement("article");
        card.className = "bookmark-card glass-panel";

        const title = document.createElement("h3");
        title.className = "skeleton";
        title.style.height = "1.5rem";
        title.style.width = "60%";
        title.style.marginBottom = "var(--space-2xs)";

        const meta = document.createElement("div");
        meta.className = "bookmark-meta skeleton";
        meta.style.height = "1rem";
        meta.style.width = "40%";
        meta.style.marginBottom = "var(--space-xs)";

        const tags = document.createElement("div");
        tags.className = "bookmark-tags skeleton";
        tags.style.height = "1.5rem";
        tags.style.width = "80%";

        card.append(title, meta, tags);
        container.append(card);
    }
}

function countValues(bookmarks, key) {
    const values = new Set();
    bookmarks.map(normalizeBookmark).forEach((bookmark) => {
        if (key === "tags" || key === "jdIds") {
            (bookmark[key] || []).forEach((item) => values.add(item));
        } else if (bookmark[key]) {
            values.add(bookmark[key]);
        }
    });
    return values;
}

function renderFilterLinks(container, values, baseUrl, queryKey) {
    if (!container) return;
    container.replaceChildren();
    [...values].sort().forEach((value) => {
        const link = document.createElement("a");
        link.className = queryKey === "tag" ? "tag-pill" : "pill";
        link.href = `${baseUrl}?${queryKey}=${encodeURIComponent(value)}`;
        link.textContent = value;
        container.append(link);
    });
}

async function initDashboard() {
    await fetchTagColors();
    const bookmarks = (await getBookmarks()).map(normalizeBookmark);
    const jdIds = countValues(bookmarks, "jdIds");
    const tags = countValues(bookmarks, "tags");

    const statTotal = document.querySelector("#stat-total");
    const statJds = document.querySelector("#stat-jds");
    const statTags = document.querySelector("#stat-tags");

    statTotal.textContent = bookmarks.length;
    statJds.textContent = jdIds.size;
    statTags.textContent = tags.size;

    statTotal.classList.remove("skeleton");
    statJds.classList.remove("skeleton");
    statTags.classList.remove("skeleton");

    renderList(
        document.querySelector("#recent-bookmarks"),
        bookmarks.slice(0, 5),
    );
    renderFilterLinks(
        document.querySelector("#jd-list"),
        jdIds,
        "/bookmarks/jd",
        "jdId",
    );
    renderFilterLinks(
        document.querySelector("#tag-list"),
        tags,
        "/bookmarks/tag",
        "tag",
    );
}

async function initAddForm() {
    document
        .querySelector("#bookmark-form")
        ?.addEventListener("submit", async (event) => {
            event.preventDefault();
            const form = event.currentTarget;
            const formData = new FormData(form);
            const payload = {
                title: formData.get("title"),
                url: formData.get("url"),
                jdIds: String(formData.get("jdIds") || "")
                    .split(",")
                    .map((jd) => jd.trim())
                    .filter(Boolean),
                tags: String(formData.get("tags") || "")
                    .split(",")
                    .map((tag) => tag.trim())
                    .filter(Boolean),
                notes: formData.get("notes"),
            };

            const result = await requestJson(API.create, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            if (window.toast) {
                toast({
                    title: result ? "Saved" : "Not saved",
                    message: result
                        ? "Bookmark saved."
                        : "Please log in and try again.",
                    type: result ? "success" : "error",
                });
            }

            if (result) form.reset();
        });
}

async function initEditForm() {
    const form = document.querySelector("#bookmark-form");
    if (!form) return;

    const params = new URLSearchParams(window.location.search);
    const id = params.get("id");
    if (!id) {
        window.location.href = "/bookmarks/dashboard";
        return;
    }

    const bookmarks = await getBookmarks();
    const bookmark = bookmarks.find((b) => String(b.id) === id);
    if (!bookmark) {
        window.location.href = "/bookmarks/dashboard";
        return;
    }

    const item = normalizeBookmark(bookmark);
    form.elements.title.value = item.title;
    form.elements.url.value = item.url;
    form.elements.jdIds.value = item.jdIds.join(", ");
    form.elements.tags.value = item.tags.join(", ");
    form.elements.notes.value = item.notes || "";

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(form);
        const payload = {
            title: formData.get("title"),
            url: formData.get("url"),
            jdIds: String(formData.get("jdIds") || "")
                .split(",")
                .map((jd) => jd.trim())
                .filter(Boolean),
            tags: String(formData.get("tags") || "")
                .split(",")
                .map((tag) => tag.trim())
                .filter(Boolean)
                .join(", "),
            notes: formData.get("notes"),
        };

        const result = await requestJson(`${API.edit}/${id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (window.toast) {
            toast({
                title: result ? "Updated" : "Not updated",
                message: result
                    ? "Bookmark updated successfully."
                    : "Please log in and try again.",
                type: result ? "success" : "error",
            });
        }

        if (result) {
            setTimeout(() => {
                window.location.href = "/bookmarks/dashboard";
            }, 1500);
        }
    });
}

function filterBookmarks(bookmarks, filters, matchAll = true) {
    const active = Object.entries(filters).filter(([, value]) => value);
    if (!active.length) return bookmarks;

    return bookmarks.filter((bookmark) => {
        const item = normalizeBookmark(bookmark);
        const checks = active.map(([key, value]) => {
            const needle = value.toLowerCase();
            if (key === "tag")
                return item.tags.some((tag) =>
                    tag.toLowerCase().includes(needle),
                );
            if (key === "title")
                return item.title.toLowerCase().includes(needle);
            if (key === "jdId")
                return item.jdIds.some((jd) =>
                    jd.toLowerCase().includes(needle),
                );
            return false;
        });
        return matchAll ? checks.every(Boolean) : checks.some(Boolean);
    });
}

async function initSearch() {
    const form = document.querySelector("#bookmark-search-form");
    const results = document.querySelector("#search-results");

    renderSkeletonList(results);
    await fetchTagColors();
    const bookmarks = (await getBookmarks()).map(normalizeBookmark);
    renderList(results, bookmarks);

    form?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(form);
        const filters = {
            jdId: String(formData.get("jdId") || "").trim(),
            tag: String(formData.get("tag") || "").trim(),
            title: String(formData.get("title") || "").trim(),
        };
        const params = new URLSearchParams(filters);
        params.set("matchAll", formData.get("matchAll") ? "true" : "false");

        renderSkeletonList(results);
        const remote = await requestJson(`${API.search}?${params.toString()}`);
        const source = Array.isArray(remote) ? remote : bookmarks;
        renderList(
            results,
            filterBookmarks(source, filters, Boolean(formData.get("matchAll"))),
        );
    });
}

async function initFilteredView(type) {
    const params = new URLSearchParams(window.location.search);
    const key = type === "jd" ? "jdId" : "tag";
    const value = params.get(key) || "";
    const input = document.querySelector(`#${type}-filter-input`);
    const form = document.querySelector(`#${type}-filter-form`);
    const results = document.querySelector(`#${type}-results`);
    const title = document.querySelector("#view-title");

    renderSkeletonList(results);
    await fetchTagColors();
    const bookmarks = (await getBookmarks()).map(normalizeBookmark);

    if (input) input.value = value;

    const load = async (nextValue) => {
        const filters =
            type === "jd" ? { jdId: nextValue } : { tag: nextValue };
        title.textContent = nextValue
            ? `Bookmarks for ${nextValue}`
            : title.textContent;

        renderSkeletonList(results);
        const remote = await requestJson(API.list);
        const source = Array.isArray(remote)
            ? remote.map(normalizeBookmark)
            : bookmarks;

        renderList(results, filterBookmarks(source, filters, true));
    };

    load(value);

    form?.addEventListener("submit", (event) => {
        event.preventDefault();
        const nextValue = String(new FormData(form).get(key) || "").trim();
        history.replaceState(
            null,
            "",
            `?${key}=${encodeURIComponent(nextValue)}`,
        );
        load(nextValue);
    });
}

if (page === "dashboard") initDashboard();
if (page === "add") initAddForm();
if (page === "edit") initEditForm();
if (page === "search") initSearch();
if (page === "jd") initFilteredView("jd");
if (page === "tag") initFilteredView("tag");

window.exportTheme = async function () {
    try {
        const response = await fetch("/api/bookmarks/tags/export");
        const data = await response.json();
        prompt("Copy this Base64 Theme string:", data.theme_data);
    } catch (e) {
        alert("Failed to export theme.");
    }
};

window.importTheme = async function () {
    const themeStr = prompt("Paste your Base64 Theme string here:");
    if (!themeStr) return;
    try {
        const response = await fetch("/api/bookmarks/tags/import", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ theme_data: themeStr }),
        });
        if (response.ok) {
            alert("Theme imported successfully!");
            window.location.reload();
        } else {
            alert("Failed to import theme.");
        }
    } catch (e) {
        alert("Failed to import theme.");
    }
};
