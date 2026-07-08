function applyRoleUI() {
    if (store.userRole === "portal") {
        dom.portalScreen.classList.add("portal-active");
        dom.appContainer.classList.add("portal-active");
        document.body.classList.remove("client-mode");
        dom.logoutBtn.style.display = "none";
    } else if (store.userRole === "client") {
        dom.portalScreen.classList.remove("portal-active");
        dom.appContainer.classList.remove("portal-active");
        document.body.classList.add("client-mode");
        switchTab("home");
        dom.logoutBtn.style.display = "flex";
    } else if (store.userRole === "admin") {
        dom.portalScreen.classList.remove("portal-active");
        dom.appContainer.classList.remove("portal-active");
        document.body.classList.remove("client-mode");
        dom.logoutBtn.style.display = "flex";
        switchTab("home");
        if (window.visualViewport) {
            const _app = document.getElementById("app");
            if (_app) {
                _app.style.height = window.visualViewport.height + "px";
            }
        }
    }
    renderHeader();
}

function login(user, pass) {
    if (!user || !pass) {
        dom.loginErrorMsg.textContent = "Isi username dan password!";
        return;
    }
    
    if (dom.adminSubmitBtn) {
        dom.adminSubmitBtn.disabled = true;
        dom.adminSubmitBtn.textContent = "Menghubungkan...";
    }
    dom.loginErrorMsg.textContent = "";
    
    store.adminUsername = user;
    if (dom.adminPassword) {
        dom.adminPassword.value = "";
    }
    if (wsClient && wsClient.getReadyState() === WebSocket.OPEN) {
        wsSend(WS_ACTIONS.AUTH, { username: user, password: pass });
    } else {
        dom.loginErrorMsg.textContent = "Koneksi server terputus. Silakan tunggu/refresh.";
        if (dom.adminSubmitBtn) {
            dom.adminSubmitBtn.disabled = false;
            dom.adminSubmitBtn.textContent = "Login Admin";
        }
    }
}

function logout() {
    if (typeof localAudio !== "undefined" && localAudio) {
        try {
            localAudio.pause();
            localAudio.src = "";
            localAudio.removeAttribute("src");
            localAudio.load();
        } catch (e) {
            console.warn("Failed to stop browser audio:", e);
        }
    }
    if (typeof _lastLoadedVideoId !== "undefined") {
        _lastLoadedVideoId = null;
    }

    if (store.userRole === "admin") {
        try {
            wsSend(WS_ACTIONS.STOP);
        } catch (e) {
            console.warn("Failed to send stop command:", e);
        }
    }

    const token = safeStorage.get("ytgui_session_token");
    if (token) {
        try {
            wsSend(WS_ACTIONS.LOGOUT, { token: token });
        } catch (e) {
            console.warn("Failed to send logout command:", e);
        }
    }

    store.userRole = "portal";
    store.adminUsername = "";
    safeStorage.remove("ytgui_user_role");
    safeStorage.remove("ytgui_admin_username");
    safeStorage.remove("ytgui_session_token");

    closeSettings();

    if (dom.portalClientBtn) {
        dom.portalClientBtn.style.display = "none";
    }
    applyRoleUI();
    try {
        if (typeof wsClient !== "undefined") {
            wsClient.close();
        }
    } catch (e) {}
}
