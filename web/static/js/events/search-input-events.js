function initSearchInputEvents() {
    const searchClearBtn = document.getElementById("search-clear-btn");
    if (searchClearBtn) {
        searchClearBtn.addEventListener("click", () => {
            dom.searchInput.value = "";
            searchClearBtn.style.display = "none";
            dom.searchInput.dispatchEvent(new Event("input"));
            dom.searchInput.focus();
        });
    }

    const searchHeader = document.getElementById("search-header");
    if (searchHeader && dom.searchInput) {
        const updateSearchHeaderCollapse = () => {
            const hasValue = !!dom.searchInput.value.trim();
            const isFocused = document.activeElement === dom.searchInput;
            if (hasValue || isFocused) {
                searchHeader.classList.add("collapsed");
            } else {
                searchHeader.classList.remove("collapsed");
            }
        };
        dom.searchInput.addEventListener("input", updateSearchHeaderCollapse);
        dom.searchInput.addEventListener("focus", updateSearchHeaderCollapse);
        dom.searchInput.addEventListener("blur", updateSearchHeaderCollapse);
        updateSearchHeaderCollapse();
    }

    let searchTimer = null;
    let lastSearchQuery = "";
    if (dom.searchInput) {
        dom.searchInput.addEventListener("input", (e) => {
            if (searchClearBtn) searchClearBtn.style.display = e.target.value ? "block" : "none";
            const q = e.target.value.trim();
            if (searchTimer) clearTimeout(searchTimer);
            if (!q) {
                dom.searchMsg.textContent = "Ketik nama lagu atau artis";
                dom.searchMsg.style.display = "block";
                dom.searchResults.innerHTML = "";
                dom.searchResults.style.display = "none";
                lastSearchQuery = "";
                return;
            }
            if (q !== lastSearchQuery) {
                lastSearchQuery = q;
                searchTimer = setTimeout(() => {
                    dom.searchMsg.innerHTML = '<span class="spinner"></span> Mencari...';
                    dom.searchMsg.style.display = "block";
                    dom.searchResults.style.display = "none";
                    wsSend("search", { query: q });
                }, 500);
            }
        });

        dom.searchInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                const q = e.target.value.trim();
                if (q) {
                    if (searchTimer) clearTimeout(searchTimer);
                    lastSearchQuery = q;
                    dom.searchMsg.innerHTML = '<span class="spinner"></span> Mencari...';
                    dom.searchMsg.style.display = "block";
                    dom.searchResults.style.display = "none";
                    wsSend("search", { query: q });
                }
            }
        });
    }

    if (dom.searchResults) {
        dom.searchResults.addEventListener("click", (e) => {
            const item = e.target.closest(".sr-item");
            if (item && item.dataset.searchTrackStr) {
                try {
                    const track = JSON.parse(item.dataset.searchTrackStr);
                    if (typeof playSearchTrack === "function") playSearchTrack(track);
                } catch (err) {
                    console.error("Invalid track data", err);
                }
            }
        });
    }
}
