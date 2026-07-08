const _hashtagColors = {};
function getHashtagColor(hashtag) {
    if (_hashtagColors[hashtag]) return _hashtagColors[hashtag];
    let hash = 0;
    for (let i = 0; i < hashtag.length; i++) {
        hash = hashtag.charCodeAt(i) + ((hash << 5) - hash);
    }
    const hue = Math.abs(hash) % 360;
    const saturation = 60 + (Math.abs(hash >> 8) % 30);
    const lightness = 50 + (Math.abs(hash >> 16) % 20);
    const color = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
    _hashtagColors[hashtag] = color;
    return color;
}

function setLazyCoverData(img, track) {
    if (img.dataset.vid !== track.video_id) {
        img.dataset.vid = track.video_id || '';
        img.dataset.title = track.title || '';
        img.dataset.artist = track.artist || '';
        img.dataset.thumb = track.thumbnail || '';
        img.src = '';
        img.classList.remove('loaded');
    }
}

function renderDiscoverList(container, items, emptyHtml, createTemplate, updateItem) {
    if (!container) return;
    if (!items || items.length === 0) {
        container.innerHTML = emptyHtml;
        return;
    }
    
    const existing = Array.from(container.children);
    if (existing.length > 0 && (existing[0].classList.contains('skeleton-box') || existing[0].querySelector('.skeleton-box'))) {
        container.innerHTML = '';
        existing.length = 0;
    } else if (existing.length === 1 && existing[0].classList.contains('discover-empty')) {
        existing[0].remove();
        existing.shift();
    }
    
    items.forEach((item, i) => {
        let el = existing[i];
        if (!el) {
            el = createTemplate();
            container.appendChild(el);
        }
        updateItem(el, item, i);
    });
    
    while (container.children.length > items.length) {
        container.removeChild(container.lastChild);
    }
}

function renderDiscoverTab() {
    // Favorites
    if (dom.discFavorites && store.discover_favorites) {
        renderDiscoverList(
            dom.discFavorites,
            store.discover_favorites,
            '<div class="discover-empty"><i class="ti ti-heart-broken" style="font-size:32px; opacity:0.6; margin-bottom:12px; display:block;"></i>Belum ada data favorit</div>',
            () => {
                const div = document.createElement("div");
                div.className = "fav-card";
                div.innerHTML = `
                    <div class="fav-num"></div>
                    <div class="fav-thumb">
                        <img class="lazy-cover" src="" alt="">
                    </div>
                    <div class="fav-info">
                        <div class="fav-title"></div>
                        <div class="fav-cnt"></div>
                    </div>
                `;
                return div;
            },
            (el, track, i) => {
                const title = cleanTrackTitle(track.title);
                const playCnt = track.play_count > 0 ? ` · ${track.play_count}×` : '';
                el.dataset.vid = track.video_id || '';
                el.querySelector('.fav-num').textContent = i + 1;
                
                setLazyCoverData(el.querySelector('.lazy-cover'), track);
                
                el.querySelector('.fav-title').textContent = title;
                el.querySelector('.fav-cnt').textContent = (track.artist || '') + playCnt;
            }
        );
    }

    // Recent
    if (dom.discRecent && store.discover_recent) {
        renderDiscoverList(
            dom.discRecent,
            store.discover_recent,
            '<div class="discover-empty"><i class="ti ti-history" style="font-size:32px; opacity:0.6; margin-bottom:12px; display:block;"></i>Belum ada riwayat</div>',
            () => {
                const div = document.createElement("div");
                div.className = "sr-item";
                div.innerHTML = `
                    <div class="sr-thumb">
                        <img class="lazy-cover" src="" alt="">
                        <div class="thumb-eq-overlay">
                            <div class="eq-anim-icon">
                                <span></span><span></span><span></span>
                            </div>
                        </div>
                    </div>
                    <div class="sr-info">
                        <div class="sr-title"></div>
                        <div class="sr-meta"></div>
                    </div>
                    <div class="sr-duration"></div>
                    <button class="sr-more-btn" aria-label="More">
                        <i class="ti ti-dots-vertical"></i>
                    </button>
                `;
                return div;
            },
            (el, track, i) => {
                const title = cleanTrackTitle(track.title);
                let artistName = track.artist || "";
                if (artistName.length > 25) {
                    artistName = artistName.substring(0, 22) + "...";
                }
                
                el.dataset.vid = track.video_id || '';
                
                const thumbDiv = el.querySelector('.sr-thumb');
                if (track.local_path && !thumbDiv.querySelector('.disc-tag')) {
                    const tag = document.createElement("span");
                    tag.className = "disc-tag";
                    tag.textContent = "cache";
                    thumbDiv.appendChild(tag);
                } else if (!track.local_path && thumbDiv.querySelector('.disc-tag')) {
                    thumbDiv.querySelector('.disc-tag').remove();
                }
                
                const img = el.querySelector('.lazy-cover');
                if (img.dataset.vid !== track.video_id) {
                    img.dataset.vid = track.video_id || '';
                    img.dataset.title = track.title || '';
                    img.dataset.artist = track.artist || '';
                    img.dataset.thumb = track.thumbnail || '';
                    img.src = '';
                    img.classList.remove('loaded');
                }
                
                el.querySelector('.sr-title').textContent = title;
                el.querySelector('.sr-meta').textContent = artistName;
                el.querySelector('.sr-duration').textContent = formatTime(track.duration);
            }
        );
    }

    // Cached
    if (dom.discCached && store.discover_cached) {
        renderDiscoverList(
            dom.discCached,
            store.discover_cached,
            '<div class="discover-empty"><i class="ti ti-box-off" style="font-size:32px; opacity:0.6; margin-bottom:12px; display:block;"></i>Tidak ada file tersimpan</div>',
            () => {
                const div = document.createElement("div");
                div.className = "sr-item";
                div.innerHTML = `
                    <div class="sr-thumb">
                        <img class="lazy-cover" src="" alt="">
                        <div class="thumb-eq-overlay">
                            <div class="eq-anim-icon">
                                <span></span><span></span><span></span>
                            </div>
                        </div>
                    </div>
                    <div class="sr-info">
                        <div class="sr-title"></div>
                        <div class="sr-meta"></div>
                    </div>
                    <div class="sr-duration"></div>
                    <button class="sr-more-btn" aria-label="More">
                        <i class="ti ti-dots-vertical"></i>
                    </button>
                `;
                return div;
            },
            (el, track, i) => {
                const title = cleanTrackTitle(track.title);
                let artistName = track.artist || "";
                if (artistName.length > 25) {
                    artistName = artistName.substring(0, 22) + "...";
                }
                
                el.dataset.vid = track.video_id || '';
                
                const img = el.querySelector('.lazy-cover');
                if (img.dataset.vid !== track.video_id) {
                    img.dataset.vid = track.video_id || '';
                    img.dataset.title = track.title || '';
                    img.dataset.artist = track.artist || '';
                    img.dataset.thumb = track.thumbnail || '';
                    img.src = '';
                    img.classList.remove('loaded');
                }
                
                el.querySelector('.sr-title').textContent = title;
                el.querySelector('.sr-meta').textContent = artistName;
                el.querySelector('.sr-duration').textContent = formatTime(track.duration);
            }
        );
    }
    
    // Artists
    if (dom.discArtists && store.discover_featured_artists) {
        renderDiscoverList(
            dom.discArtists,
            store.discover_featured_artists,
            '',
            () => {
                const div = document.createElement("div");
                div.className = "hashtag-pill";
                return div;
            },
            (el, artist, i) => {
                const name = cleanTrackTitle(artist.nama);
                const hashtag = "#" + name.replace(/\s+/g, '');
                const color = getHashtagColor(hashtag);
                const clicks = artist.click_count || 0;
                const bonusSize = Math.min(clicks * 2, 14);
                const fontSize = 14 + bonusSize;
                
                el.dataset.artist = artist.nama;
                el.style.color = color;
                el.style.setProperty('--base-size', `${fontSize}px`);
                el.textContent = hashtag;
            }
        );
        
        dom.discArtists.onclick = (e) => {
            const pill = e.target.closest('.hashtag-pill');
            if (pill && pill.dataset.artist) {
                if (store.userRole !== 'admin') {
                    showLogToast("Hanya admin yang bisa memutar musik");
                    return;
                }
                showLogToast(`Memutar playlist dari ${pill.dataset.artist}...`);
                wsSend(WS_ACTIONS.ENQUEUE_ARTIST_SONGS, { artist: pill.dataset.artist });
                switchTab('home');
            }
        };
    }
    
    // Genres
    if (dom.discGenres && store.discover_featured_genres) {
        renderDiscoverList(
            dom.discGenres,
            store.discover_featured_genres,
            '',
            () => {
                const div = document.createElement("div");
                div.className = "hashtag-pill";
                return div;
            },
            (el, genre, i) => {
                const name = cleanTrackTitle(genre.nama_genre);
                const hashtag = "#" + name.replace(/\s+/g, '');
                const color = getHashtagColor(hashtag);
                const clicks = genre.click_count || 0;
                const bonusSize = Math.min(clicks * 2, 14);
                const fontSize = 14 + bonusSize;
                
                el.dataset.genre = genre.nama_genre;
                el.style.color = color;
                el.style.setProperty('--base-size', `${fontSize}px`);
                el.textContent = hashtag;
            }
        );
        
        dom.discGenres.onclick = (e) => {
            const pill = e.target.closest('.hashtag-pill');
            if (pill && pill.dataset.genre) {
                if (store.userRole !== 'admin') {
                    showLogToast("Hanya admin yang bisa memutar musik");
                    return;
                }
                showLogToast(`Memutar playlist dari genre ${pill.dataset.genre}...`);
                wsSend(WS_ACTIONS.ENQUEUE_GENRE_SONGS, { genre: pill.dataset.genre });
                switchTab('home');
            }
        };
    }
    
    window.loadLazyCovers();
    
    updateDiscoverPlayingState();
}

function updateDiscoverPlayingState() {
    const currentId = store.current_track && store.current_track.video_id;
    const isPlaying = store.status === "PLAYING";

    const homeRecentContainer = document.getElementById('home-recent-list');
    if (homeRecentContainer) {
        homeRecentContainer.querySelectorAll(".home-recent-item").forEach(item => {
            const isCurrent = currentId && item.dataset.vid === currentId;
            item.classList.toggle("current", !!isCurrent);
            item.classList.toggle("playing", !!(isCurrent && isPlaying));
        });
    }

    if (dom.discRecent) {
        dom.discRecent.querySelectorAll(".sr-item").forEach(item => {
            const isCurrent = currentId && item.dataset.vid === currentId;
            item.classList.toggle("current", !!isCurrent);
            item.classList.toggle("playing", !!(isCurrent && isPlaying));
        });
    }

    if (dom.discCached) {
        dom.discCached.querySelectorAll(".sr-item").forEach(item => {
            const isCurrent = currentId && item.dataset.vid === currentId;
            item.classList.toggle("current", !!isCurrent);
            item.classList.toggle("playing", !!(isCurrent && isPlaying));
        });
    }
}


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


function renderRecentRow() {
    const container = document.getElementById('home-recent-list');
    if (!container) return;

    const items = (store.discover_recent || []).slice(0, 5);

    renderDiscoverList(
        container,
        items,
        '<div style="padding:24px 20px; color:var(--text-3); font-size:14px; text-align:center;">Belum ada riwayat putar</div>',
        () => {
            const div = document.createElement("div");
            div.className = "home-recent-item";
            div.innerHTML = `
                <div class="home-recent-thumb">
                    <img class="lazy-cover" src="" alt="">
                </div>
                <div class="home-recent-info">
                    <div class="home-recent-title"></div>
                    <div class="home-recent-artist"></div>
                </div>
                <button class="home-recent-more" aria-label="More">
                    <i class="ti ti-dots-vertical"></i>
                </button>
            `;
            
            div.addEventListener('click', (e) => {
                if (e.target.closest('.home-recent-more')) return;
                if (store.userRole !== 'admin') return;
                const vid = div.dataset.vid;
                if (!vid) return;
                const track = (store.discover_recent || []).find(t => t.video_id === vid);
                if (track) window.wsSend(WS_ACTIONS.PLAY_TRACK, track);
            });
            
            div.querySelector('.home-recent-more').addEventListener('click', (e) => {
                e.stopPropagation();
                if (store.userRole !== 'admin') return;
                const vid = div.dataset.vid;
                if (!vid) return;
                const track = (store.discover_recent || []).find(t => t.video_id === vid);
                if (track) window.showActionModal(track);
            });
            
            return div;
        },
        (el, track, i) => {
            const title = typeof cleanTrackTitle === 'function' ? cleanTrackTitle(track.title) : track.title;
            const currentId = store.current_track && store.current_track.video_id;
            const isCurrent = track.video_id && track.video_id === currentId;
            
            el.dataset.vid = track.video_id || '';
            
            if (isCurrent) el.classList.add('current');
            else el.classList.remove('current');
            
            const img = el.querySelector('.lazy-cover');
            if (img.dataset.vid !== track.video_id) {
                img.dataset.vid = track.video_id || '';
                img.dataset.title = track.title || '';
                img.dataset.artist = track.artist || '';
                img.dataset.thumb = track.thumbnail || '';
                img.src = '';
                img.classList.remove('loaded');
            }
            
            el.querySelector('.home-recent-title').textContent = title;
            el.querySelector('.home-recent-artist').textContent = track.artist || '';
        }
    );

    window.loadLazyCovers();
}
