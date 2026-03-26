$(document).ready(function() {
    // --- Global Selectors ---
    const $sidebar = $('#sidebar');
    const $overlay = $('#sidebar-overlay');
    const $menuToggle = $('#menu-toggle');

    /**
     * 1. SIDEBAR & LAYOUT LOGIC
     */
    function toggleSidebar() {
        const isOpening = $sidebar.hasClass('sidebar-hidden');
        
        $sidebar.toggleClass('sidebar-hidden sidebar-visible');
        $overlay.toggleClass('overlay-active');

        if (isOpening) {
            $menuToggle.find('i').addClass('d-none');
        } else {
            $menuToggle.find('i').removeClass('d-none');
        }
    }

    $(document).on('click', '#menu-toggle, #menu-close, #sidebar-overlay, .close-sidebar-btn', function(e) {
        toggleSidebar();
    });

    $(window).on('resize', function() {
        if (window.innerWidth >= 992 && $sidebar.hasClass('sidebar-visible')) {
            $overlay.removeClass('overlay-active'); 
        }
    });


    /**
     * 2. CURRICULUM & NAVIGATION LOGIC
     */
    function initNavigation() {
        const currentPath = window.location.pathname;
        
        $('.nav-link, .sidebar-chapter-link').each(function() {
            const $link = $(this);
            const linkHref = $link.attr('href');

            const isHome = (linkHref === '/' && currentPath === '/');
            const isSubPage = (linkHref !== '/' && currentPath.includes(linkHref));

            if (isHome || isSubPage) {
                $link.addClass('active bg-primary-subtle text-primary fw-bold');
                
                const $collapse = $link.closest('.collapse');
                if ($collapse.length) {
                    $collapse.addClass('show');
                    $collapse.closest('.nav-item-wrapper')
                             .find('[data-bs-toggle="collapse"]')
                             .attr('aria-expanded', 'true');
                }
            }
        });
    }
    initNavigation();

    /**
     * 4. AVATAR UPLOAD LOGIC
     */
    $('#avatar-upload').on('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;

        if (!file.type.startsWith('image/')) {
            alert('Please select an image file.');
            return;
        }
        if (file.size > 2 * 1024 * 1024) { 
            alert('Image is too large (Limit: 2MB).');
            return;
        }

        const reader = new FileReader();
        reader.onload = function(event) {
            $('.rounded-circle[alt="User Profile"], .avatar-large').attr('src', event.target.result);
        };
        reader.readAsDataURL(file);

        const formData = new FormData();
        formData.append('avatar', file);

        $.ajax({
            url: '/user/update-user-avatar',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                console.log("Avatar updated:", response.path);
            },
            error: function() {
                alert('Failed to save avatar to server.');
            }
        });
    });

    document.getElementById('logout-link')?.addEventListener('click', function(e) {
        e.preventDefault();
        fetch("/user/logout", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => { if (data.redirect) window.location.href = data.redirect; })
        .catch(err => console.error("Logout failed:", err));
    });
});