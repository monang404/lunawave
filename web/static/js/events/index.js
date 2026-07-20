function initEvents() {
    document.querySelectorAll(".mood-card").forEach(card => {
        card.addEventListener("click", () => {
            const mood = card.getAttribute("data-mood");
            if (mood && store.userRole === "admin") {
                if (typeof switchTab === "function") switchTab("search");
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
                window.safeStorage.set("lunawave_user_role", "client");
            } else {
                localStorage.setItem("lunawave_user_role", "client");
            }
            if (typeof applyRoleUI === "function") applyRoleUI();
            if (typeof unlockBrowserAudio === "function") unlockBrowserAudio();
            if (typeof syncBrowserAudio === "function") syncBrowserAudio();
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
            if (typeof login === 'function') {
                login(user, pass);
            }
        });
    }

    if (dom.adminPassword) {
        dom.adminPassword.addEventListener("keypress", (e) => {
            if (e.key === "Enter" && dom.adminSubmitBtn) dom.adminSubmitBtn.click();
        });
    }

    // T-B12.1: submit #setup-screen disabled sampai Password == Confirm
    // Password. Dicek tiap kali salah satu field diketik (bukan cuma saat
    // submit), supaya user tau mismatch-nya SEBELUM klik tombol.
    if (dom.setupPassword) {
        dom.setupPassword.addEventListener("input", updateSetupSubmitState);
    }
    if (dom.setupConfirmPassword) {
        dom.setupConfirmPassword.addEventListener("input", updateSetupSubmitState);
        dom.setupConfirmPassword.addEventListener("keypress", (e) => {
            if (e.key === "Enter" && dom.setupSubmitBtn && !dom.setupSubmitBtn.disabled) {
                dom.setupSubmitBtn.click();
            }
        });
    }
    // Set state awal (kedua field kosong dianggap "match" -- submitSetup()
    // sendiri yang menolak field kosong lewat pesan generiknya sendiri).
    updateSetupSubmitState();

    if (dom.setupSubmitBtn) {
        dom.setupSubmitBtn.addEventListener("click", () => {
            const user = dom.setupUsername ? dom.setupUsername.value.trim() : "";
            const pass = dom.setupPassword ? dom.setupPassword.value : "";
            const confirmPass = dom.setupConfirmPassword ? dom.setupConfirmPassword.value : "";
            if (typeof submitSetup === "function") {
                submitSetup(user, pass, confirmPass);
            }
        });
    }

    if (dom.logoutBtn) {
        dom.logoutBtn.addEventListener("click", () => {
            if (typeof logout === "function") logout();
        });
    }

    document.querySelectorAll(".nav-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            if (typeof switchTab === "function") switchTab(btn.dataset.tab);
        });
    });

    // Initialize sub-modules
    if (typeof initTransportEvents === "function") initTransportEvents();
    if (typeof initProgressEvents === "function") initProgressEvents();
    if (typeof initSearchInputEvents === "function") initSearchInputEvents();
    if (typeof initActionModalEvents === "function") initActionModalEvents();
    if (typeof initClickDelegationEvents === "function") initClickDelegationEvents();
    if (typeof initKeyboardShortcutEvents === "function") initKeyboardShortcutEvents();
    if (typeof initQueueEvents === "function") initQueueEvents();
    if (typeof initQueueDragDrop === "function") initQueueDragDrop();
    if (typeof initLyricsEvents === "function") initLyricsEvents();
    if (typeof initSettingsEvents === "function") initSettingsEvents();
    if (typeof initDiscoverFilterEvents === "function") initDiscoverFilterEvents();
    if (typeof initDiscoverSearchEvents === "function") initDiscoverSearchEvents();
    if (typeof initDragScrollEvents === "function") initDragScrollEvents();
}

// T-B12.1: submit #setup-screen disabled sampai Password == Confirm Password.
// Field kosong (kedua-duanya) dianggap "match" secara string -- itu memang
// disengaja, kasus field kosong ditolak terpisah oleh submitSetup() sendiri
// lewat pesan "Isi username dan password!" (bukan tanggung jawab fungsi ini).
function updateSetupSubmitState() {
    if (!dom.setupSubmitBtn) return;
    const pass = dom.setupPassword ? dom.setupPassword.value : "";
    const confirmPass = dom.setupConfirmPassword ? dom.setupConfirmPassword.value : "";
    const mismatch = pass !== confirmPass;
    dom.setupSubmitBtn.disabled = mismatch;
    if (dom.setupConfirmErrorMsg) {
        dom.setupConfirmErrorMsg.textContent =
            mismatch && confirmPass.length > 0 ? "Password dan Confirm Password tidak sama." : "";
    }
}
