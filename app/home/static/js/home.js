document.addEventListener('DOMContentLoaded', () => {
    const mainInput = document.getElementById('main-input');
    const $submitBtn = $('[aria-label="Start Research"]');
    const projectCards = document.querySelectorAll('.project-card');

    /**
     * 1. Search Logic: Triggers the Global Modal
     */
    const handleResearchQuery = () => {
        const query = mainInput.value.trim();
        
        if (!query) {
            mainInput.classList.add('is-invalid');
            return;
        }

        // Disable button and show spinner
        $submitBtn.disabled = true;
        $submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';

        sessionStorage.setItem('pending_query', query);

        const $formData = {
            'project_name': 'New Research Session',
            'session_name': query.substring(0, 30) + (query.length > 30 ? '...' : ''),
        };

        $.ajax({
            url: '/api/project/new',
            type: 'POST',
            data: JSON.stringify($formData),
            contentType: 'application/json',
            success: function(response) {
                if (response.redirect_url) {
                    window.location.href = response.redirect_url;
                } else {
                    window.location.href = '/'; 
                }
            },
            error: function(xhr) {
                const errorMsg = xhr.responseJSON?.message || 'Could not create project. Please try again.';
                alert('Error: ' + errorMsg);
                
                $submitBtn.disabled = false;
                $submitBtn.innerHTML = '<i class="bi bi-stars"></i>';
            }
        });
    };

    // Trigger on Button Click
    $submitBtn.on('click', function(e) {
        e.preventDefault();
        handleResearchQuery();
    });

    // Trigger on 'Enter' Key
    mainInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleResearchQuery();
        }
    });

    /**
     * 2. Card Interaction: Subtle hover/click logic
     */
    projectCards.forEach(card => {
        card.addEventListener('click', (e) => {
            // Prevent triggering if clicking interactive elements
            if (e.target.closest('.dropdown') || e.target.closest('a') || e.target.closest('button')) return;

            const openLink = card.querySelector('a.btn-primary');
            if (openLink) {
                window.location.href = openLink.getAttribute('href');
            }
        });
    });

    /**
     * 3. UI Polish
     */
    mainInput?.addEventListener('input', () => {
        mainInput.classList.remove('is-invalid');
    });

    /**
     * PROJECT MANAGEMENT (RENAME & DELETE)
     */

    // 1. RENAME (POST)
    $(document).on('click', '.rename-project-btn', function() {
        const id = $(this).data('id');
        const oldName = $(this).data('current-name');
        const newName = prompt("Rename Project:", oldName);

        if (newName && newName.trim() !== "" && newName !== oldName) {
            $.ajax({
                url: `/api/project/${id}/rename`,
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ new_name: newName.trim() }),
                success: (res) => {
                    // 1. Update the Card Title on the Home Page
                    $(this).closest('.card-body').find('.card-title').text(res.new_name);
                    
                    // 2. Update the button's data attribute for future renames
                    $(this).data('current-name', res.new_name).hide().fadeIn(500);

                    // 3. Update the Sidebar Label
                    // We find the <small> tag inside our specifically ID'd project block
                    const $sidebarLabel = $(`#sidebar-project-block-${id}`).find('.sidebar-project-label');
                    if ($sidebarLabel.length) {
                        $sidebarLabel.text(res.new_name).hide().fadeIn(500);
                    }
                },
                error: (xhr) => alert(xhr.responseJSON?.message || "Rename failed")
            });
        }
    });

    // 2. DELETE (DELETE)
    $(document).on('click', '.delete-project-btn', function() {
        const id = $(this).data('id');
        const name = $(this).data('name');
        const $card = $(this).closest('.col-md-6');

        if (confirm(`Permanently delete "${name}"?`)) {
            $.ajax({
                url: `/api/project/${id}/delete`,
                type: 'DELETE',
                success: () => {
                    $card.fadeOut(300, function() { $(this).remove(); });
                    const $sidebarBlock = $(`#sidebar-project-block-${id}`);
                    if ($sidebarBlock.length) {
                        $sidebarBlock.fadeOut(300, function() {
                            $(this).remove();
                        });
                    }
                },
                error: (xhr) => alert(xhr.responseJSON?.message || "Delete failed")
            });
        }
    });
});