(function() {
    let touchStartX = 0;
    let touchStartY = 0;

    document.addEventListener('touchstart', e => {
        unlockBrowserAudio();
        if (e.touches.length === 1) {
            touchStartX = e.touches[0].screenX;
            touchStartY = e.touches[0].screenY;
        }
    }, { passive: true });

    document.addEventListener('touchend', e => {
        if (e.target.closest(
            "#radio-toggle-btn, button, a, input, select, textarea, [role=\"button\"], .mood-row, .disc-row2, [style*=\"overflow-x\"]"
        )) return;
        
        if (e.changedTouches.length === 1) {
            const touchEndX = e.changedTouches[0].screenX;
            const touchEndY = e.changedTouches[0].screenY;
            const diffX = Math.abs(touchEndX - touchStartX);
            const diffY = Math.abs(touchEndY - touchStartY);
            
            if (diffX > 80 && diffX > diffY) {
                if (store.userRole !== "admin") {
                    showLogToast("Hanya admin yang bisa memutar musik");
                    return;
                }
                if (touchEndX < touchStartX) {
                    wsSend(WS_ACTIONS.NEXT);
                } else {
                    wsSend(WS_ACTIONS.PREV);
                }
            }
        }
    });
})();
