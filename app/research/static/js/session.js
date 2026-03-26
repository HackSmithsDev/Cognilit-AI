/* ==========================================================================
    EVENT LISTENERS & INITIALIZATION
   ========================================================================== */

$(document).ready(function() {
    const $inputField = $('#chat-input-field');
    const $voiceBtn = $('#voice-input-btn');
    const $sendBtn = $('#send-btn');
    const $fileInput = $('#hidden-file-input');

    // 0. BOOERLAN NORMALIZATION (Fixes the first-click bug)
    if (typeof window.isAudioEnabled === 'string') {
        window.isAudioEnabled = (window.isAudioEnabled.toLowerCase() === 'true');
    }

    // 1. VOLUME TOGGLE LOGIC
    $('#volume-toggle-btn').on('click', async function() {
        // Toggle the global state
        window.isAudioEnabled = !window.isAudioEnabled;
        
        const $icon = $('#volume-icon');
        const $btn = $(this);
        
        if (window.isAudioEnabled) {
            $btn.addClass('btn-primary').removeClass('btn-light');
            $icon.removeClass('bi-volume-up').addClass('bi-volume-up-fill');
        } else {
            $btn.removeClass('btn-primary').addClass('btn-light');
            $icon.removeClass('bi-volume-up-fill').addClass('bi-volume-up');
            window.speechSynthesis.cancel();
        }

        // Persist to database
        await autoSave('dictation', window.isAudioEnabled);
    });

    // 2. GENERATION TYPE CHIPS
    $('.generation-chip').on('click', function() {
        const type = $(this).attr('id') === 'chip-pdf' ? 'pdf' : 'image';

        if (selectedGenerationType === type) {
            selectedGenerationType = null;
            $(this).removeClass('active');
        } else {
            $('.generation-chip').removeClass('active');
            selectedGenerationType = type;
            $(this).addClass('active');
        }
    });

    // 3. INPUT UI MANAGEMENT (Toggle Voice/Send icons)
    $inputField.on('input', function() {
        const hasText = $(this).val().trim().length > 0;
        $voiceBtn.toggleClass('d-none', hasText).toggleClass('d-flex', !hasText);
        $sendBtn.toggleClass('d-none', !hasText).toggleClass('d-flex', hasText);
    });

    // 4. MESSAGE SUBMISSION LOGIC
    $sendBtn.on('click', async function() {
        const message = $inputField.val().trim();
        const file = $fileInput[0].files[0];

        if (message || file) {
            const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const localFileUrl = file ? URL.createObjectURL(file) : null;
            let clientChatId = null;
            let fileType = null;

            if (file) {
                fileType = file.name.split('.').pop().toLowerCase();
                // Secure UUID generation
                clientChatId = Array.from(crypto.getRandomValues(new Uint8Array(20))).map(b => (b % 36).toString(36)).join('');
            }

            // UI Update: Append user message
            appendMessage('user', message, now, localFileUrl, clientChatId, fileType);
            
            // Cleanup: Attachments and Input
            if (window.AttachmentManager) window.AttachmentManager.clear();
            else { $('#attachment-preview').empty().addClass('d-none'); $fileInput.val(''); }

            $inputField.val('').trigger('input');

            // Server Handoff
            showTypingIndicator();
            await sendMessageToServer(message, file, clientChatId);
        }
    });

    // Keyboard Shortcut (Enter to Send)
    $inputField.on('keydown', function(e) {
        if (e.which === 13 && !e.shiftKey) {
            e.preventDefault();
            $sendBtn.click();
        }
    });

    // 5. SPEECH RECOGNITION (STT)
    const recognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (recognition) {
        const speechApi = new recognition();
        const currentLang = window.userLanguagePreference || 'English (US)';
        
        speechApi.lang = currentLang === 'Hindi' ? 'hi-IN' : (currentLang === 'Spanish' ? 'es-ES' : 'en-US');
        speechApi.continuous = false;
        speechApi.interimResults = true;

        $voiceBtn.on('click', () => {
            if (window.speechSynthesis.isSpeaking) window.speechSynthesis.cancel();
            if (!isListening) {
                try { speechApi.start(); } catch (err) { isListening = true; }
            } else { speechApi.stop(); }
        });

        speechApi.onstart = () => {
            isListening = true;
            $('#mic-icon').addClass('text-danger pulse');
            $inputField.attr('placeholder', 'Listening...');
        };

        speechApi.onresult = (event) => {
            const transcript = Array.from(event.results).map(r => r[0].transcript).join('');
            $inputField.val(transcript).trigger('input');
            
            if (event.results[0].isFinal) {
                isListening = false;
                speechApi.stop();
                setTimeout(() => $sendBtn.click(), 600);
            }
        };

        speechApi.onend = () => {
            isListening = false;
            $('#mic-icon').removeClass('text-danger pulse');
            $inputField.attr('placeholder', 'Type a message...');
        };

        speechApi.onerror = (e) => {
            isListening = false;
            $('#mic-icon').removeClass('text-danger pulse');
            console.error("Speech Recognition Error:", e.error);
        };
    }

    // 6. INITIALIZATION
    scrollToBottom();
    handleInitialState();
});