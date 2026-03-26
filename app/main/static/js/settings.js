document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const avatarInput = document.getElementById('avatar-input');
    const avatarPreview = document.getElementById('avatar-preview');
    const syncStatus = document.getElementById('sync-status');
    const submitTicketBtn = document.getElementById('submitTicketBtn');

    // --- 1. Reactive Save Function ---
    // Automatically saves individual fields to provide a "live" feel.
    const autoSave = async (key, value) => {
        try {
            const response = await fetch('/setting/update-settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [key]: value })
            });

            if (response.ok) {
                showSyncFeedback();
            }
        } catch (err) {
            console.error("Auto-save failed:", err);
        }
    };

    // --- 2. Event Listeners for Live Preferences ---
    document.querySelectorAll('.reactive-setting').forEach(element => {
        element.addEventListener('change', async (e) => {
            const el = e.target;
            const key = el.name; 
            const value = el.type === 'checkbox' ? el.checked : el.value;
            
            // 1. Save to Database (Persona selection)
            await autoSave(key, value);

            // 2. Trigger the Global TTS if voice or language changed
            if (key === 'dictation') {
                window.isAudioEnabled = value;
                if (!value) {
                    window.speechSynthesis.cancel(); // Mute immediately if turned OFF
                } else {
                    // Optional: Give a small audio cue if turned ON
                    speak("Voice responses enabled.");
                }
            }
            
            if (key === 'voice' || key === 'language') {
                window.userVoicePreference = document.getElementById('voicePersona').value;
                window.userLanguagePreference = document.getElementById('preferredLanguage').value;
                
                // Only speak preview if dictation is actually ON
                if (window.isAudioEnabled) {
                    speak(`Voice updated to ${window.userVoicePreference}.`);
                }
            }
        });
    });

    // --- 3. Avatar Upload Logic ---
    if (avatarInput) {
        avatarInput.addEventListener('change', async function() {
            const file = this.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('avatar', file);

            try {
                const response = await fetch('/setting/update-agent-avatar', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                if (response.ok) {
                    // Update preview and show sync success
                    avatarPreview.src = `/${result.path}`;
                    showSyncFeedback();
                }
            } catch (err) {
                console.error("Avatar Upload Error:", err);
            }
        });
    }

    // --- 4. Support Ticket Submission ---
    if (submitTicketBtn) {
        submitTicketBtn.addEventListener('click', async () => {
            const issueType = document.getElementById('issue_type').value;
            const details = document.getElementById('supportDetails').value;
            const $modal = $('#supportModal'); // Helper expects jQuery/Element compatible with toggleModalProcessing
            const $modalBody = $modal.find('.modal-body');
            const $form = $modal.find('form'); // Assuming your inputs are inside a form

            if (!details.trim()) {
                alert("Please describe your issue before submitting.");
                return;
            }

            // STAGE 1: Lock UI
            submitTicketBtn.disabled = true;
            submitTicketBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Sending...';
            toggleModalProcessing($modal, true);

            try {
                const response = await fetch('/user/support-ticket', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ issue_type: issueType, details: details })
                });

                if (response.ok) {
                    // STAGE 2: Success (No need to unlock, we are showing success state)
                    showSuccessState(
                        $modalBody, 
                        "Ticket Received!", 
                        "Our team is on it. Check your email for updates."
                    );

                } else {
                    throw new Error("Failed to send");
                }
            } catch (err) {
                // STAGE 3: Unlock & Error Recovery
                toggleModalProcessing($modal, false);
                console.error("Support Error:", err);
                
                handleFormError($form, "Something went wrong. Please try again later.");
                submitTicketBtn.disabled = false;
                submitTicketBtn.innerHTML = 'Try Again';
            }
        });
    }

    // --- 5. Account Deletion (Manual UI Control) ---
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', async () => {
            const modal = document.getElementById('deleteModal');
            const modalBody = modal.querySelector('.modal-body');
            const header = modal.querySelector('.modal-header');
            const modalFooter = modal.querySelector('.modal-footer');
            const cancelBtn = modalFooter ? modalFooter.querySelector('.btn-light') : null;

            if (!confirm("Warning: This will permanently delete your research history. Continue?")) return;

            // --- STAGE 1: DISABLE (Wait State) ---
            confirmDeleteBtn.disabled = true;
            confirmDeleteBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Wiping Data...';
            
            if (cancelBtn) cancelBtn.disabled = true;

            try {
                const response = await fetch('/user/delete-account', { method: 'DELETE' });
                const data = await response.json(); 

                if (response.ok) {
                    // --- STAGE 2: SUCCESS (Hide & Swap) ---
                    header.removeClass('bg-danger').addClass('bg-success');
                    header.find('.modal-title').html('<i class="bi bi-check-circle-fill me-2"></i>Success');

                    if (modalFooter) modalFooter.style.display = 'none';
                    showSuccessState(
                        modalBody,
                        "Account Wiped",
                        "Your research vault and data have been permanently removed. Redirecting...",
                        () => { window.location.href = response.redirect || '/'; }
                    );
                } else {
                    throw new Error(data.message || 'Deletion failed');
                }

            } catch (err) {
                // --- STAGE 3: ERROR RECOVERY (Restore) ---
                confirmDeleteBtn.disabled = false;
                confirmDeleteBtn.innerHTML = 'Delete Permanently';
                
                if (cancelBtn) cancelBtn.disabled = false;

                // Using your global error helper
                handleFormError($(modalBody), err.message);
            }
        });
    }

    // --- Helper: Visual Sync Feedback ---
    function showSyncFeedback() {
        if (syncStatus) {
            syncStatus.classList.add('sync-active');
            // Remove class using proper Vanilla JS syntax
            setTimeout(() => syncStatus.classList.remove('sync-active'), 2000);
        }
    }
});