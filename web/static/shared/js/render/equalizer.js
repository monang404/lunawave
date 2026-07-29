/**
 * Module: web.static.shared.js.render.equalizer
 *
 * Purpose:
 *     Satu sumber kebenaran untuk visibilitas + status animasi
 *     #home-equalizer (fallback visual saat lirik tidak ditemukan).
 *
 * PATCH-EQ-REDESIGN-01:
 *     Sebelumnya logic ini terpecah di dua tempat yang saling menimpa
 *     tergantung urutan panggilan:
 *       - render/lyrics.js  -> nyalakan container equalizer setiap kali
 *         tidak ada lirik, TANPA peduli status PLAYING/PAUSED.
 *       - render/now-playing.js -> matikan container equalizer setiap kali
 *         status BUKAN PLAYING, TANPA peduli lirik.
 *     Karena client.js kadang manggil salah satu duluan (lihat urutan
 *     renderNowPlaying()+renderLyrics() vs renderLyrics() saja), hasil
 *     akhirnya race condition: kadang equalizer nyangkut nyala padahal
 *     lirik sudah ada, kadang mati padahal seharusnya jadi fallback idle.
 *     Selain itu tidak ada satupun dari keduanya yang peduli soal
 *     document.hidden -- jadi keyframe animasi bar tetap jalan (dan
 *     browser tetap compute repaint-nya) walau tab/layar sedang
 *     tersembunyi selama status masih PLAYING, boros CPU/baterai di
 *     Termux/Android saat layar mati (sama seperti pola PERF-3 di
 *     audio/visualizer.js & render/radio-hero-moon.js).
 *
 *     updateEqualizerState() sekarang jadi satu-satunya tempat yang boleh
 *     menyentuh dom.homeEqualizer -- dipanggil dari renderLyrics() dan
 *     renderNowPlaying() (keduanya delegasi ke sini, tidak lagi
 *     memanipulasi display-nya sendiri-sendiri), plus dari listener
 *     visibilitychange di bawah.
 *
 * Depends on:
 *     - shared.js.dom, shared.js.store
 *
 * Thread Safety:
 *     Main thread (DOM).
 */

import { dom } from "../dom.js";
import { store } from "../store.js";

if (typeof document !== "undefined") {
    document.addEventListener("visibilitychange", () => {
        updateEqualizerState();
    });
}

export function updateEqualizerState() {
    if (!dom.homeEqualizer) return;

    const hasLyrics = !!(store.lyrics_lines && store.lyrics_lines.length > 0);
    const pageHidden = typeof document !== "undefined" && document.hidden;

    // Container: dipakai sebagai fallback kapanpun tidak ada lirik --
    // termasuk saat idle/paused, karena teks "Audio Focus" tetap perlu
    // terlihat (bukan cuma sewaktu PLAYING). Begitu lirik tersedia,
    // disembunyikan total.
    dom.homeEqualizer.style.display = hasLyrics ? "none" : "flex";

    // Animasi bar cuma boleh benar-benar jalan kalau ketiganya terpenuhi:
    // tidak ada lirik, status PLAYING, dan tab/layar sedang terlihat.
    // Selain itu (termasuk idle/paused DAN saat backgrounded meski masih
    // PLAYING) di-freeze total lewat class "eq-frozen" (animation: none di
    // CSS) -- bukan cuma opacity -- supaya tidak ada keyframe yang terus
    // dihitung di belakang layar.
    const shouldAnimate = !hasLyrics && store.status === "PLAYING" && !pageHidden;
    dom.homeEqualizer.classList.toggle("eq-frozen", !shouldAnimate);
}
