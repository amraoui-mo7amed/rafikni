document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token from cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Handle delete buttons with SweetAlert
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', function() {
            const deleteUrl = this.dataset.deleteUrl;
            const row = this.closest('tr');
            const caseName = row.querySelector('.fw-bold').textContent;

            Swal.fire({
                title: 'هل أنت متأكد؟',
                html: 'هل تريد حذف الحالة الطبية <strong>' + caseName + '</strong>؟<br>لا يمكن التراجع عن هذا الإجراء!',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#dc3545',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'نعم، احذفها!',
                cancelButtonText: 'إلغاء',
                reverseButtons: true
            }).then((result) => {
                if (result.isConfirmed) {
                    // Create form and submit for DELETE
                    const form = document.createElement('form');
                    form.method = 'POST';
                    form.action = deleteUrl;

                    const csrfToken = getCookie('csrftoken');
                    const csrfInput = document.createElement('input');
                    csrfInput.type = 'hidden';
                    csrfInput.name = 'csrfmiddlewaretoken';
                    csrfInput.value = csrfToken;

                    form.appendChild(csrfInput);
                    document.body.appendChild(form);
                    form.submit();
                }
            });
        });
    });

    // Handle view details buttons - Bootstrap Modal
    const caseModalEl = document.getElementById('caseDetailsModal');
    const caseModal = new bootstrap.Modal(caseModalEl);

    document.querySelectorAll('.btn-view').forEach(btn => {
        btn.addEventListener('click', function() {
            const caseType = this.dataset.caseType;

            // Populate basic info
            document.getElementById('modalCaseName').textContent = this.dataset.caseName;
            document.getElementById('modalCaseAge').textContent = this.dataset.caseAge + ' سنة';
            document.getElementById('modalCaseGender').textContent = this.dataset.caseGender;
            document.getElementById('modalCaseAphasie').textContent = this.dataset.caseAphasie;

            // Update status badge with animation
            const typeBadge = document.getElementById('modalCaseTypeBadge');
            const typeText = document.getElementById('modalCaseType');
            typeBadge.className = 'status-badge-lg ' + caseType;
            typeText.textContent = this.dataset.caseTypeDisplay;

            // Populate owner info (for admin)
            const ownerEl = document.getElementById('modalCaseOwner');
            if (ownerEl) {
                ownerEl.textContent = this.dataset.caseOwner;
            }

            // Helper function to create tags from comma-separated values
            function createTags(containerId, valuesString) {
                const container = document.getElementById(containerId);
                container.innerHTML = '';
                
                if (!valuesString || valuesString === '-' || valuesString === 'لا يوجد') {
                    container.innerHTML = '<span class="text-muted">لا يوجد</span>';
                    return;
                }
                
                // Split by both English comma (,) and Arabic comma (،)
                const values = valuesString.split(/[,،]/).map(v => v.trim()).filter(v => v);
                
                if (values.length === 0) {
                    container.innerHTML = '<span class="text-muted">لا يوجد</span>';
                    return;
                }
                
                values.forEach(value => {
                    const tag = document.createElement('span');
                    tag.className = 'tag-badge';
                    tag.textContent = value;
                    container.appendChild(tag);
                });
            }

            // Show/hide category-specific fields with animation
            const childFields = document.getElementById('modalChildFields');
            const elderlyFields = document.getElementById('modalElderlyFields');

            if (childFields) {
                if (caseType === 'child') {
                    childFields.style.display = 'block';
                    createTags('modalDisorders', this.dataset.caseDisorders);
                    createTags('modalSyndromes', this.dataset.caseSyndromes);
                    document.getElementById('modalDisability').textContent = this.dataset.caseDisability || 'لا يوجد';
                } else {
                    childFields.style.display = 'none';
                }
            }

            if (elderlyFields) {
                if (caseType === 'elderly') {
                    elderlyFields.style.display = 'block';
                    document.getElementById('modalAlzheimer').textContent = this.dataset.caseAlzheimer;
                    document.getElementById('modalParkinson').textContent = this.dataset.caseParkinson;
                } else {
                    elderlyFields.style.display = 'none';
                }
            }

            // Show the modal
            caseModal.show();
        });
    });
});
