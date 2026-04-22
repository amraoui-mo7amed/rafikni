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

    // Handle Order Details Modal
    const viewDetailBtns = document.querySelectorAll('.view-order-details');
    viewDetailBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Close any open status dropdowns first
            document.querySelectorAll('.status-dropdown-list').forEach(l => l.classList.remove('show'));
            document.querySelectorAll('.game-status-picker').forEach(p => p.classList.remove('open'));
            document.querySelectorAll('.status-current').forEach(c => c.classList.remove('active'));

            const data = this.dataset;
            document.getElementById('modalOrderId').textContent = `#${data.id}`;
            document.getElementById('modalCustomerName').textContent = data.name;
            document.getElementById('modalCustomerType').textContent = data.type;
            document.getElementById('modalCustomerPhone').textContent = data.phone;
            document.getElementById('modalCustomerPhone').href = `tel:${data.phone}`;
            document.getElementById('modalWilaya').textContent = data.wilaya;
            document.getElementById('modalCommune').textContent = data.commune;
            document.getElementById('modalAddress').textContent = data.address;

            const modal = new bootstrap.Modal(document.getElementById('orderDetailModal'));
            modal.show();
        });
    });

    // Close status dropdowns on outside click
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.game-status-picker')) {
            document.querySelectorAll('.status-dropdown-list').forEach(list => list.classList.remove('show'));
            document.querySelectorAll('.status-current').forEach(curr => curr.classList.remove('active'));
        }
    });
});

/**
 * Toggles the custom status dropdown.
 */
function toggleStatusDropdown(orderId) {
    const list = document.getElementById(`status-list-${orderId}`);
    const picker = document.querySelector(`.game-status-picker[data-order-id="${orderId}"]`);
    const current = list.previousElementSibling;
    
    // Close others
    document.querySelectorAll('.status-dropdown-list').forEach(l => {
        if (l.id !== `status-list-${orderId}`) {
            l.classList.remove('show');
            l.closest('.game-status-picker').classList.remove('open');
        }
    });
    
    list.classList.toggle('show');
    current.classList.toggle('active');
    picker.classList.toggle('open');
}

/**
 * Updates the order status via AJAX.
 */
function updateOrderStatus(orderId, newValue, newLabel) {
    const picker = document.querySelector(`.game-status-picker[data-order-id="${orderId}"]`);
    const url = picker.dataset.url;
    const csrfToken = picker.dataset.csrf;
    const labelSpan = picker.querySelector('.status-label');
    const list = document.getElementById(`status-list-${orderId}`);

    fetch(url, {
        method: 'POST',
        body: new URLSearchParams({ 'status': newValue }),
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI
            labelSpan.textContent = newLabel;
            list.querySelectorAll('.status-option').forEach(opt => {
                opt.classList.remove('active');
                if (opt.dataset.value === newValue) opt.classList.add('active');
            });
            
            // Close dropdown
            list.classList.remove('show');
            picker.querySelector('.status-current').classList.remove('active');

            // Success feedback
            Swal.mixin({
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 3000
            }).fire({
                icon: 'success',
                title: data.message
            });
        } else {
            Swal.fire('خطأ!', data.errors.join('\n'), 'error');
        }
    })
    .catch(() => {
        Swal.fire('خطأ!', 'حدث خطأ أثناء الاتصال بالخادم.', 'error');
    });
}

/**
 * Previews multiple gallery images before upload.
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
