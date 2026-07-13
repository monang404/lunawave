function initKeyboardShortcutEvents() {
    document.addEventListener("keydown", (e) => {
        if (document.activeElement === dom.searchInput) {
            if (e.key === "Escape") dom.searchInput.blur();
            return;
        }

        switch (e.key) {
            case " ":
                if (store.userRole !== "admin") return;
                e.preventDefault();
                wsSend("toggle_pause");
                break;
            case "n":
            case "N":
                if (store.userRole !== "admin") return;
                wsSend("next");
                break;
            case "b":
            case "B":
                if (store.userRole !== "admin") return;
                wsSend("prev");
                break;
            case "s":
            case "S":
                if (store.userRole !== "admin") return;
                wsSend("stop");
                break;
            case "ArrowUp":
                if (store.userRole !== "admin") return;
                e.preventDefault();
                wsSend("volume_up");
                break;
            case "ArrowDown":
                if (store.userRole !== "admin") return;
                e.preventDefault();
                wsSend("volume_down");
                break;
            case "m":
            case "M":
                if (store.userRole !== "admin") return;
                wsSend("download");
                break;
            case "r":
            case "R":
                if (store.userRole !== "admin") return;
                if (store.status === "LOADING") break;
                const newMode = store.playback_mode === "RADIO" ? "QUEUE" : "RADIO";
                wsSend("set_mode", { mode: newMode });
                break;
            case "l":
            case "L":
                if (dom.lyricsSheet) {
                    const isOpen = dom.lyricsSheet.classList.contains("open");
                    if (isOpen) {
                        dom.lyricsSheet.classList.remove("open");
                        if (typeof closeMainOverlay === "function") closeMainOverlay();
                    } else {
                        dom.lyricsSheet.classList.add("open");
                        if (dom.mainOverlay) dom.mainOverlay.classList.add("open");
                        if (typeof renderLyrics === "function") renderLyrics();
                    }
                }
                break;
            case "/":
                e.preventDefault();
                if (typeof switchTab === "function") switchTab("search");
                break;
            case "?":
                if (dom.helpSheet) {
                    if (dom.helpSheet.classList.contains("open")) {
                        dom.helpSheet.classList.remove("open");
                        if (typeof closeMainOverlay === "function") closeMainOverlay();
                    } else {
                        dom.helpSheet.classList.add("open");
                        if (dom.mainOverlay) dom.mainOverlay.classList.add("open");
                    }
                }
                break;
            case "Escape":
                if (typeof hideActionModal === "function") hideActionModal();
                if (dom.helpSheet) dom.helpSheet.classList.remove("open");
                if (dom.settingsSheet) dom.settingsSheet.classList.remove("open");
                if (dom.lyricsSheet) dom.lyricsSheet.classList.remove("open");
                if (typeof closeMainOverlay === "function") closeMainOverlay();
                break;
        }
    });
}
