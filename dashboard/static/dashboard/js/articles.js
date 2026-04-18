/**
 * Article Management JavaScript
 * Handles AJAX requests for article deletion with SweetAlert confirmation.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Handle Article Deletion
    const articlesTable = document.getElementById('articlesTable');
    if (articlesTable) {
        articlesTable.addEventListener('click', function(e) {
            const deleteBtn = e.target.closest('.delete-article');
            if (deleteBtn) {
                const url = deleteBtn.getAttribute('data-url');
                const csrfToken = deleteBtn.getAttribute('data-csrf');

                Swal.fire({
                    title: 'هل أنت متأكد؟',
                    text: "لن تتمكن من استعادة هذا المقال!",
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
                        })
                        .catch(error => {
                            Swal.fire('خطأ!', 'حدث خطأ أثناء الاتصال بالخادم.', 'error');
                        });
                    }
                });
            }
        });
    }
});

/**
 * Previews the hero image when a file is selected.
 * @param {HTMLInputElement} input 
 */
function previewHeroImage(input) {
    const preview = document.getElementById('heroPreview');
    const content = document.getElementById('heroContent');
    const uploadBox = document.getElementById('heroUpload');
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
            if (content) content.style.display = 'none';
            uploadBox.classList.add('has-image');
        }
        reader.readAsDataURL(input.files[0]);
    }
}
