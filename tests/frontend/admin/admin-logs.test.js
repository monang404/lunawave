import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

describe('Admin Logs Orchestrator', () => {
    beforeEach(() => {
        // Setup minimal DOM needed for admin-logs.js
        document.body.innerHTML = `
            <button id="btnFilter"></button>
            <button id="btnDownload"></button>
            <select id="filterLevel"></select>
            <select id="filterCategory"></select>
            <input id="filterSearch" type="text" />
            <button class="tab-btn" data-tab="live"></button>
            <div id="tab-live" class="tab-content"></div>
        `;

        vi.mock('../../../web/static/pages/admin-logs/log-tail.js', () => ({
            appendLogBatch: vi.fn(),
            navigateToLiveTail: vi.fn(),
            formatFields: vi.fn()
        }));
        vi.mock('../../../web/static/pages/admin-logs/dashboard-stats.js', () => ({
            fetchStats: vi.fn()
        }));
        vi.mock('../../../web/static/pages/admin-logs/admin-ws-transport.js', () => ({
            connectWs: vi.fn(),
            fallbackToPolling: vi.fn(),
            fetchTail: vi.fn(),
            fetchHealth: vi.fn(),
            sendOverWs: vi.fn(),
            disconnectWs: vi.fn(),
            setAppendLogBatch: vi.fn()
        }));
        vi.mock('../../../web/static/pages/admin-logs/admin-chat-panel.js', () => ({
            handleIncomingChat: vi.fn(),
            renderChatHistory: vi.fn(),
            openChatPanel: vi.fn()
        }));
    });

    afterEach(() => {
        vi.resetModules();
        vi.restoreAllMocks();
        document.body.innerHTML = '';
    });

    it('loads and initializes properly', async () => {
        await import('../../../web/static/pages/admin-logs/admin-logs.js');
        const adminWs = await import('../../../web/static/pages/admin-logs/admin-ws-transport.js');
        const dashboardStats = await import('../../../web/static/pages/admin-logs/dashboard-stats.js');

        expect(adminWs.fetchHealth).toHaveBeenCalled();
        expect(dashboardStats.fetchStats).toHaveBeenCalled();
        expect(adminWs.fetchTail).toHaveBeenCalledWith(true);
        expect(adminWs.connectWs).toHaveBeenCalled();
    });

    it('listens for chat:open custom event', async () => {
        await import('../../../web/static/pages/admin-logs/admin-logs.js');
        const adminChat = await import('../../../web/static/pages/admin-logs/admin-chat-panel.js');

        document.dispatchEvent(new CustomEvent('chat:open', {
            detail: { uid: 'user-123', ip: '127.0.0.1' }
        }));

        expect(adminChat.openChatPanel).toHaveBeenCalledWith('user-123', '127.0.0.1');
    });
});
