function initClickDelegationEvents() {
    document.addEventListener("click", (e) => {
        // 1. Clicks on 3-dots button (.sr-more-btn)
        const moreBtn = e.target.closest(".sr-more-btn");
        if (moreBtn) {
            const item = moreBtn.closest(".sr-item");
            if (item) {
                const trackStr = item.dataset.trackStr || item.dataset.searchTrackStr;
                if (trackStr) {
                    try {
                        const track = JSON.parse(trackStr);
                        if (typeof showActionModal === "function") showActionModal(track);
                    } catch (err) { console.error(err); }
                }
            }
            return;
        }

        // 2. Clicks on the sr-item row itself -> Play track
        const srItem = e.target.closest(".sr-item");
        if (srItem) {
            const trackStr = srItem.dataset.trackStr || srItem.dataset.searchTrackStr;
            if (trackStr) {
                try {
                    const track = JSON.parse(trackStr);
                    if (store.userRole === "admin") {
                        wsSend("play_track", track);
                    }
                } catch (err) { console.error(err); }
            }
            return;
        }

        // 3. Clicks on fav-card or disc-card
        const card = e.target.closest(".disc-card, .fav-card, .search-result-item");
        if (card && card.dataset.vid) {
            let track = null;
            if (card.classList.contains("search-result-item") && card.dataset.searchTrackStr) {
                track = JSON.parse(card.dataset.searchTrackStr);
            } else {
                const vid = card.dataset.vid;
                // find in store lists
                const lists = [
                    store.discover_recent || [],
                    store.discover_cached || [],
                    store.queue || []
                ];
                for (const list of lists) {
                    track = list.find(t => t.video_id === vid);
                    if (track) break;
                }
            }
            if (track && typeof showActionModal === "function") showActionModal(track);
            return;
        }
    });
}
