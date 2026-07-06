(function() {
    if (window.matchMedia('(pointer: fine)').matches) {
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            switch (e.code) {
                case 'Space':
                    e.preventDefault();
                    cmd('play');
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    cmd('next');
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    cmd('prev');
                    break;
            }
        });
    }
})();
