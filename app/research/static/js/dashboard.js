/**
 * PROJECT & SESSION MANAGEMENT
 * Handles renaming and RESTful deletion of research subjects.
 */

$(document).ready(function() {

    /* ==========================================================================
       1. SESSION (SUBJECT) MANAGEMENT
       ========================================================================== */

    /**
     * RENAME SESSION (POST)
     * Updates the session name and triggers a brief highlight effect
     */
    $(document).on('click', '.rename-session-btn', function(e) {
        e.preventDefault();
        const $btn = $(this);
        const sessionId = $btn.data('id');
        const oldName = $btn.data('current');
        
        const newName = prompt("Rename Research Session:", oldName);

        if (newName && newName.trim() !== "" && newName.trim() !== oldName) {
            $.ajax({
                url: `/api/session/${sessionId}/rename`,
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ new_name: newName.trim() }),
                success: function(res) {
                    // 1. Update the local UI (List/Card)
                    const $item = $btn.closest('.list-group-item');
                    const $heading = $item.find('h6');
                    
                    $heading.text(res.new_name);
                    $btn.data('current', res.new_name).hide().fadeIn(500);
                    
                    // 2. Update the Sidebar Sync
                    // We target the span inside our specifically ID'd li
                    const $sidebarSpan = $(`#sidebar-session-li-${sessionId}`).find('span.text-truncate');
                    if ($sidebarSpan.length) {
                        $sidebarSpan.text(res.new_name).hide().fadeIn(500);
                    }
                    
                    // Visual feedback: brief highlight
                    $heading.addClass('text-primary');
                    setTimeout(() => $heading.removeClass('text-primary'), 1000);
                },
                error: function(xhr) {
                    alert("Rename failed: " + (xhr.responseJSON?.message || "Server error"));
                }
            });
        }
    });

    /**
     * DELETE SESSION (DELETE)
     * Removes session from list and updates global counter
     */
    $(document).on('click', '.delete-session-btn', function(e) {
        e.preventDefault();
        const $btn = $(this);
        const sessionId = $btn.data('id');
        const sessionName = $btn.data('name');
        const $item = $btn.closest('.list-group-item');

        if (!confirm(`Permanently delete session "${sessionName}"?\nThis will remove all research messages and citations.`)) {
            return;
        }

        $.ajax({
            url: `/api/session/${sessionId}/delete`,
            type: 'DELETE',
            success: function() {
                $item.fadeOut(300, function() { 
                    $(this).remove();
                    
                    // 1. Update the "Total Sessions" UI count
                    const $countDisplay = $('.card.bg-primary h2.fw-bold'); 
                    let currentCount = parseInt($countDisplay.text());
                    if (!isNaN(currentCount) && currentCount > 0) {
                        $countDisplay.text(currentCount - 1);
                    }

                    // 2. If zero items remain, swap the list with the placeholder
                    if ($('.list-group-item').length === 0) {
                        $('.list-group').replaceWith(`
                            <div class="text-center py-5 animate__animated animate__fadeIn">
                                <i class="bi bi-chat-left-dots fs-1 text-muted"></i>
                                <p class="mt-3 text-muted">No sessions found in this project.</p>
                            </div>
                        `);
                    }
                    if (sessionId) {
                        const $sessionLi = $(`#sidebar-session-li-${sessionId}`);
                        $sessionLi.fadeOut(400, function() {                        
                            $(this).remove();
                        });
                    }
                });
            },
            error: function(xhr) {
                alert("Delete failed: " + (xhr.responseJSON?.message || "Check your connection"));
            }
        });
    });

    /* ==========================================================================
       2. PROJECT (WORKSPACE) MANAGEMENT
       ========================================================================== */

    /**
     * DELETE ENTIRE PROJECT (DELETE)
     * Destroys the workspace and redirects user
     */
    $(document).on('click', '.delete-project-btn', function(e) {
        e.preventDefault();
        const $btn = $(this);
        const projectId = $btn.data('id');
        const projectName = $btn.data('name');
        const redirectUrl = $btn.data('redirect');

        const warningMsg = `WARNING: You are about to delete "${projectName}".\n\n` +
                          `This will permanently destroy all 5 subjects and 25+ chapters within this project. ` +
                          `This action cannot be undone.`;

        if (confirm(warningMsg)) {
            // UI Feedback: Loading state
            $btn.prop('disabled', true).html(`
                <span class="spinner-border spinner-border-sm me-2"></span>Deleting Workspace...
            `);

            $.ajax({
                url: `/api/project/${projectId}/delete`,
                type: 'DELETE',
                success: function() {
                    window.location.href = redirectUrl;
                },
                error: function(xhr) {
                    alert("Error: " + (xhr.responseJSON?.message || "Could not delete project."));
                    $btn.prop('disabled', false).html('<i class="bi bi-trash me-2"></i>Delete Workspace');
                }
            });
        }
    });
});