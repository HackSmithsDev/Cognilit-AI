document.addEventListener('DOMContentLoaded', () => {
    // Using Event Delegation: Attach one listener to the document
    // This is more robust for dynamic UI changes and nested icons
    document.addEventListener('click', async function(e) {
        const btn = e.target.closest('.resolve-btn');
        if (!btn) return;

        const ticketId = btn.getAttribute('data-id');
        const row = document.getElementById(`row-${ticketId}`);
        
        // Visual feedback: Start loading
        const originalContent = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>';

        try {
            // Keeping your original endpoint logic
            const response = await fetch(`/admin/dashboard/reviews/resolve/${ticketId}`, { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                // 1. Update row styling (Matching refined UI class)
                row.classList.add('resolved-opacity');
                
                // 2. Update Status Column (Targeting the centered icon cell)
                // We find the cell by looking for the status-dot or the specific column
                const statusCell = row.querySelector('.d-md-table-cell.text-center');
                if (statusCell) {
                    statusCell.innerHTML = `
                        <div class="d-flex align-items-center justify-content-center text-success small fw-medium">
                            <i class="bi bi-check-circle-fill me-2"></i>
                        </div>
                    `;
                }
                // 3. Remove the resolve button
                btn.remove();
            } else {
                throw new Error('Server returned an error');
            }
        } catch (err) {
            console.error("Resolve failed:", err);
            alert("Could not update ticket. Please try again.");
            btn.disabled = false;
            btn.innerHTML = originalContent;
        }
    });
});