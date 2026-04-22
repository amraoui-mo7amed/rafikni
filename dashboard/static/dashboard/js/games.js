/**
 * Game Management Dashboard JS
 */
document.addEventListener('DOMContentLoaded', function() {
    // Handle Game Deletion
    const gamesTable = document.getElementById('gamesTable');
    if (gamesTable) {
        gamesTable.addEventListener('click', function(e) {
            const deleteBtn = e.target.closest('.delete-game');
            if (deleteBtn) {
                const url = deleteBtn.getAttribute('data-url');
                const csrfToken = deleteBtn.getAttribute('data-csrf');

                Swal.fire({
                    title: 'هل أنت متأكد؟',
                    text: "سيتم حذف اللعبة نهائياً!",
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#d33',
                    cancelButtonColor: '#3085d6',
                    confirmButtonText: 'نعم، احذف',
                    cancelButtonText: 'إلغاء'
                }).then((result) => {
                    if (result.isConfirmed) {
                        fetch(url, {
                            method: 'POST',
                            headers: {
                                'X-CSRFToken': csrfToken,
                                'X-Requested-With': 'XMLHttpRequest'
                            }
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                Swal.fire('تم!', data.message, 'success').then(() => {
                                    location.reload();
                                });
                            } else {
                                Swal.fire('خطأ!', data.errors.join('\n'), 'error');
                            }
                        });
                    }
                });
            }
        });
    }

    // Handle Order Status Update
    const ordersTable = document.getElementById('ordersTable');
    if (ordersTable) {
        ordersTable.addEventListener('change', function(e) {
            const statusSelect = e.target.closest('.order-status-select');
            if (statusSelect) {
                const url = statusSelect.getAttribute('data-url');
                const csrfToken = statusSelect.getAttribute('data-csrf');
                const newStatus = statusSelect.value;

                fetch(url, {
                    method: 'POST',
                    body: new URLSearchParams({ 'status': newStatus }),
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const toast = Swal.mixin({
                            toast: true,
                            position: 'top-end',
                            showConfirmButton: false,
                            timer: 3000
                        });
                        toast.fire({
                            icon: 'success',
                            title: data.message
                        });
                    } else {
                        Swal.fire('خطأ!', data.errors.join('\n'), 'error');
                    }
                });
            }
        });
    }
});

/**
 * Previews multiple gallery images before upload.
 * @param {HTMLInputElement} input 
 */
function previewGalleryImages(input) {
    const container = document.getElementById('galleryPreviewContainer');
    if (!container) return;

    if (input.files) {
        Array.from(input.files).forEach(file => {
            const reader = new FileReader();
            reader.onload = function(e) {
                const col = document.createElement('div');
                col.className = 'col-3';
                col.innerHTML = `
                    <div class="rounded-3 overflow-hidden shadow-sm border border-primary" style="height: 80px; position: relative;">
                        <img src="${e.target.result}" class="w-100 h-100" style="object-fit: cover;">
                        <span class="badge bg-primary position-absolute top-0 start-0 m-1" style="font-size: 0.6rem;">جديد</span>
                    </div>
                `;
                container.appendChild(col);
            }
            reader.readAsDataURL(file);
        });
    }
}
