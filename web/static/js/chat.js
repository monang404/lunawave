// web/static/js/chat.js

(function () {
    const fab = document.getElementById('chat-fab');
    const panel = document.getElementById('chat-panel');
    const closeBtn = document.getElementById('chat-close-btn');
    const badge = document.getElementById('chat-unread-badge');
    const msgContainer = document.getElementById('chat-messages');
    const form = document.getElementById('chat-form');
    const inputMsg = document.getElementById('chat-msg-input');
    const inputName = document.getElementById('chat-name-input');

    let unreadCount = 0;
    let isOpen = false;

    // Load saved name
    const savedName = localStorage.getItem('chat_name');
    if (savedName) {
        inputName.value = savedName;
    }

    function toggleChat() {
        isOpen = !isOpen;
        if (isOpen) {
            panel.classList.add('open');
            unreadCount = 0;
            updateBadge();
            // Scroll to bottom
            setTimeout(() => {
                msgContainer.scrollTop = msgContainer.scrollHeight;
                inputMsg.focus();
            }, 300);
        } else {
            panel.classList.remove('open');
        }
    }

    fab.addEventListener('click', toggleChat);
    closeBtn.addEventListener('click', toggleChat);

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const msg = inputMsg.value.trim();
        let name = inputName.value.trim();

        if (!name) name = "Anonymous";

        if (msg && window.wsSend) {
            localStorage.setItem('chat_name', name);
            window.wsSend('send_chat', {
                sender_name: name,
                message: msg
            });
            inputMsg.value = '';
        }
    });

    function formatTime(timestamp) {
        const d = new Date(timestamp * 1000);
        const hh = d.getHours().toString().padStart(2, '0');
        const mm = d.getMinutes().toString().padStart(2, '0');
        return `${hh}:${mm}`;
    }

    function renderMessage(msgData) {
        const { sender_name, message, is_admin, created_at } = msgData;
        const myName = inputName.value.trim() || "Anonymous";
        const isMine = sender_name === myName && !is_admin;

        const wrap = document.createElement('div');
        wrap.className = 'chat-msg-wrap ' + (isMine ? 'mine' : 'others');

        let adminBadge = is_admin ? '<span class="admin-badge">ADMIN</span>' : '';

        wrap.innerHTML = `
            <div class="chat-sender-name">${sender_name} ${adminBadge}</div>
            <div class="chat-bubble">${message.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div>
            <div class="chat-time">${formatTime(created_at)}</div>
        `;

        msgContainer.appendChild(wrap);

        if (isOpen) {
            msgContainer.scrollTop = msgContainer.scrollHeight;
        } else {
            unreadCount++;
            updateBadge();
        }
    }

    function updateBadge() {
        if (unreadCount > 0) {
            badge.style.display = 'flex';
            badge.textContent = unreadCount > 9 ? '9+' : unreadCount;
        } else {
            badge.style.display = 'none';
        }
    }

    // Export API for ws.js to call
    window.ChatModule = {
        onHistory: (messages) => {
            msgContainer.innerHTML = '';
            messages.forEach(msg => renderMessage(msg));
            if (isOpen) msgContainer.scrollTop = msgContainer.scrollHeight;
        },
        onNewMessage: (msg) => {
            renderMessage(msg);
        }
    };

    // Auto-fetch history on load if connected
    setTimeout(() => {
        if (window.store && window.store.is_online && window.wsSend) {
            window.wsSend('get_chat_history');
        }
    }, 1500);

})();
