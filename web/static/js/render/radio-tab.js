function renderRadio() {
    const isRadio = store.playback_mode === 'RADIO';

    if (dom.radioToggleBtn) {
        if (isRadio) {
            dom.radioToggleBtn.classList.add("on");
            dom.radioToggleBtn.classList.remove("off");
            dom.radioToggleBtn.dataset.on = "true";
        } else {
            dom.radioToggleBtn.classList.add("off");
            dom.radioToggleBtn.classList.remove("on");
            dom.radioToggleBtn.dataset.on = "false";
        }
    }

    if (dom.rtSub) {
        if (isRadio) {
            if (store.status === "LOADING") {
                dom.rtSub.textContent = "Mencari stasiun...";
            } else {
                dom.rtSub.textContent = "24/7 Nonstop Music";
            }
        } else {
            dom.rtSub.textContent = "Aktifkan untuk putar otomatis";
        }
    }
}
