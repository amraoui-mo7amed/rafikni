/**
 * User Management Logic
 * Handles user details view, status toggling, and deletion with confirmations.
 */

const UserManager = {
    init() {
        this.userModal = new bootstrap.Modal(document.getElementById('userModal'));
        this.deleteModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
        this.csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        this.deleteUserId = null;

        // Bind delete confirmation button
        document.getElementById('confirmDeleteBtn').addEventListener('click', () => {
            if (this.deleteUserId) this.executeDelete(this.deleteUserId);
        });
    },

    viewDetails(pk) {
        fetch(`/dashboard/users/${pk}/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(r => r.json())
        .then(res => {
            if (res.success) {
                const d = res.data;
                document.getElementById('modalContent').innerHTML = `
                    <div class="text-center mb-4">
                        <img src="https://ui-avatars.com/api/?name=${d.username}&size=100&background=0D6EFD&color=fff" class="rounded-circle mb-3 shadow-sm border border-4 border-white">
                        <h4 class="mb-0 fw-bold">${d.username}</h4>
                        <span class="badge bg-primary px-3 rounded-pill mt-2">${d.role}</span>
                    </div>
                    <div class="row g-3">
                        <div class="col-6"><div class="small text-muted">البريد الإلكتروني</div><div class="fw-bold text-dark">${d.email}</div></div>
                        <div class="col-6"><div class="small text-muted">رقم الهاتف</div><div class="fw-bold text-dark">${d.phone}</div></div>
                        <div class="col-6"><div class="small text-muted">تاريخ الميلاد</div><div class="fw-bold text-dark">${d.birthdate}</div></div>
                        <div class="col-6"><div class="small text-muted">الحالة</div><div class="fw-bold text-dark">${d.is_active ? 'نشط' : 'محظور'}</div></div>
                        <div class="col-6"><div class="small text-muted">انضم في</div><div class="fw-bold text-dark">${d.date_joined}</div></div>
                        <div class="col-6"><div class="small text-muted">آخر دخول</div><div class="fw-bold text-dark">${d.last_login}</div></div>
                    </div>
                `;
                this.userModal.show();
            }
        });
    },

    toggleStatus(pk, currentIsActive) {
        const action = currentIsActive ? 'حظر' : 'تفعيل';
        Swal.fire({
            title: `هل أنت متأكد من ${action} المستخدم؟`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'نعم، قم بذلك',
            cancelButtonText: 'إلغاء',
            confirmButtonColor: currentIsActive ? '#f59e0b' : '#10b981',
            customClass: {
                confirmButton: 'btn btn-warning px-4 py-2',
                cancelButton: 'btn btn-light px-4 py-2'
            }
        }).then((result) => {
            if (result.isConfirmed) {
                fetch(`/dashboard/users/${pk}/toggle-status/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': this.csrfToken }
                }).then(r => r.json()).then(res => {
                    if (res.success) {
                        Swal.fire('تم بنجاح', res.message, 'success').then(() => location.reload());
                    } else {
                        Swal.fire('خطأ', res.message, 'error');
                    }
                });
            }
        });
    },

    requestDelete(pk) {
        this.deleteUserId = pk;
        this.deleteModal.show();
    },

    executeDelete(pk) {
        const btn = document.getElementById('confirmDeleteBtn');
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> جاري الحذف...';

        fetch(`/dashboard/users/${pk}/delete/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': this.csrfToken }
        })
        .then(r => r.json())
        .then(res => {
            this.deleteModal.hide();
            if (res.success) {
                Swal.fire('تم الحذف', res.message, 'success').then(() => location.reload());
            } else {
                Swal.fire('خطأ', res.message, 'error');
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        })
        .catch(() => {
            Swal.fire('خطأ', 'حدث خطأ غير متوقع', 'error');
            btn.disabled = false;
            btn.innerHTML = originalText;
        });
    }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => UserManager.init());

// Global access for onclick
window.viewUserDetails = (pk) => UserManager.viewDetails(pk);
window.toggleUserStatus = (pk, currentIsActive) => UserManager.toggleStatus(pk, currentIsActive);
window.deleteUser = (pk) => UserManager.requestDelete(pk);
