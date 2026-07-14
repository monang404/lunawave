function renderPlayerBar() {
    // PATCH-ANDROID-AUDIO-01: dulu baris ini menimpa data-player-state dengan logic
    // berbeda dari now-playing.js (cuma cek store.status, gak cek track),
    // bikin idle-view bisa nyangkut salah. Sekarang pakai fungsi bersama.
    if (typeof syncPlayerStateAttr === "function") syncPlayerStateAttr();
    const t = store.current_track;

    if (store.status === "LOADING") {
        dom.pbTrackInfo.innerHTML = '<span class="spinner" style="display:inline-block; margin-right:5px; vertical-align:-2px;"></span> Memuat... ' + escapeHtml(t ? t.title : "");
    } else if (t) {
        const title = typeof cleanTrackTitle === "function" ? cleanTrackTitle(t.title) : t.title;
        const thumbUrl = t.thumbnail || '';
        const fallbackIcon = `<i class="ti ti-music" style="color:var(--text-3); font-size:20px;"></i>`;
        const thumbHtml = thumbUrl ? `<img src="${escapeHtml(thumbUrl)}" style="width:44px; height:44px; border-radius:6px; object-fit:cover; flex-shrink:0;">` : `<div style="width:44px; height:44px; border-radius:6px; background:rgba(255,255,255,0.1); flex-shrink:0; display:flex; align-items:center; justify-content:center;">${fallbackIcon}</div>`;
        dom.pbTrackInfo.innerHTML = `
            <div style="display:flex; align-items:center; gap:12px; min-width:0;">
                ${thumbHtml}
                <div style="display:flex; flex-direction:column; justify-content:center; line-height:1.3; overflow:hidden; min-width:0;">
                    <span style="font-weight:600; font-size:14px; color:var(--text-1); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(title)}</span>
                    <span style="font-size:12px; color:var(--text-3); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(t.artist)}</span>
                </div>
            </div>
        `;
    } else {
        dom.pbTrackInfo.innerHTML = "";
    }

    renderPlayBtn();

    if (store.playback_mode === "RADIO") {
        dom.pbModeBadge.textContent = "📻 radio";
        dom.pbModeBadge.className = "pb-mode-badge radio";
    } else {
        dom.pbModeBadge.textContent = "≡ queue";
        dom.pbModeBadge.className = "pb-mode-badge queue";
    }

    if (dom.pbVolLabel) dom.pbVolLabel.textContent = store.volume + "%";
    if (dom.volSlider && !window.isDraggingVol) dom.volSlider.value = store.volume;

    if (t && t.local_path) {
        dom.pbCacheBadge.textContent = "✓ tersimpan";
        dom.pbCacheBadge.className = "pb-badge-sm cached";
        dom.pbCacheBadge.style.display = "inline-block";
    } else if (t) {
        dom.pbCacheBadge.textContent = "☁ stream";
        dom.pbCacheBadge.className = "pb-badge-sm stream";
        dom.pbCacheBadge.style.display = "inline-block";
    } else {
        dom.pbCacheBadge.textContent = "";
        dom.pbCacheBadge.style.display = "none";
    }

    dom.pbSbBadge.textContent = store.sponsorblock_active ? "SB: ON" : "";
    dom.pbSbBadge.style.display = store.sponsorblock_active ? "inline-block" : "none";

    if (store.download_progress != null) {
        dom.pbDlBadge.textContent = "⬇ " + Math.round(store.download_progress * 100) + "%";
        dom.pbDlBadge.style.display = "inline-block";
    } else {
        dom.pbDlBadge.textContent = "";
        dom.pbDlBadge.style.display = "none";
    }
}

function renderPlayBtn() {
    if (store.status === "PLAYING") {
        dom.btnPlay.innerHTML = '<svg viewBox="0 0 24 24" width="28" height="28" fill="#fff"><path d="M14,19H18V5H14M6,19H10V5H6V19Z"></path></svg>';
    } else {
        dom.btnPlay.innerHTML = '<svg viewBox="0 0 24 24" width="28" height="28" fill="#fff"><path d="M8,5.14V19.14L19,12.14L8,5.14Z"></path></svg>';
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// SMOOTH PROGRESS CLOCK (biar semulus Spotify/YouTube Music)
//
// Sebelumnya progress bar cuma digambar ulang PAS ada event baru: "timeupdate"
// dari <audio> browser (~4x/detik, gak selalu rapi jaraknya) atau pesan
// "progress" dari server (~1x/detik). Karena dua sumber ini gak pernah
// nge-tick bebarengan & gak sama presisinya, tampilannya "patah-patah" dan
// kadang kerasa balapan/gontai — sebentar diem, sebentar loncat — beda jauh
// dari Spotify/YouTube Music yang progress bar-nya gerak mulus tiap frame.
//
// Fix: bar gak lagi digambar langsung dari event. Event2 itu (timeupdate,
// progress server, seek) sekarang cuma nge-update SATU "anchor" (posisi
// diketahui + kapan itu diketahui, pakai performance.now()). Lalu ada satu
// loop requestAnimationFrame yang jalan terus (~60fps) yang GAMBAR posisi
// hasil interpolasi dari anchor itu: anchor.value + waktu yang berlalu sejak
// anchor di-set. Hasilnya gerakan progress bar mulus terus-menerus, gak
// peduli event sumbernya jarang/gak rata — sama seperti cara Spotify bikin
// progress bar mulus walau posisi asli cuma di-refresh sesekali dari server.
// ─────────────────────────────────────────────────────────────────────────────
let _posAnchorValue = 0;
let _posAnchorTime = 0;
let _progressRafId = null;

function setPositionAnchor(value) {
    _posAnchorValue = Math.max(0, value || 0);
    _posAnchorTime = performance.now();
    store.position = _posAnchorValue;
}

// FIX-POSITION-DRIFT-06: dipanggil setiap kali status BERUBAH jadi "PLAYING"
// (klik play, atau notifikasi dari client lain kalau admin lain yang resume).
// Cuma reset _posAnchorTime ke "sekarang" — nilai posisinya TETAP yang
// terakhir diketahui. Kalau ini gak dipanggil, interpolasi rAF ikut
// menghitung elapsed dari kapan anchor terakhir di-set (yaitu SAAT PAUSE
// tadi), sehingga durasi jeda nunggu sebelum nekan play ikut ke-hitung
// sebagai "waktu berjalan" -> angka loncat maju jauh (mis. 41+jeda=45),
// baru ketarik balik begitu timeupdate asli dari audio browser masuk.
// Reset ini bikin interpolasi mulai dari 0 elapsed persis saat play beneran
// ditekan/diketahui, jadi gak ada lompatan maju-mundur itu lagi.
function resetAnchorClock() {
    _posAnchorTime = performance.now();
}

function getInterpolatedPosition() {
    if (store.status !== "PLAYING") return _posAnchorValue;
    const dur = store.current_track ? store.current_track.duration : 0;
    const elapsed = (performance.now() - _posAnchorTime) / 1000;
    const pos = _posAnchorValue + elapsed;
    return dur > 0 ? Math.min(pos, dur) : pos;
}

function startProgressClock() {
    if (_progressRafId) return;
    function tick() {
        _progressRafId = requestAnimationFrame(tick);
        if (window.isDraggingPb) return;
        _renderProgressCore(getInterpolatedPosition());
    }
    _progressRafId = requestAnimationFrame(tick);
}

function renderProgress() {
    // Dipanggil dari event (timeupdate, progress, seek, dll) yang sudah
    // mengupdate anchor lewat setPositionAnchor(). Loop rAF di atas yang
    // pegang penggambaran tiap frame; ini cuma jaga-jaga gambar sekali
    // langsung (misal pas status bukan PLAYING, di mana loop tetap jalan
    // tapi nilainya statis) supaya gak nunggu frame berikutnya.
    if (window.isDraggingPb) return;
    _renderProgressCore(getInterpolatedPosition());
}

function _renderProgressCore(posOverride) {
    if (window.isDraggingPb) return;
    const dur = store.current_track ? store.current_track.duration : 0;
    const pos = posOverride != null ? posOverride : (store.position || 0);
    const pct = dur > 0 ? Math.min(100, (pos / dur) * 100) : 0;

    dom.pbProgressFill.style.width = pct + "%";

    // update thumb
    const thumb = dom.pbProgressTrack.querySelector('.pb-thumb');
    if(thumb) thumb.style.left = pct + "%";

    dom.pbTimePos.textContent = formatTime(pos);
    dom.pbTimeDur.textContent = formatTime(dur);

    // S8-08 Mini Player Progress
    const playerBar = document.getElementById("player-bar");
    if(playerBar) playerBar.style.setProperty("--mini-progress", pct + "%");
}
