function initDragScrollEvents() {
    let isDown = false;
    let isDragging = false;
    let startX;
    let scrollLeft;
    let slider = null;

    document.addEventListener('mousedown', (e) => {
        const row = e.target.closest('.card-row, .radio-grid, .nav-tabs, .chip-row');
        if (!row) return;

        isDown = true;
        isDragging = false;
        slider = row;
        slider.style.cursor = 'grabbing';

        startX = e.pageX - slider.offsetLeft;
        scrollLeft = slider.scrollLeft;
    });

    const stopDrag = () => {
        isDown = false;
        if (slider) {
            slider.style.cursor = '';
            slider = null;
        }
    };

    document.addEventListener('mouseleave', stopDrag);
    document.addEventListener('mouseup', stopDrag);

    document.addEventListener('mousemove', (e) => {
        if (!isDown || !slider) return;

        // Failsafe: If mouse button is released outside window or swallowed by other events
        if (e.buttons !== 1) {
            stopDrag();
            return;
        }

        const x = e.pageX - slider.offsetLeft;
        const walk = (x - startX);

        if (Math.abs(walk) > 3) {
            isDragging = true;
            e.preventDefault(); // Prevent text selection
            slider.scrollLeft = scrollLeft - walk * 1.5;
        }
    });

    document.addEventListener('click', (e) => {
        if (isDragging) {
            e.preventDefault();
            e.stopPropagation();
            isDragging = false;
        }
    }, true);

    // Prevent native browser image drag which breaks custom drag-scroll
    document.addEventListener('dragstart', (e) => {
        if (e.target.closest('.card-row, .radio-grid, .nav-tabs, .chip-row')) {
            e.preventDefault();
        }
    });
}
