/**
 * saved.js - Research Vault Logic (Optimized for Fluidity)
 * Handles real-time filtering, sorting, and deletion with zero layout thrashing.
 */

$(document).ready(function() {

    // --- 1. FILTERING LOGIC (High-Performance Batch Toggle) ---
    $('#filter-options .dropdown-item').on('click', function(e) {
        e.preventDefault();
        const $this = $(this);
        const filterValue = $this.data('filter');

        // Update UI Active State
        $('#filter-options .dropdown-item').removeClass('active');
        $this.addClass('active');

        const $items = $('.vault-item');
        
        // Batch update classes to trigger CSS transitions simultaneously
        $items.each(function() {
            const $item = $(this);
            const itemFileType = $item.data('file-type');
            
            // Logical check for matching
            const isMatch = (filterValue === 'all') || 
                            (filterValue === 'image' && itemFileType === 'image') || 
                            (itemFileType === filterValue);

            if (isMatch) {
                $item.removeClass('item-hidden').addClass('item-visible');
            } else {
                $item.removeClass('item-visible').addClass('item-hidden');
            }
        });
        
        // Delay empty state check slightly to allow CSS transitions to begin
        setTimeout(checkEmptyStates, 300);
    });

    // --- 2. SORTING LOGIC ---
    $('#sort-options .dropdown-item').on('click', function(e) {
        e.preventDefault();
        const $this = $(this);
        const sortType = $this.data('sort');

        $('#sort-options .dropdown-item').removeClass('active');
        $this.addClass('active');

        performSort('#images-container', sortType);
        performSort('#docs-container', sortType);
    });

    function performSort(containerSelector, type) {
        const $container = $(containerSelector);
        const items = $container.children('.vault-item').get();

        items.sort(function(a, b) {
            const valA = $(a).data(type === 'alpha' ? 'title' : 'date');
            const valB = $(b).data(type === 'alpha' ? 'title' : 'date');

            if (type === 'alpha') {
                return valA.toString().localeCompare(valB.toString());
            } else if (type === 'newest') {
                return new Date(valB) - new Date(valA);
            } else if (type === 'oldest') {
                return new Date(valA) - new Date(valB);
            }
            return 0;
        });

        // Use a document fragment for faster DOM re-insertion
        const fragment = document.createDocumentFragment();
        items.forEach(item => fragment.appendChild(item));
        $container[0].appendChild(fragment);
    }

    // --- 3. AJAX DELETION ---
    $('.delete-btn').on('click', function() {
        const $btn = $(this);
        const itemId = $btn.data('id');
        const itemType = $btn.data('type'); 
        const $card = $btn.closest('.vault-item');

        if (confirm("Move this research to the trash? This cannot be undone.")) {
            $btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span>');

            $.ajax({
                url: `/vault/delete/${itemType}/${itemId}`,
                type: 'DELETE',
                success: function() {
                    // Trigger CSS hide before removing from DOM
                    $card.addClass('item-hidden');
                    setTimeout(() => {
                        $card.remove();
                        checkEmptyStates();
                    }, 300);
                },
                error: function() {
                    alert("Error removing item. Please try again.");
                    $btn.prop('disabled', false).html('<i class="bi bi-trash"></i>');
                }
            });
        }
    });

    /**
     * Shows the "No items found" message with a smooth fade-in
     */
    function checkEmptyStates() {
        $('.tab-pane').each(function() {
            const $pane = $(this);
            const activeFilter = $('#filter-options .dropdown-item.active').text().trim();
            const visibleCount = $pane.find('.vault-item.item-visible').length;
            const $emptyState = $pane.find('.empty-state-container'); // Note: targeting the new container
            
            if (visibleCount === 0) {
                $emptyState.find('.filter-name').text(activeFilter);
                $emptyState.addClass('is-empty-active');
            } else {
                $emptyState.removeClass('is-empty-active');
            }
        });
    }

    // Run once on load to initialize visibility
    $('.vault-item').addClass('item-visible');
});