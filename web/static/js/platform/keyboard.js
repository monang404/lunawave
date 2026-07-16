(function() {
    // Hanya aktif di desktop (pointer: fine = mouse)
    if (window.matchMedia('(pointer: fine)').matches) {
        document.addEventListener('keydown', (e) => {
            // Jangan intercept saat user mengetik di input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            // NOTE: 'Space' sengaja tidak ditangani di sini -- sudah ditangani secara
            // global (admin-gated) oleh events/keyboard-shortcut-events.js. Menangani
            // Space di sini juga akan jadi duplicate listener untuk tombol yang sama.
            switch (e.code) {
                case 'ArrowRight':
                    if (store.userRole !== 'admin') return;
                    e.preventDefault();
                    if (typeof wsSend === 'function') wsSend('next');
                    break;
                case 'ArrowLeft':
                    if (store.userRole !== 'admin') return;
                    e.preventDefault();
                    if (typeof wsSend === 'function') wsSend('prev');
                    break;
            }
        });
    }
})();
