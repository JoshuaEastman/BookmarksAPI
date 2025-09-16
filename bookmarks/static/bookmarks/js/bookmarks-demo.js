// bookmarks/static/bookmarks/demo.js

(function () {
  const API_BASE = "/bookmarks/v1/bookmarks/";
  const SUBMIT_URL = "/bookmarks/v1/bookmarks/submit/";

  const ALLOWED_ORDERINGS = new Set(["-created_at", "created_at"]);

  // Timezone formatting (America/Chicago)
  const TIMEZONE = "America/Chicago";
  const DATE_FMT_OPTIONS = {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
    timeZone: TIMEZONE,
  };

  function formatInTZ(isoString) {
    if (!isoString) return "";
    try {
      const d = new Date(isoString);
      return new Intl.DateTimeFormat(undefined, DATE_FMT_OPTIONS).format(d);
    } catch {
      return isoString;
    }
  }

  // Elements
  const searchInput = document.getElementById("searchInput");
  const tagInput = document.getElementById("tagInput");
  const orderingSelect = document.getElementById("orderingSelect");
  const fetchBtn = document.getElementById("fetchBtn");
  const clearBtn = document.getElementById("clearBtn");
  const resultsInfo = document.getElementById("resultsInfo");
  const resultsList = document.getElementById("resultsList");
  const prevBtn = document.getElementById("prevBtn");
  const nextBtn = document.getElementById("nextBtn");

  const submitDialog = document.getElementById("submitDialog");
  const openSubmitModalBtn = document.getElementById("openSubmitModalBtn");
  const closeSubmitModalBtn = document.getElementById("closeSubmitModalBtn");
  const submitForm = document.getElementById("submitForm");
  const submitMsg = document.getElementById("submitMsg");

  let nextPage = null;
  let prevPage = null;
  let lastQuery = null;

  function qs(params) {
    const u = new URLSearchParams();
    if (params.search) u.set("search", params.search.trim());
    if (params.tag) u.set("tag", params.tag.trim());
    if (params.ordering) u.set("ordering", params.ordering);
    return u.toString();
  }

  async function fetchList(url) {
    resultsInfo.textContent = "Loading…";
    resultsList.innerHTML = "";
    prevBtn.disabled = true;
    nextBtn.disabled = true;

    try {
      const res = await fetch(url, { headers: { Accept: "application/json" } });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Request failed (${res.status})`);
      }
      const data = await res.json();

      nextPage = data.next;
      prevPage = data.previous;

      resultsInfo.textContent = `Found ${data.count ?? data.results?.length ?? 0} item(s).`;
      renderResults(data.results || []);

      prevBtn.disabled = !prevPage;
      nextBtn.disabled = !nextPage;
    } catch (e) {
      resultsInfo.textContent = e.message;
    }
  }

  function renderResults(items) {
    if (!items.length) {
      resultsList.innerHTML = `<div class="opacity-70">No results.</div>`;
      return;
    }

    const html = items
      .map((b) => {
        const tags = (b.tags || [])
          .map((t) => `<span class="badge badge-outline">${t}</span>`)
          .join(" ");
        return `
        <div class="card h-full bg-base-200 border border-base-300">
          <div class="card-body">
            <div class="flex items-start justify-between gap-3">
              <div>
                <a href="${b.url}" target="_blank" rel="noopener" class="link link-hover text-lg font-semibold">${b.title}</a>
                <div class="text-xs opacity-70">${b.domain || ""}</div>
              </div>
              <a href="${API_BASE}${b.id}/" class="btn btn-xs">API</a>
            </div>
            <p class="mt-2">${b.description ? escapeHTML(b.description) : ""}</p>
            <div class="mt-3 flex flex-wrap gap-2">${tags}</div>
            <div class="text-xs opacity-70 mt-2" title="${b.created_at}">
              Created: ${formatInTZ(b.created_at)} <span class="opacity-60">(CT)</span>
            </div>
          </div>
        </div>
      `;
      })
      .join("");
    resultsList.innerHTML = html;
  }

  function escapeHTML(s) {
    return String(s)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }

  function buildListURL(params) {
    const query = qs(params);
    lastQuery = `${API_BASE}?${query}`;
    return lastQuery;
  }

  // Events
  fetchBtn.addEventListener("click", () => {
    const selectedOrdering = ALLOWED_ORDERINGS.has(orderingSelect.value)
      ? orderingSelect.value
      : "-created_at";

    const url = buildListURL({
      search: searchInput.value,
      tag: tagInput.value,
      ordering: selectedOrdering,
    });
    fetchList(url);
  });

  clearBtn.addEventListener("click", () => {
    searchInput.value = "";
    tagInput.value = "";
    orderingSelect.value = "-created_at";
    resultsList.innerHTML = "";
    resultsInfo.textContent = "";
    prevBtn.disabled = true;
    nextBtn.disabled = true;
  });

  prevBtn.addEventListener("click", () => {
    if (prevPage) fetchList(prevPage);
  });

  nextBtn.addEventListener("click", () => {
    if (nextPage) fetchList(nextPage);
  });

  // Submit modal
  openSubmitModalBtn.addEventListener("click", () => submitDialog.showModal());
  closeSubmitModalBtn.addEventListener("click", () => submitDialog.close());

  submitForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    submitMsg.className = "text-sm";
    submitMsg.textContent = "Submitting…";

    const form = new FormData(submitForm);
    const payload = {
      title: form.get("title")?.trim(),
      url: form.get("url")?.trim(),
      description: form.get("description")?.trim() || "",
      tags: (form.get("tags") || "")
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      website: form.get("website") || "",
    };

    try {
      const res = await fetch(SUBMIT_URL, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg =
          data?.detail ||
          Object.values(data || {})
            .flat()
            .join(" ") ||
          `Submit failed (${res.status})`;
        throw new Error(msg);
      }

      const pt = (data.pending_tags || []).join(", ");
      submitMsg.className = "text-sm text-success";
      submitMsg.innerHTML = `Submitted! <br>Pending tags: <b>${pt || "None"}</b><br>Approved: <b>${
        data.is_approved ? "yes" : "no"
      }</b>`;

      if (lastQuery?.includes("ordering=-created_at")) fetchList(lastQuery);

      submitForm.reset();
    } catch (err) {
      submitMsg.className = "text-sm text-error";
      submitMsg.textContent = err.message;
    }
  });

  function getCSRFToken() {
    const name = "csrftoken";
    const cookies = document.cookie ? document.cookie.split("; ") : [];
    for (const c of cookies) {
      const [k, v] = c.split("=");
      if (k === name) return decodeURIComponent(v);
    }
    return "";
  }

  // Auto-load initial list
  fetchList(buildListURL({ ordering: "-created_at" }));
})();
