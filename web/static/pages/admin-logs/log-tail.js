/**
 * log-tail.js
 * Domain: append/render baris log individual + navigasi filter dari matrix cell
 */
import { fetchTail } from "./admin-ws-transport.js";

const logContainer = document.getElementById('logContainer');
const autoScrollCheckbox = /** @type {HTMLInputElement} */ (document.getElementById('autoScroll'));
const filterLevel = /** @type {HTMLSelectElement} */ (document.getElementById('filterLevel'));
const filterCategory = /** @type {HTMLSelectElement} */ (document.getElementById('filterCategory'));
const seenLogs = new Set();

export function navigateToLiveTail(cat, level) {
    /** @type {HTMLElement} */
    (document.querySelector('.tab-btn[data-tab="live"]')).click();
    filterCategory.value = cat;
    filterLevel.value = level;
    fetchTail(true);
}
export function escapeHtml(unsafe) {
    if (!unsafe) return "";
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}
export function formatFields(fields) {
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
export function getLevelIcon(level) {
    switch (level) {
        case 'INFO': return '<i class="ti ti-info-circle"></i>';
        case 'WARNING': return '<i class="ti ti-alert-triangle"></i>';
        case 'ERROR':
        case 'CRITICAL': return '<i class="ti ti-circle-x"></i>';
        case 'DEBUG': return '<i class="ti ti-bug"></i>';
        default: return '<i class="ti ti-point-filled"></i>';
    }
}
export function createLogLineElement(log) {
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
export function appendLogBatch(logs, clearFirst = false) {
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
