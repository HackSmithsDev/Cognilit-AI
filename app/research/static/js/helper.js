/* ==========================================================================
    CORE CHAT HELPERS
   ========================================================================== */

let isListening = false;
let selectedGenerationType = null; 

/**
 * Smoothly scrolls chat to the bottom
 */
function scrollToBottom() {
    const chatContainer = document.getElementById('chat-container');
    if (!chatContainer) return;

    setTimeout(() => {
        window.requestAnimationFrame(() => {
            chatContainer.scrollTo({
                top: chatContainer.scrollHeight,
                behavior: 'smooth'
            });
        });
    }, 50);
}

/**
 * Appends a message bubble to the chat container
 */
function appendMessage(role, text, time, fileUrl = null, chatId = null, fileType = null) {
    const isAi = role === 'ai' || role === 'agent';
    
    $('#typing-indicator').remove();

    // 1. ATTACHMENT LOGIC
    let attachmentHtml = '';
    if (fileUrl) {
        let type = fileType ? fileType.toLowerCase() : "";
        if (!type) {
            const extensionMatch = fileUrl.match(/\.([a-z0-9]+)(?:[\?#]|$)/i);
            type = extensionMatch ? extensionMatch[1].toLowerCase() : "text";
        }

        const isImage = ['jpg', 'jpeg', 'png', 'webp', 'gif'].includes(type);
        let previewHtml = '';

        if (isImage) {
            previewHtml = `
                <div class="message-image-container">
                    <img src="${fileUrl}" class="rounded-3 img-fluid border shadow-sm" 
                         style="max-height: 250px; cursor: zoom-in; background: #f8f9fa;" 
                         onclick="window.open(this.src, '_blank')" alt="Research Image">
                </div>`;
        } else {
            const config = {
                pdf:  { icon: 'bi-file-earmark-pdf-fill', color: 'text-danger' },
                doc:  { icon: 'bi-file-earmark-word-fill', color: 'text-primary' },
                docx: { icon: 'bi-file-earmark-word-fill', color: 'text-primary' },
                xls:  { icon: 'bi-file-earmark-excel-fill', color: 'text-success' },
                xlsx: { icon: 'bi-file-earmark-excel-fill', color: 'text-success' }
            };

            const icon = config[type]?.icon || 'bi-file-earmark-text-fill';
            const color = config[type]?.color || 'text-secondary';
            const rawName = fileUrl.split('/').pop();
            const displayName = rawName.includes('_') ? rawName.split('_').slice(1).join('_') : rawName;

            previewHtml = `
                <div class="p-2 bg-light border rounded-3 d-flex align-items-center text-dark" 
                     style="cursor: pointer;" onclick="window.open('${fileUrl}', '_blank')">
                    <i class="bi ${icon} ${color} fs-3 me-2"></i>
                    <span class="small fw-bold text-truncate" style="max-width: 180px;">${displayName}</span>
                </div>`;
        }

        attachmentHtml = `
            <div class="attachment-wrapper position-relative mb-2">
                ${previewHtml}
                <div class="mt-1 vault-action-area" id="vault-container-${chatId}">
                    <button class="btn btn-sm p-0 ${isAi ? 'text-muted' : 'text-white-50'} hover-primary" 
                            onclick="saveToVault('${chatId}')" id="save-btn-${chatId}" title="Save to Vault">
                        <i class="bi bi-bookmark-plus me-1"></i>
                        <span style="font-size: 0.65rem;">Save to Vault</span>
                    </button>
                </div>
            </div>`;
    }

    // 2. AVATAR & CONTENT
    const avatarHtml = isAi ? `
        <div class="d-flex align-items-center mb-2 ms-2">
            <img src="/${agent_avatar_path}" width="24" height="24" class="me-2 rounded-circle" alt="AI">
            <span class="fw-bold small text-primary">${agent_name}</span>
        </div>` : '';

    const messageTextHtml = text ? `
        <div class="message-text">
            ${text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}
        </div>` : '';

    // 3. RENDER
    const finalHtml = `
        <div class="message-group mb-4 d-flex flex-column ${isAi ? 'align-items-start ai-message' : 'align-items-end user-message'}" data-chat-id="${chatId || ''}">
            ${avatarHtml}
            <div class="message-bubble rounded-4 shadow-sm border ${isAi ? 'bg-white' : 'bg-primary text-white'} px-3 py-2">
                ${attachmentHtml}
                ${messageTextHtml}
            </div>
            <small class="text-muted mt-1 px-2" style="font-size: 0.7rem;">${time}</small>
        </div>`;

    $('#chat-container').append(finalHtml);
    scrollToBottom();
}

/**
 * UI Loading State
 */
function showTypingIndicator() {
    if ($('#typing-indicator').length) return;
    
    const html = `
        <div id="typing-indicator" class="message-group mb-4 ai-message d-flex flex-column align-items-start animate__animated animate__fadeIn">
            <div class="d-flex align-items-center mb-2 ms-2">
                <img src="/${agent_avatar_path}" width="24" height="24" class="me-2 rounded-circle" alt="AI">
                <span class="fw-bold small text-primary">${agent_name}</span>
            </div>
            <div class="message-bubble ai-bubble shadow-sm border px-3 py-2">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>`;
    $('#chat-container').append(html);
    scrollToBottom();
}

/**
 * Logic for initial load and curriculum guidance
 */
function handleInitialState() {
    const query = sessionStorage.getItem('pending_query');
    const hasHistory = $('.message-group').length > 0;

    if (query) {
        sessionStorage.removeItem('pending_query');
        const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        appendMessage('user', query, now);
        showTypingIndicator();
        sendMessageToServer(query, null);
    } else if (!hasHistory) {
        const welcomeHtml = `
            <div class="message-group mb-4 ai-message d-flex flex-column align-items-start">
                <div class="d-flex align-items-center mb-2">
                    <img src="/${agent_avatar_path}" width="24" height="24" class="me-2 rounded-circle">
                    <span class="fw-bold small text-primary">${agent_name}</span>
                </div>
                <div class="message-bubble rounded-4 shadow-sm px-3 py-2">
                    <strong>New Research Session Started.</strong><br><br>
                    I've initialized your workspace. I'm ready to help you analyze, 
                    structure, and synthesize your data. 
                    <br><br>
                    What is the core focus of our research today?
                </div>
            </div>`;
        $('#chat-container').append(welcomeHtml);
        scrollToBottom();
    }
}