/* ==========================================================================
    COMMUNICATION & VAULT LOGIC
   ========================================================================== */

/**
 * Sends user message and attachments to the server
 */
async function sendMessageToServer(message, file = null, clientChatId = null) {
    const formData = new FormData();
    formData.append('message', message);
    
    if (selectedGenerationType) formData.append('generation_type', selectedGenerationType);
    if (file) formData.append('file', file);
    if (clientChatId) formData.append('chat_id', clientChatId);

    try {
        const response = await $.ajax({
            url: `/api/session/${CURRENT_SESSION_ID}/send`,
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false
        });

        if (response.status === 'success') {
            // Unlock the local "Save to Vault" button if a file was uploaded
            if (clientChatId) {
                $(`#save-btn-${clientChatId}`).prop('disabled', false).css('opacity', '1');
            }
            selectedGenerationType = null;
            $('.generation-chip').removeClass('active');

            // Render AI response
            appendMessage(
                'ai', 
                response.ai_message, 
                response.timestamp, 
                response.ai_file_url, 
                response.ai_chat_id,
                response.ai_file_type
            );

            // Trigger Text-to-Speech if enabled
            if (window.isAudioEnabled && typeof speak === 'function') {
                speak(response.ai_message);
            }
        }
    } catch (error) {
        console.error("Chat Error:", error);
        if (error.status === 429) {
            appendMessage('ai', "Slow down! You've reached the limit. Please wait a few minutes before sending another message.", "System");
        } else {
            appendMessage('ai', "I encountered an error. Please try again.", "Just now");
        }
        $('#typing-indicator').remove();
        
        if (clientChatId) {
            $(`#save-btn-${clientChatId}`).closest('.vault-action-area')
                .html('<span class="text-danger small"><i class="bi bi-exclamation-circle"></i> Upload failed</span>');
        }
    }
}

/**
 * Promotes a specific message/file to the permanent Research Vault
 */
window.saveToVault = function(chatId) {
    const $container = $(`#vault-container-${chatId}`); 
    const $btn = $(`#save-btn-${chatId}`);
    
    $btn.html('<i class="bi bi-hourglass-split"></i> Saving...').prop('disabled', true);

    $.ajax({
        url: `/api/message/${chatId}/save`,
        method: 'POST',
        success: function(response) {
            if (response.status === 'success') {
                $container.html(`
                    <span class="text-success small fw-bold animate__animated animate__fadeIn">
                        <i class="bi bi-bookmark-check-fill me-1"></i> Saved to Vault
                    </span>
                `);
            }
        },
        error: function(xhr) {
            const errorMsg = xhr.responseJSON?.message || "Failed to save.";
            alert(errorMsg);
            $btn.html('<i class="bi bi-bookmark-plus"></i> Save to Vault').prop('disabled', false);
        }
    });
};

/**
 * Updates user settings in the background
 */
async function autoSave(key, value) {
    try {
        const response = await fetch('/setting/update-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [key]: value })
        });
        
        const data = await response.json();
        if (response.ok) {
            console.log(`Setting [${key}] updated:`, data.message);
        }
    } catch (err) {
        console.error("Auto-save failed:", err);
    }
}