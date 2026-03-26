/* ==========================================================================
   ATTACHMENTS.JS - MODULAR FILE HANDLING & PREVIEWS
   ========================================================================== */

/**
 * Global AttachmentManager to handle file selection, validation, and UI previews.
 */
window.AttachmentManager = {
    /**
     * File configuration for icons and colors
     */
    CONFIG: {
        'pdf':  { icon: 'bi-file-earmark-pdf-fill', color: 'text-danger' },
        'docx': { icon: 'bi-file-earmark-word-fill', color: 'text-primary' },
        'doc':  { icon: 'bi-file-earmark-word-fill', color: 'text-primary' },
        'xlsx': { icon: 'bi-file-earmark-excel-fill', color: 'text-success' },
        'xls':  { icon: 'bi-file-earmark-excel-fill', color: 'text-success' },
        'pptx': { icon: 'bi-file-earmark-slides-fill', color: 'text-warning' },
        'ppt':  { icon: 'bi-file-earmark-slides-fill', color: 'text-warning' },
        'txt':  { icon: 'bi-file-earmark-text-fill', color: 'text-secondary' }
    },

    getFileContext: function(filename) {
        if (!filename) return { icon: 'bi-file-earmark', color: 'text-muted' };
        const ext = filename.split('.').pop().toLowerCase();
        return this.CONFIG[ext] || { icon: 'bi-file-earmark-fill', color: 'text-muted' };
    },

    isImage: function(filename) {
        return /\.(jpg|jpeg|png|webp|gif)$/i.test(filename);
    },

    /**
     * Renders a preview bubble above the input field
     */
    renderPreview: function(file, containerSelector) {
        const $container = $(containerSelector);
        $container.attr('class', 'd-flex gap-2 px-3 mb-2 animate__animated animate__fadeIn').empty();

        if (this.isImage(file.name)) {
            const reader = new FileReader();
            reader.onload = (e) => {
                $container.append(`
                    <div class="position-relative d-inline-block attachment-preview-item">
                        <img src="${e.target.result}" class="rounded border shadow-sm" 
                             style="width: 60px; height: 60px; object-fit: cover;">
                        <button type="button" 
                                class="btn-close btn-close-white position-absolute top-0 start-100 translate-middle bg-danger rounded-circle shadow-sm" 
                                style="padding: 0.2rem; font-size: 0.5rem;" 
                                onclick="AttachmentManager.clear()"></button>
                    </div>`);
            };
            reader.readAsDataURL(file);
        } else {
            const ctx = this.getFileContext(file.name);
            $container.append(`
                <div class="badge bg-white text-dark border p-2 rounded-3 d-flex align-items-center shadow-sm attachment-preview-item">
                    <i class="bi ${ctx.icon} ${ctx.color} fs-5 me-2"></i>
                    <span class="text-truncate fw-medium" style="max-width: 150px;">${file.name}</span>
                    <button type="button" class="btn-close ms-2" style="font-size: 0.5rem;" 
                            onclick="AttachmentManager.clear()"></button>
                </div>`);
        }
    },

    /**
     * Resets the file input and clears the UI
     */
    clear: function() {
        const $fileInput = $('#hidden-file-input');
        const $preview = $('#attachment-preview');
        
        $fileInput.val(''); 
        $preview.empty().addClass('d-none'); 
        
        // Sync UI state (returns to voice button if text is empty)
        $('#chat-input-field').trigger('input');
    }
};

/* ==========================================================================
   EVENT HANDLERS
   ========================================================================== */

$(document).ready(function() {
    // 1. Handle Attachment Dropdown Selections
    $(document).on('click', '.attach-option', function(e) {
        e.preventDefault();
        const type = $(this).data('type');
        const $input = $('#hidden-file-input');
        
        const accepts = {
            'img': 'image/*',
            'doc': '.pdf, .docx, .doc, .xlsx, .xls, .pptx, .ppt, .txt'
        };
        
        $input.attr('accept', accepts[type] || '*/*').click();
    });

    // 2. Handle File Selection
    $(document).on('change', '#hidden-file-input', function() {
        const file = this.files[0];
        if (file) {
            AttachmentManager.renderPreview(file, '#attachment-preview');
            
            // Switch UI from Voice to Send icon
            $('#voice-input-btn').addClass('d-none').removeClass('d-flex');
            $('#send-btn').removeClass('d-none').addClass('d-flex');
        }
    });
});