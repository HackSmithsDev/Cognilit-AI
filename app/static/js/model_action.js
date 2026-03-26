window.openNewSessionModal = function(projectId, projectName) {
    const selector = document.getElementById('project-selector');
    const projectInputGroup = document.getElementById('new-project-input-group');
    const newProjectNameInput = document.getElementById('new_project_name');

    if (selector) {
        selector.value = projectId;
        projectInputGroup.classList.add('d-none');
        newProjectNameInput.removeAttribute('required');
        
        const modal = new bootstrap.Modal(document.getElementById('initiateResearchModal'));
        modal.show();
    }
}

/**
 * Helper: Toggles Modal Security State
 * @param {jQuery} $modalBody - The modal element
 * @param {boolean} isProcessing - True to lock, False to unlock
 * @param {string} title - Success title
 * @param {string} message - Success description
 * @param {function} callback - Default is location.reload
 * @param {number} delay - Default 2000ms
 */
function toggleModalProcessing($modalBody, isProcessing) {
    if (!$modalBody || $modalBody.length === 0) return; // Prevent "undefined" errors

    const $closeBtn = $modalBody.find('.btn-close');
    const modalElement = $modalBody[0];
    
    // Use getOrCreateInstance to ensure we always have the object
    const modalInstance = bootstrap.Modal.getOrCreateInstance(modalElement);

    if (isProcessing) {
        // 1. Hide the 'X' button
        $closeBtn.fadeOut(200);
        
        // 2. Lock the backdrop and keyboard
        if (modalInstance) {
            modalInstance._config.backdrop = 'static';
            modalInstance._config.keyboard = false;
        }
    } else {
        // 1. Restore the 'X' button
        $closeBtn.fadeIn(200);
        
        // 2. Unlock backdrop and keyboard
        if (modalInstance) {
            modalInstance._config.backdrop = true;
            modalInstance._config.keyboard = true;
        }
    }
}

/**
 * Helper: Inline Error Handler
 */
function handleFormError($form, message) {
    // Remove existing errors to prevent duplicates
    $form.find('.form-error-msg').remove();
    
    $form.prepend(`
        <div class="alert alert-danger small py-2 animate-fade-in form-error-msg">
            <i class="bi bi-exclamation-triangle-fill me-2"></i>${message}
        </div>
    `);
}

/**
 * Helper: Success State Switcher
 */
function showSuccessState($modalBody, title, message, callback = () => location.reload(), delay = 2500) {
    // 1. Render Success UI (Removed data-bs-dismiss)
    $modalBody.html(`
        <div class="text-center py-4 animate__animated animate__fadeIn">
            <div class="mb-3">
                <div class="success-icon-circle d-flex align-items-center justify-content-center mx-auto bg-success bg-opacity-10 text-success rounded-circle" style="width: 80px; height: 80px;">
                    <i class="bi bi-check-circle-fill" style="font-size: 3rem;"></i>
                </div>
            </div>
            <h5 class="fw-bold text-dark">${title}</h5>
            <p class="text-muted small mb-3">${message}</p>
            <button type="button" id="success-done-btn" class="btn btn-primary btn-sm px-4">
                Great, thanks
            </button>
        </div>
    `);

    let actionTriggered = false;

    // Internal function to ensure the callback only runs once
    const runAction = () => {
        if (!actionTriggered) {
            actionTriggered = true;
            if (callback && typeof callback === 'function') {
                callback();
            }
        }
    };

    // 2. Manual Click Trigger
    $modalBody.find('#success-done-btn').on('click', function() {
        runAction();
    });

    // 3. Automated Timer Trigger
    setTimeout(() => {
        // Only trigger if the modal is still open/visible
        if ($.contains(document, $modalBody[0])) {
            runAction();
        }
    }, delay);
}



$(document).ready(function() {

    $('.modal').on('hidden.bs.modal', function () {
        // Only reload if a success state was reached
        if ($(this).find('.text-success').length > 0) {
            $('body').css('opacity', '0.5');
            location.reload();
        }
    });
    /**

    /**
     * PROFILE UPDATE
     */
    $('#form-update').on('submit', function(e) {
        e.preventDefault();
        const $form = $(this);
        const $btn = $form.find('button[type="submit"]');
        const $modal = $form.closest('.modal'); // FIX: Define $modal here
        const $modalBody = $form.closest('.modal-body');

        const originalText = $btn.text();
        
        // STAGE 1: Lock UI
        $btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-2"></span>Updating...');
        toggleModalProcessing($modal, true);

        $.ajax({
            url: '/user/update-details',
            type: 'POST',
            data: $form.serialize(),
            success: function(response) {
                // STAGE 2: Success State (No need to unlock, we are showing success UI)
                
                showSuccessState(
                    $modalBody, 
                    "Profile Updated!", 
                    "Your changes have been saved successfully. The page will refresh shortly."
                );
            },
            error: function(xhr) {
                // STAGE 3: Unlock & Recovery
                toggleModalProcessing($modal, false);
                
                const errorMsg = xhr.responseJSON?.message || 'Update failed';
                handleFormError($form, errorMsg);
                $btn.prop('disabled', false).text(originalText);
            }
        });
    });

    /**
     * PASSWORD CHANGE
     */
    $('#password-change-form').on('submit', function(e) {
        e.preventDefault();
        
        const $form = $(this);
        const $btn = $form.find('button[type="submit"]');
        const $modal = $form.closest('.modal'); // FIX: Define $modal here
        const $modalBody = $form.closest('.modal-body');
        
        const oldP = $('#old-p').val();
        const newP = $('#new-p').val();
        const confP = $('#conf-p').val();

        // Client-side validation
        if (newP !== confP) {
            handleFormError($form, "New passwords do not match!");
            return;
        }

        // STAGE 1: Lock UI
        const originalText = $btn.text();
        $btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-2"></span>Updating...');
        toggleModalProcessing($modal, true);

        $.ajax({
            url: '/user/change-password',
            type: 'POST',
            data: { old_password: oldP, new_password: newP },
            success: function(response) {
                // STAGE 2: Success
                toggleModalProcessing($modal, false);
                showSuccessState(
                    $modalBody, 
                    "Security Updated", 
                    "Your password has been changed. You will be redirected shortly."
                );
            },
            error: function(xhr) {
                // STAGE 3: Unlock & Recovery
                toggleModalProcessing($modal, false);

                const errorMsg = xhr.responseJSON?.message || 'Failed to update password.';
                handleFormError($form, errorMsg);
                $btn.prop('disabled', false).text(originalText);
            }
        });
    });
    /**
     * RESEARCH MODAL DYNAMIC UI LOGIC
     */
    $('#project-selector').on('change', function() {
        const val = $(this).val();
        const $projectInputGroup = $('#new-project-input-group');
        const $newProjectNameInput = $('#new_project_name');

        if (val === "NEW_PROJECT") {
            $projectInputGroup.removeClass('d-none');
            $newProjectNameInput.attr('required', 'required');
        } else {
            $projectInputGroup.addClass('d-none');
            $newProjectNameInput.removeAttr('required');
        }
    });

    /**
     * NEW RESEARCH SESSION AJAX SUBMISSION
     * Intercepts the form submission to use AJAX instead of traditional POST.
     */
    $('#research-init-form').on('submit', function(e) {
        e.preventDefault();
        const $form = $(this);
        const $btn = $form.find('button[type="submit"]');
        const $modal = $form.closest('.modal'); // Defined to prevent ReferenceError
        
        const selection = $('#project-selector').val();
        const targetUrl = (selection === "NEW_PROJECT") ? '/api/project/new' : '/api/session/add';

        const formData = {
            project_id: selection,
            project_name: $('#new_project_name').val(),
            session_name: $('#new_session_name').val(),
        };

        const originalText = $btn.text();

        // --- STAGE 1: LOCKDOWN ---
        $btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-2"></span>Initializing...');
        toggleModalProcessing($modal, true);

        $.ajax({
            url: targetUrl,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                // Note: No showSuccessState here as we are redirecting immediately
                if (response.redirect_url) {
                    window.location.href = response.redirect_url;
                }
            },
            error: function(xhr) {
                // --- STAGE 2: REVERSE ON ERROR ---
                toggleModalProcessing($modal, false);
                
                const errorMsg = xhr.responseJSON?.message || 'Failed to Initialize Project.';
                handleFormError($form, errorMsg);
                $btn.prop('disabled', false).text(originalText);
            }
        });
    });
});