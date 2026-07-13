function initActionModalEvents() {
    if (dom.actionPlayNow) {
        dom.actionPlayNow.addEventListener("click", () => {
            if (window.pendingTrack) wsSend("play_track", window.pendingTrack);
            if (typeof hideActionModal === "function") hideActionModal();
        });
    }

    if (dom.actionEnqueue) {
        dom.actionEnqueue.addEventListener("click", () => {
            if (window.pendingTrack) wsSend("queue_add", window.pendingTrack);
            if (typeof hideActionModal === "function") hideActionModal();
        });
    }

    if (dom.actionCancel) {
        dom.actionCancel.addEventListener("click", () => {
            if (typeof hideActionModal === "function") hideActionModal();
        });
    }

    if (dom.actionDelete) {
        dom.actionDelete.addEventListener("click", () => {
            if (store.userRole !== "admin") return;
            if (window.pendingTrack) {
                wsSend("delete_download", window.pendingTrack);
            }
            if (typeof hideActionModal === "function") hideActionModal();
        });
    }
}
