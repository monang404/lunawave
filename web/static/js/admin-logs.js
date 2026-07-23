/**
 * admin-logs.js
 *
 * Fetches initial log history and listens to live tailing via WebSocket.
 */

// UI Elements
const logContainer = document.getElementById('logContainer');
const autoScrollCheckbox = document.getElementById('autoScroll');
const connBanner = document.getElementById('connBanner');
const btnFilter = document.getElementById('btnFilter');
const btnDownload = document.getElementById('btnDownload');
const filterLevel = document.getElementById('filterLevel');
const filterCategory = document.getElementById('filterCategory');
const filterSearch = document.getElementById('filterSearch');

const globalStatsGrid = document.getElementById('globalStatsGrid');
const levelStatsList = document.getElementById('levelStatsList');
const catStatsList = document.getElementById('catStatsList');

const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');
const matrixContainer = document.getElementById('matrixContainer');

tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));

        btn.classList.add('active');
        document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    });
});

function navigateToLiveTail(cat, level) {
    document.querySelector('.tab-btn[data-tab="live"]').click();
    filterCategory.value = cat;
    filterLevel.value = level;
    fetchTail(true);
}

let ws = null;
let reconnectTimer = null;
let isPolling = false;
let pollTimer = null;
const seenLogs = new Set();

// Categories for badge coloring
const CATEGORY_COLORS = {
    "lifecycle": "#bb86fc",
    "http": "#004d40",
    "session": "#01579b",
    "command": "#b71c1c",
    "playback": "#1b5e20",
    "queue": "#827717",
    "discovery": "#e65100",
    "download": "#3e2723",
    "lyrics": "#880e4f",
    "db": "#4e342e",
    "cache": "#37474f",
    "metrics": "#006064",
    "security": "#b71c1c",
    "app": "#212121",
    "unknown": "#212121"
};

function getCategoryColor(cat) {
    return CATEGORY_COLORS[cat] || CATEGORY_COLORS["unknown"];
}

function escapeHtml(unsafe) {
    if (!unsafe) return "";
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

function formatFields(fields) {
    if (!fields || Object.keys(fields).length === 0) return "";
    const parts = [];
    for (const [k, v] of Object.entries(fields)) {
        if (k !== "category") {
            parts.push(`${k}=${v}`);
        }
    }
    if (parts.length === 0) return "";
    return `(${escapeHtml(parts.join(", "))})`;
}

function getLevelIcon(level) {
    switch (level) {
        case 'INFO': return '<i class="ti ti-info-circle"></i>';
        case 'WARNING': return '<i class="ti ti-alert-triangle"></i>';
        case 'ERROR':
        case 'CRITICAL': return '<i class="ti ti-circle-x"></i>';
        case 'DEBUG': return '<i class="ti ti-bug"></i>';
        default: return '<i class="ti ti-point-filled"></i>';
    }
}

function createLogLineElement(log) {
    const div = document.createElement('div');
    div.className = 'log-line';

    const catShort = log.fields && log.fields.category
        ? log.fields.category.replace('LC_', '').toLowerCase()
        : 'unknown';

    let fieldsHtml = '';
    let compHtml = '';
    let eventText = log.event || '';

    let extraChips = [];

    // Parse status and dur from eventText if it's a traffic log
    const statusMatch = eventText.match(/status=(\d+)/);
    if (statusMatch) {
        let code = parseInt(statusMatch[1]);
        let statusClass = "val-num";
        let iconHtml = "";
        if (code >= 400) {
            statusClass = "val-err";
            iconHtml = '<i class="ti ti-x" style="margin-right:2px"></i>';
        } else if (code >= 200 && code < 300) {
            statusClass = "val-ok";
            iconHtml = '<i class="ti ti-check" style="margin-right:2px"></i>';
        }
        extraChips.push(`<span class="log-chip"><span class="chip-key">status</span><span class="chip-val ${statusClass}">${iconHtml}${code}</span></span>`);
        eventText = eventText.replace(statusMatch[0], '').trim();
    }

    const durMatch = eventText.match(/dur=(\d+(?:\.\d+)?ms)/);
    if (durMatch) {
        extraChips.push(`<span class="log-chip"><span class="chip-key">dur</span><span class="chip-val val-num"><i class="ti ti-clock" style="margin-right:2px"></i>${durMatch[1]}</span></span>`);
        eventText = eventText.replace(durMatch[0], '').trim();
    }

    if (log.fields) {
        const fields = {...log.fields};
        delete fields.category; // Already shown

        let component = fields.component || '';
        delete fields.component;

        if (component) {
            compHtml = `<span class="log-comp">${component}</span><span style="color:var(--border-3); margin:0 6px;">›</span>`;
        }

        const fieldKeys = Object.keys(fields);
        for (const key of fieldKeys) {
            let valClass = "chip-val";
            if (key === 'error_type' || key === 'error') valClass += " val-err";
            if (key.includes('duration') || key.includes('bytes') || typeof fields[key] === 'number') valClass += " val-num";

            extraChips.push(`<span class="log-chip"><span class="chip-key">${key}</span><span class="${valClass}">${fields[key]}</span></span>`);
        }
    }

    if (extraChips.length > 0) {
        fieldsHtml = `<div class="log-chips">${extraChips.join('')}</div>`;
    }

    div.innerHTML = `
        <div class="log-icon lvl-${log.level}">${getLevelIcon(log.level)}</div>
        <div class="log-time">${log.time || '--:--:--'}</div>
        <div class="log-cat">${catShort}</div>
        <div class="log-message">
            ${compHtml}<span class="log-event">${eventText}</span>
        </div>
        ${fieldsHtml}
    `;

    const copyBtn = document.createElement('button');
    copyBtn.className = 'log-copy-btn';
    copyBtn.title = 'Copy log text';
    copyBtn.innerHTML = '<i class="ti ti-copy"></i>';
    copyBtn.onclick = () => {
        const rawFields = log.fields || {};
        const fieldStrs = [];
        for (const [k, v] of Object.entries(rawFields)) {
            if (k !== 'category' && k !== 'component') {
                fieldStrs.push(`${k}=${v}`);
            }
        }
        const fieldStr = fieldStrs.length > 0 ? ` (${fieldStrs.join(', ')})` : '';
        const compStr = rawFields.component ? `${rawFields.component}: ` : '';
        const textToCopy = `[${log.time || '--:--:--'}] ${log.level} [${catShort.toUpperCase()}] ${compStr}${log.event || ''}${fieldStr}`;

        navigator.clipboard.writeText(textToCopy).then(() => {
            copyBtn.innerHTML = '<i class="ti ti-check" style="color:var(--green)"></i>';
            setTimeout(() => {
                copyBtn.innerHTML = '<i class="ti ti-copy"></i>';
            }, 2000);
        });
    };
    div.appendChild(copyBtn);

    return div;
}

function appendLogBatch(logs, clearFirst = false) {
    if (clearFirst) {
        logContainer.innerHTML = '';
        seenLogs.clear();
    }

    const fragment = document.createDocumentFragment();
    for (const log of logs) {
        const hash = log.time + log.level + log.event + JSON.stringify(log.fields || {});
        if (!seenLogs.has(hash)) {
            seenLogs.add(hash);
            fragment.appendChild(createLogLineElement(log));
        }
    }

    if (fragment.childNodes.length > 0) {
        logContainer.appendChild(fragment);

        // Cleanup old lines if too many
        while (logContainer.children.length > 5000) {
            logContainer.removeChild(logContainer.firstChild);
        }

        // Trim seenLogs set to prevent memory leak
        if (seenLogs.size > 10000) {
            const arr = Array.from(seenLogs).slice(-5000);
            seenLogs.clear();
            arr.forEach(h => seenLogs.add(h));
        }

        if (autoScrollCheckbox.checked) {
            logContainer.scrollTop = logContainer.scrollHeight;
        }
    }
}

async function fetchStats() {
    try {
        const token = localStorage.getItem('metricsToken') || '';
        const headers = token ? {'X-Metrics-Token': token} : {};
        const res = await fetch('/api/logs/stats', { headers });
        if (!res.ok) throw new Error('Failed to fetch stats');

        const data = await res.json();

        // Render Global Metrics Grid (Categories)
        globalStatsGrid.innerHTML = '';
        if (data.log_stats && data.log_stats.categories) {
            const sorted = Object.entries(data.log_stats.categories).sort((a, b) => b[1] - a[1]);
            for (const [cat, count] of sorted) {
                const box = document.createElement('div');
                box.className = 'stat-box';
                box.style.cursor = 'pointer';
                box.innerHTML = `
                    <div class="stat-val">${count}</div>
                    <div class="stat-lbl">${cat}</div>
                `;
                box.onclick = () => {
                    filterCategory.value = cat;
                    fetchTail(true);
                };
                globalStatsGrid.appendChild(box);
            }
        }

        // Render Levels
        levelStatsList.innerHTML = '';
        if (data.log_stats && data.log_stats.levels) {
            for (const [lvl, count] of Object.entries(data.log_stats.levels)) {
                levelStatsList.innerHTML += `<li class="category-item"><span class="lvl-${lvl}">${lvl}</span> <span>${count}</span></li>`;
            }
        }

        // Render Top Categories List
        catStatsList.innerHTML = '';
        if (data.log_stats && data.log_stats.categories) {
            const sorted = Object.entries(data.log_stats.categories).sort((a, b) => b[1] - a[1]).slice(0, 5);
            for (const [cat, count] of sorted) {
                const color = getCategoryColor(cat);
                catStatsList.innerHTML += `<li class="category-item"><span style="color:${color}">${cat}</span> <span>${count}</span></li>`;
            }
        }

        // Render Matrix Table
        if (data.log_stats && data.log_stats.matrix) {
            renderMatrix(data.log_stats.matrix);
        }

        // Render System Dashboard
        if (data.system_stats) {
            renderSystemDashboard(data.system_stats);
        }

        // Render Active Users
        if (data.active_users) {
            renderActiveUsers(data.active_users);
        }

    } catch (e) {
        console.error("Stats fetch error:", e);
    }
}

function renderMatrix(matrixData) {
    if (!matrixData || Object.keys(matrixData).length === 0) {
        matrixContainer.innerHTML = '<div style="color:var(--text-3); text-align:center; padding: 20px;">Belum ada data log untuk membuat matriks.</div>';
        return;
    }

    const levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'];
    const categories = Object.keys(matrixData).sort();

    let html = '<table class="matrix-table"><thead><tr><th>Kategori</th>';
    levels.forEach(lvl => {
        html += `<th>${lvl}</th>`;
    });
    html += '</tr></thead><tbody>';

    categories.forEach(cat => {
        html += `<tr><td class="cat-name">${cat}</td>`;
        levels.forEach(lvl => {
            const count = matrixData[cat][lvl] || 0;
            if (count > 0) {
                let cellClass = 'cell-info';
                if (lvl === 'WARNING') cellClass = 'cell-warning';
                if (lvl === 'ERROR' || lvl === 'CRITICAL') cellClass = 'cell-error';

                html += `<td class="clickable-cell ${cellClass}" onclick="navigateToLiveTail('${cat}', '${lvl}')">${count}</td>`;
            } else {
                html += `<td class="cell-zero">-</td>`;
            }
        });
        html += '</tr>';
    });
    html += '</tbody></table>';
    matrixContainer.innerHTML = html;
}

function formatDuration(seconds) {
    if (!seconds) return '--';
    const s = Math.floor(seconds);
    if (s < 60) return `${s} detik`;
    const m = Math.floor(s / 60);
    const s2 = s % 60;
    if (m < 60) return `${m}m ${s2}s`;
    const h = Math.floor(m / 60);
    const m2 = m % 60;
    return `${h}j ${m2}m`;
}

function parseUserAgent(ua) {
    if (!ua) return { os: 'Unknown OS', browser: 'Unknown Browser', icon: 'ti-device-desktop' };

    let os = 'Unknown OS';
    let icon = 'ti-device-desktop';
    if (ua.includes('Windows')) { os = 'Windows'; icon = 'ti-brand-windows'; }
    else if (ua.includes('Mac OS')) { os = 'macOS'; icon = 'ti-brand-apple'; }
    else if (ua.includes('Linux')) { os = 'Linux'; icon = 'ti-brand-ubuntu'; }
    else if (ua.includes('Android')) { os = 'Android'; icon = 'ti-brand-android'; }
    else if (ua.includes('iPhone') || ua.includes('iPad')) { os = 'iOS'; icon = 'ti-device-mobile'; }

    let browser = 'Unknown Browser';
    if (ua.includes('Firefox')) browser = 'Firefox';
    else if (ua.includes('Edg')) browser = 'Edge';
    else if (ua.includes('Chrome')) browser = 'Chrome';
    else if (ua.includes('Safari')) browser = 'Safari';
    else if (ua.includes('Opera') || ua.includes('OPR')) browser = 'Opera';

    return { os, browser, icon };
}

function getPageName(referer) {
    if (!referer) return 'Unknown Page';
    if (referer.includes('/admin/logs')) return 'Logging Dashboard';
    if (referer.includes('/admin')) return 'Admin Panel';
    if (referer.endsWith('/') || referer.endsWith(':8765') || referer.endsWith('localhost')) return 'Main Player';
    return 'Main Player'; // fallback
}

function renderSystemDashboard(stats) {
    const grid = document.getElementById('sysDashGrid');
    if (!grid) return;

    const cpuStr = stats.cpu_percent !== null ? `${stats.cpu_percent}%` : '--';
    const ramStr = stats.ram_mb !== null ? `${stats.ram_mb} MB` : '--';
    const uptimeStr = stats.uptime_seconds ? formatDuration(stats.uptime_seconds) : '--';

    grid.innerHTML = `
        <div class="sys-card">
            <div class="sys-card-icon"><i class="ti ti-cpu"></i></div>
            <div class="sys-card-val">${cpuStr}</div>
            <div class="sys-card-lbl">CPU Usage</div>
        </div>
        <div class="sys-card">
            <div class="sys-card-icon"><i class="ti ti-device-floppy"></i></div>
            <div class="sys-card-val">${ramStr}</div>
            <div class="sys-card-lbl">RAM Usage</div>
        </div>
        <div class="sys-card">
            <div class="sys-card-icon"><i class="ti ti-player-play-filled"></i></div>
            <div class="sys-card-val">${stats.songs_played || 0}</div>
            <div class="sys-card-lbl">Songs Played</div>
        </div>
        <div class="sys-card">
            <div class="sys-card-icon"><i class="ti ti-music"></i></div>
            <div class="sys-card-val">${stats.total_tracks || 0}</div>
            <div class="sys-card-lbl">Total Tracks</div>
        </div>
        <div class="sys-card">
            <div class="sys-card-icon"><i class="ti ti-users-group"></i></div>
            <div class="sys-card-val">${stats.total_artists || 0}</div>
            <div class="sys-card-lbl">Total Artists</div>
        </div>
        <div class="sys-card">
            <div class="sys-card-icon"><i class="ti ti-clock"></i></div>
            <div class="sys-card-val">${uptimeStr}</div>
            <div class="sys-card-lbl">Uptime</div>
        </div>
    `;
}

function renderActiveUsers(users) {
    const tbody = document.getElementById('activeUsersTbody');
    if (!tbody) return;

    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:var(--text-3); padding:var(--s5);">Tidak ada pengguna aktif</td></tr>';
        return;
    }

    let html = '';
    users.forEach(u => {
        const dev = parseUserAgent(u.user_agent);
        const pageName = getPageName(u.referer);
        html += `
            <tr>
                <td style="font-family:monospace; color:var(--accent); font-weight:bold; vertical-align:middle;">
                    <i class="ti ti-network" style="margin-right:8px; opacity:0.7;"></i>${u.ip || 'Unknown'}
                </td>
                <td style="vertical-align:middle;">
                    <span style="background: rgba(255, 204, 0, 0.1); color: var(--accent); padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600;">
                        ${pageName}
                    </span>
                </td>
                <td style="vertical-align:middle;">
                    <div class="device-badge">
                        <i class="ti ${dev.icon}"></i> ${dev.os} &bull; ${dev.browser}
                    </div>
                </td>
                <td style="vertical-align:middle;">${formatDuration(u.duration)}</td>
                <td style="vertical-align:middle;">
                    <span style="display:inline-flex; align-items:center; gap:6px; color:#22c55e; border:1px solid rgba(34,197,94,0.3); padding:4px 10px; border-radius:12px; font-size:11px; font-weight:600;">
                        <span style="width:6px; height:6px; border-radius:50%; background:#22c55e; box-shadow:0 0 8px #22c55e;"></span> Active
                    </span>
                </td>
                <td style="vertical-align:middle; text-align:right;">
                    ${u.uid ? `
                    <button class="chat-btn" data-uid="${u.uid}" style="background:var(--bg-elevated); border:1px solid var(--border-2); padding:6px 12px; font-size:12px; border-radius:16px; color:var(--text-2); cursor:pointer; display:inline-flex; align-items:center; gap:6px; position:relative;">
                        <i class="ti ti-message-circle"></i> Chat
                        <span class="chat-badge" id="badge-${u.uid}" style="display:none; position:absolute; top:-6px; right:-6px; background:var(--accent); color:var(--accent-dark); width:16px; height:16px; border-radius:50%; font-size:10px; font-weight:bold; align-items:center; justify-content:center;"></span>
                    </button>
                    ` : `<span style="color:var(--text-3); font-size:11px;" title="Client belum memuat modul chat">Chat belum siap</span>`}
                </td>
            </tr>
        `;
    });
    tbody.innerHTML = html;

    // Bind chat buttons (data-uid = client_uid, kunci thread chat --
    // bukan IP, lihat server/handlers/ws_chat.py)
    document.querySelectorAll('.chat-btn').forEach(btn => {
        btn.addEventListener('click', () => openChatPanel(btn.dataset.uid));
    });
}

// Add keyframes for the pulse animation if not exists
if (!document.getElementById('pulse-anim')) {
    const style = document.createElement('style');
    style.id = 'pulse-anim';
    style.innerHTML = `
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.4; }
            100% { opacity: 1; }
        }
    `;
    document.head.appendChild(style);
}

async function fetchTail(clearFirst = false) {
    try {
        const limit = 200;
        const level = filterLevel.value;
        const category = filterCategory.value;
        const q = filterSearch.value;

        const params = new URLSearchParams();
        params.append('limit', limit);
        if (level) params.append('level', level);
        if (category) params.append('category', category);
        if (q) params.append('q', q);

        const token = localStorage.getItem('metricsToken') || '';
        const headers = token ? {'X-Metrics-Token': token} : {};

        const res = await fetch(`/api/logs/tail?${params.toString()}`, { headers });
        if (!res.ok) {
            if (res.status === 403) {
                // Try to prompt for token
                const promptToken = prompt("Metrics token required (localhost bypassing failed):");
                if (promptToken) {
                    localStorage.setItem('metricsToken', promptToken);
                    return fetchTail(clearFirst);
                }
            }
            throw new Error('Failed to fetch tail');
        }

        const data = await res.json();
        if (data.logs) {
            appendLogBatch(data.logs, clearFirst);
        }
    } catch (e) {
        console.error("Tail fetch error:", e);
    }
}

async function fetchHealth() {
    try {
        const res = await fetch('/health');
        if (res.ok) {
            const data = await res.json();
            document.getElementById('ind-db').className = 'status-indicator ' + (data.db === 'connected' ? 'ok' : 'error');
            document.getElementById('ind-mpv').className = 'status-indicator ' + (data.mpv === 'connected' ? 'ok' : 'warn');
            document.getElementById('val-uptime').textContent = `Uptime: ${data.uptime_seconds || 0}s`;
            document.getElementById('val-mem').textContent = `Mem: ${data.memory_mb || 0}MB`;
            document.getElementById('val-conn').textContent = `WS: ${data.active_connections || 0}`;
        }
    } catch (e) {
        console.error("Health fetch error:", e);
    }
}

function fallbackToPolling() {
    if (!isPolling) {
        isPolling = true;
        connBanner.style.display = 'block';
        connBanner.textContent = 'Live tail via WS tidak tersedia (butuh admin login). Beralih ke mode polling.';
        if (pollTimer) clearInterval(pollTimer);
        pollTimer = setInterval(() => fetchTail(false), 2000);
    }
}

function connectWs() {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${proto}//${window.location.host}/ws?page=${encodeURIComponent(window.location.pathname)}`);

    ws.onopen = () => {
        connBanner.style.display = 'none';
        isPolling = false;
        if (pollTimer) clearInterval(pollTimer);

        const adminToken = localStorage.getItem('lunawave_session_token');
        if (adminToken) {
            ws.send(JSON.stringify({
                type: "cmd",
                action: "auth",
                data: { token: adminToken }
            }));
        } else {
            // No admin token, WS log_tail will likely be rejected.
            // Try anyway, it will trigger error fallback.
            ws.send(JSON.stringify({
                type: "cmd",
                action: "log_tail",
                data: { action: "subscribe" }
            }));
        }
    };

    ws.onmessage = (evt) => {
        try {
            const data = JSON.parse(evt.data);

            if (data.type === "auth_status") {
                if (data.data && data.data.success) {
                    ws.send(JSON.stringify({
                        type: "cmd",
                        action: "log_tail",
                        data: { action: "subscribe" }
                    }));
                } else {
                    fallbackToPolling();
                }
            } else if (data.type === "error" && data.data && data.data.includes("Akses ditolak")) {
                fallbackToPolling();
            } else if (data.type === "log_batch" && data.logs) {
                // Apply current filters client-side just to avoid rendering mismatch
                // between ws stream and applied static filters before refetch
                const level = filterLevel.value;
                const category = filterCategory.value;
                const q = filterSearch.value.toLowerCase();

                const filtered = data.logs.filter(log => {
                    if (level && log.level !== level) return false;
                    if (category && (!log.fields || log.fields.category !== category)) return false;
                    if (q && !(log.event.toLowerCase().includes(q) || (log.fields && Object.values(log.fields).join(' ').toLowerCase().includes(q)))) return false;
                    return true;
                });

                if (filtered.length > 0) {
                    appendLogBatch(filtered, false);
                }
            } else if (data.type === "chat_message") {
                handleIncomingChat(data.data);
            } else if (data.type === "chat_history") {
                renderChatHistory(data.data);
            }
        } catch (e) {
            console.error("WS parse error:", e);
        }
    };

    ws.onclose = () => {
        ws = null;
        fallbackToPolling();
    };
}

// DECISION: Download button implementation
// Instead of modifying the backend to add a new static file route just for lunawave.log,
// we utilize the existing `/api/logs/tail` endpoint by requesting a large limit (e.g. 5000 lines).
// We then format the JSON response back into a plain text file format client-side.
// This strictly follows the rule of not adding new endpoints to the server (R-D4 / R-D1 context)
// when an existing API can cover the requirement.
btnDownload.addEventListener('click', async () => {
    btnDownload.disabled = true;
    btnDownload.textContent = "Mengunduh...";

    try {
        const token = localStorage.getItem('metricsToken') || '';
        const headers = token ? {'X-Metrics-Token': token} : {};
        const res = await fetch(`/api/logs/tail?limit=5000`, { headers });
        if (!res.ok) throw new Error('Failed to fetch logs for download');

        const data = await res.json();
        let textData = "";

        if (data.logs) {
            for (const log of data.logs) {
                if (log.level === "BANNER") {
                    textData += `${log.event}\n`;
                } else {
                    const extra = formatFields(log.fields);
                    textData += `[${log.time}] ${log.level}: ${log.event}${extra ? ' ' + extra : ''}\n`;
                }
            }
        }

        const blob = new Blob([textData], { type: "text/plain;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `lunawave_logs_${new Date().getTime()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (e) {
        alert("Gagal mengunduh log: " + e.message);
    } finally {
        btnDownload.disabled = false;
        btnDownload.textContent = "Unduh lunawave.log";
    }
});

btnFilter.addEventListener('click', () => {
    fetchTail(true);
});

window.addEventListener('beforeunload', () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: "cmd",
            action: "log_tail",
            data: { action: "unsubscribe" }
        }));
        ws.close();
    }
});

// Chat Logic -- disegmentasi per client_uid (UUID per-browser client),
// BUKAN per IP. IP tidak reliable sebagai kunci identitas di balik reverse
// proxy (lihat server/handlers/ws_chat.py untuk penjelasan lengkap).
let activeChatUid = null;
let unreadCounts = {};
const dashChatPanel = document.getElementById('dash-chat-panel');
const dashChatClose = document.getElementById('dash-chat-close-btn');
const dashChatMessages = document.getElementById('dash-chat-messages');
const dashChatForm = document.getElementById('dash-chat-form');
const dashChatInput = document.getElementById('dash-chat-input');
const dashChatTargetIp = document.getElementById('dash-chat-target-ip');

function updateBadge(uid) {
    const badge = document.getElementById(`badge-${uid}`);
    if (!badge) return;
    const count = unreadCounts[uid] || 0;
    if (count > 0) {
        badge.style.display = 'flex';
        badge.textContent = count > 9 ? '9+' : count;
        // Make the button highlighted
        badge.parentElement.style.color = 'var(--accent)';
        badge.parentElement.style.borderColor = 'var(--accent)';
    } else {
        badge.style.display = 'none';
        badge.parentElement.style.color = 'var(--text-2)';
        badge.parentElement.style.borderColor = 'var(--border-2)';
    }
}

function openChatPanel(uid) {
    if (!uid) return;
    activeChatUid = uid;
    dashChatTargetIp.textContent = uid;
    dashChatPanel.classList.add('active');
    unreadCounts[uid] = 0;
    updateBadge(uid);

    // Request history
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: "cmd",
            action: "get_chat_history",
            data: { target_uid: uid }
        }));
    }

    setTimeout(() => dashChatInput.focus(), 300);
}

dashChatClose.addEventListener('click', () => {
    dashChatPanel.classList.remove('active');
    activeChatUid = null;
});

dashChatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!activeChatUid) return;
    const msg = dashChatInput.value.trim();
    if (!msg) return;

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: "cmd",
            action: "send_chat",
            data: {
                sender_name: "Admin",
                message: msg,
                target_uid: activeChatUid
            }
        }));
    }
    dashChatInput.value = '';
});

function formatTime(isoStr) {
    if (!isoStr) return '';
    try {
        const d = new Date(isoStr);
        return d.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });
    } catch(e) {
        return '';
    }
}

function createMsgEl(msgData) {
    const { sender_name, message, is_admin, created_at } = msgData;
    const isMe = is_admin;
    const wrapper = document.createElement('div');

    const meta = document.createElement('span');
    meta.className = isMe ? 'dash-chat-me-meta' : 'dash-chat-meta';
    meta.textContent = `${isMe ? 'Admin' : sender_name} • ${formatTime(created_at)}`;

    const bubble = document.createElement('div');
    bubble.className = `dash-chat-msg ${isMe ? 'me' : 'them'}`;
    bubble.textContent = message;

    if (isMe) {
        wrapper.appendChild(bubble);
        wrapper.appendChild(meta);
        wrapper.style.alignSelf = 'flex-end';
        wrapper.style.display = 'flex';
        wrapper.style.flexDirection = 'column';
    } else {
        wrapper.appendChild(meta);
        wrapper.appendChild(bubble);
        wrapper.style.alignSelf = 'flex-start';
        wrapper.style.display = 'flex';
        wrapper.style.flexDirection = 'column';
    }
    return wrapper;
}

function renderChatHistory(messages) {
    dashChatMessages.innerHTML = '';
    messages.forEach(m => {
        dashChatMessages.appendChild(createMsgEl(m));
    });
    dashChatMessages.scrollTop = dashChatMessages.scrollHeight;
}

function handleIncomingChat(msgData) {
    const { client_uid } = msgData;
    if (client_uid === activeChatUid) {
        dashChatMessages.appendChild(createMsgEl(msgData));
        dashChatMessages.scrollTop = dashChatMessages.scrollHeight;
    } else if (client_uid && !msgData.is_admin) {
        // Unread from another client
        unreadCounts[client_uid] = (unreadCounts[client_uid] || 0) + 1;
        updateBadge(client_uid);
    }
}

// Init
fetchHealth();
fetchStats();
fetchTail(true);
connectWs();
setInterval(fetchHealth, 5000);
setInterval(fetchStats, 10000);
