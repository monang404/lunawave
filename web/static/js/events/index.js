function initEvents() {
    document.querySelectorAll(".mood-card").forEach(card => {
        card.addEventListener("click", () => {
            const mood = card.getAttribute("data-mood");
            if (mood && store.userRole === "admin") {
                switchTab("search");
                if (dom.searchInput) {
                    dom.searchInput.value = mood + " mix";
                    dom.searchInput.dispatchEvent(new Event("input"));
                }
            }
        });
    });

    if (dom.portalClientBtn) {
        dom.portalClientBtn.addEventListener("click", () => {
            store.userRole = "client";
            if (window.safeStorage) {
                window.safeStorage.set("ytgui_user_role", "client");
            } else {
                localStorage.setItem("ytgui_user_role", "client");
            }
            applyRoleUI();
            unlockBrowserAudio();
            syncBrowserAudio();
        });
    }

    if (dom.portalAdminBtn) {
        dom.portalAdminBtn.addEventListener("click", () => {
            if (dom.portalLoginForm) {
                dom.portalLoginForm.classList.toggle("hidden");
                if (!dom.portalLoginForm.classList.contains("hidden") && dom.adminUsername) {
                    dom.adminUsername.focus();
                }
            }
        });
    }

    if (dom.adminSubmitBtn) {
        dom.adminSubmitBtn.addEventListener("click", () => {
            const user = dom.adminUsername ? dom.adminUsername.value.trim() : "";
            const pass = dom.adminPassword ? dom.adminPassword.value : "";
            login(user, pass);
        });
    }

    if (dom.adminPassword) {
        dom.adminPassword.addEventListener("keypress", (e) => {
            if (e.key === "Enter" && dom.adminSubmitBtn) dom.adminSubmitBtn.click();
        });
    }

    if (dom.adminUsername) {
        dom.adminUsername.addEventListener("keypress", (e) => {
            if (e.key === "Enter" && dom.adminSubmitBtn) dom.adminSubmitBtn.click();
        });
    }

    if (dom.logoutBtn) {
        dom.logoutBtn.addEventListener("click", () => {
            logout();
        });
    }

    document.querySelectorAll(".nav-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            switchTab(btn.dataset.tab);
        });
    });

    initPlayerEvents();
    initQueueEvents();
    initQueueDragDrop();
    initLyricsEvents();
    initSettingsEvents();
}
