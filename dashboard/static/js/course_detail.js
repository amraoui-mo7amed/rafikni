/**
 * Course Detail JavaScript
 * Handles enrollment and video upload for admins
 */

document.addEventListener('DOMContentLoaded', function() {
    // Enroll button
    const enrollBtn = document.querySelector('.btn-enroll');
    
    if (enrollBtn) {
        enrollBtn.addEventListener('click', function() {
            const courseId = this.dataset.courseId;
            const coursePrice = parseFloat(this.dataset.coursePrice);
            
            enrollBtn.disabled = true;
            enrollBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> جاري التسجيل...';
            
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', getCsrfToken());
            
            fetch(`/dashboard/courses/${courseId}/enroll/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                enrollBtn.disabled = false;
                
                if (data.success) {
                    if (data.requires_payment) {
                        window.location.href = `/dashboard/courses/payment/${data.enrollment_id}/submit/`;
                    } else {
                        Swal.fire({
                            title: 'تم التسجيل بنجاح!',
                            text: 'يمكنك الآن مشاهدة جميع الفيديوهات',
                            icon: 'success',
                            confirmButtonText: 'حسناً',
                            confirmButtonColor: '#0d6efd'
                        }).then(() => {
                            window.location.reload();
                        });
                    }
                } else {
                    enrollBtn.innerHTML = '<i class="fa-solid fa-user-plus me-2"></i> تسجيل';
                    Swal.fire({
                        title: 'خطأ',
                        text: data.errors ? data.errors[0] : 'حدث خطأ أثناء التسجيل',
                        icon: 'error',
                        confirmButtonText: 'حسناً'
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                enrollBtn.disabled = false;
                enrollBtn.innerHTML = '<i class="fa-solid fa-user-plus me-2"></i> تسجيل';
                Swal.fire({
                    title: 'خطأ',
                    text: 'حدث خطأ في الاتصال بالخادم',
                    icon: 'error',
                    confirmButtonText: 'حسناً'
                });
            });
        });
    }
    
    // Delete button
    const deleteBtn = document.querySelector('.btn-delete-course');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            const deleteUrl = this.dataset.deleteUrl;
            
            Swal.fire({
                title: 'هل أنت متأكد؟',
                text: 'سيتم حذف الدورة وجميع الفيديوهات المرتبطة بها!',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#dc3545',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'نعم، احذف',
                cancelButtonText: 'إلغاء'
            }).then((result) => {
                if (result.isConfirmed) {
                    deleteCourse(deleteUrl);
                }
            });
        });
    }
    
    // Video upload functionality (admin only)
    const videoFileInput = document.getElementById('videoFileInput');
    const uploadVideoBtn = document.getElementById('uploadVideoBtn');
    const uploadDropzone = document.querySelector('.upload-dropzone');
    
    if (videoFileInput && uploadDropzone) {
        // Click to select file
        uploadDropzone.addEventListener('click', function(e) {
            if (!e.target.closest('.btn-remove-file')) {
                videoFileInput.click();
            }
        });
        
        // Drag and drop
        uploadDropzone.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadDropzone.classList.add('drag-over');
        });
        
        uploadDropzone.addEventListener('dragleave', function() {
            uploadDropzone.classList.remove('drag-over');
        });
        
        uploadDropzone.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadDropzone.classList.remove('drag-over');
            
            if (e.dataTransfer.files.length > 0) {
                videoFileInput.files = e.dataTransfer.files;
                handleVideoSelect(e.dataTransfer.files[0]);
            }
        });
        
        // File input change
        videoFileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                handleVideoSelect(this.files[0]);
            }
        });
        
        // Remove file button
        document.addEventListener('click', function(e) {
            if (e.target.closest('.btn-remove-file')) {
                videoFileInput.value = '';
                hideFileInfo();
                if (uploadVideoBtn) uploadVideoBtn.disabled = true;
            }
        });
    }
    
    function handleVideoSelect(file) {
        // Validate file type
        const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm'];
        if (!validTypes.includes(file.type)) {
            Swal.fire({
                title: 'خطأ',
                text: 'يرجى اختيار ملف فيديو صالح (MP4, AVI, MOV, MKV)',
                icon: 'error',
                confirmButtonText: 'حسناً'
            });
            videoFileInput.value = '';
            return;
        }
        
        // Validate file size (500MB max)
        const maxSize = 500 * 1024 * 1024;
        if (file.size > maxSize) {
            Swal.fire({
                title: 'خطأ',
                text: 'حجم الملف كبير جداً. الحد الأقصى 500MB',
                icon: 'error',
                confirmButtonText: 'حسناً'
            });
            videoFileInput.value = '';
            return;
        }
        
        // Show file info
        showFileInfo(file);
        
        // Enable upload button
        if (uploadVideoBtn) {
            uploadVideoBtn.disabled = false;
        }
    }
    
    function showFileInfo(file) {
        const fileInfo = document.querySelector('.file-info');
        const fileName = fileInfo.querySelector('.file-name');
        const fileSize = fileInfo.querySelector('.file-size');
        
        // Format file size
        const sizeInMB = (file.size / (1024 * 1024)).toFixed(2);
        
        fileName.textContent = file.name;
        fileSize.textContent = `(${sizeInMB} MB)`;
        fileInfo.classList.remove('d-none');
    }
    
    function hideFileInfo() {
        const fileInfo = document.querySelector('.file-info');
        fileInfo.classList.add('d-none');
    }
    
    // Upload video button click
    if (uploadVideoBtn) {
        uploadVideoBtn.addEventListener('click', function() {
            const file = videoFileInput.files[0];
            const title = document.querySelector('input[name="title"]').value;
            const description = document.querySelector('textarea[name="description"]').value;
            const courseId = window.location.pathname.split('/').filter(Boolean).pop();
            
            if (!title.trim()) {
                Swal.fire({
                    title: 'خطأ',
                    text: 'يرجى إدخال عنوان الفيديو',
                    icon: 'error',
                    confirmButtonText: 'حسناً'
                });
                return;
            }
            
            if (!file) {
                Swal.fire({
                    title: 'خطأ',
                    text: 'يرجى اختيار ملف الفيديو',
                    icon: 'error',
                    confirmButtonText: 'حسناً'
                });
                return;
            }
            
            const formData = new FormData();
            formData.append('video_file', file);
            formData.append('title', title);
            formData.append('description', description);
            formData.append('csrfmiddlewaretoken', getCsrfToken());
            
            // Show progress
            uploadVideoBtn.disabled = true;
            uploadVideoBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> جاري الرفع...';
            
            // Show progress container
            const progressContainer = document.querySelector('.upload-progress');
            const progressBar = document.querySelector('.progress-bar');
            const progressPercentage = document.querySelector('.progress-percentage');
            const statusText = document.querySelector('.status-text');
            
            progressContainer.classList.remove('d-none');
            progressBar.style.width = '0%';
            progressPercentage.textContent = '0%';
            statusText.textContent = 'جاري التحضير...';
            
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', function(e) {
                if (e.lengthComputable) {
                    const percentComplete = Math.round((e.loaded / e.total) * 100);
                    progressBar.style.width = percentComplete + '%';
                    progressPercentage.textContent = percentComplete + '%';
                    statusText.textContent = `جاري الرفع... ${percentComplete}%`;
                }
            });
            
            xhr.addEventListener('load', function() {
                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        progressBar.style.width = '100%';
                        progressPercentage.textContent = '100%';
                        statusText.textContent = 'اكتمل الرفع!';
                        
                        Swal.fire({
                            title: 'تم!',
                            text: 'تم رفع الفيديو بنجاح',
                            icon: 'success',
                            confirmButtonText: 'حسناً'
                        }).then(() => {
                            window.location.reload();
                        });
                    } else {
                        Swal.fire({
                            title: 'خطأ',
                            text: response.errors ? response.errors[0] : 'حدث خطأ أثناء رفع الفيديو',
                            icon: 'error',
                            confirmButtonText: 'حسناً'
                        });
                        resetUploadButton();
                    }
                } else {
                    Swal.fire({
                        title: 'خطأ',
                        text: 'حدث خطأ في الاتصال بالخادم',
                        icon: 'error',
                        confirmButtonText: 'حسناً'
                    });
                    resetUploadButton();
                }
            });
            
            xhr.addEventListener('error', function() {
                Swal.fire({
                    title: 'خطأ',
                    text: 'حدث خطأ في الاتصال بالخادم',
                    icon: 'error',
                    confirmButtonText: 'حسناً'
                });
                resetUploadButton();
            });
            
            xhr.open('POST', `/dashboard/courses/${courseId}/videos/upload/`);
            xhr.send(formData);
        });
    }
    
    function resetUploadButton() {
        if (uploadVideoBtn) {
            uploadVideoBtn.disabled = false;
            uploadVideoBtn.innerHTML = '<i class="fa-solid fa-upload me-2"></i> رفع الفيديو';
        }
        const progressContainer = document.querySelector('.upload-progress');
        if (progressContainer) progressContainer.classList.add('d-none');
    }
    
    function deleteCourse(deleteUrl) {
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', getCsrfToken());
        
        fetch(deleteUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                Swal.fire({
                    title: 'تم الحذف!',
                    text: 'تم حذف الدورة بنجاح',
                    icon: 'success',
                    confirmButtonText: 'حسناً'
                }).then(() => {
                    window.location.href = '/dashboard/courses/';
                });
            } else {
                Swal.fire({
                    title: 'خطأ',
                    text: data.errors ? data.errors[0] : 'حدث خطأ أثناء الحذف',
                    icon: 'error',
                    confirmButtonText: 'حسناً'
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire({
                title: 'خطأ',
                text: 'حدث خطأ في الاتصال بالخادم',
                icon: 'error',
                confirmButtonText: 'حسناً'
            });
        });
    }
    
    // Enrollment confirmation modal handlers
    const enrollmentConfirmModal = document.getElementById('enrollmentConfirmModal');
    const approveEnrollmentBtn = document.getElementById('approveEnrollmentBtn');
    const rejectEnrollmentBtn = document.getElementById('rejectEnrollmentBtn');
    
    // Use event delegation for dynamically loaded content
    document.addEventListener('click', function(e) {
        const approveBtn = e.target.closest('.btn-approve-enrollment');
        const rejectBtn = e.target.closest('.btn-reject-enrollment');
        
        if (approveBtn && enrollmentConfirmModal) {
            e.preventDefault();
            e.stopPropagation();
            
            const enrollmentId = approveBtn.dataset.enrollmentId;
            const userName = approveBtn.dataset.userName;
            const receiptUrl = approveBtn.dataset.receiptUrl || '';
            const approveUrl = approveBtn.dataset.approveUrl;
            
            console.log('Approve button clicked:', { enrollmentId, userName, approveUrl });
            
            document.getElementById('enrollmentConfirmId').value = enrollmentId;
            document.getElementById('enrollmentConfirmAction').value = 'approve';
            document.getElementById('enrollmentUserName').textContent = userName;
            enrollmentConfirmModal.dataset.actionUrl = approveUrl;
            enrollmentConfirmModal.dataset.action = 'approve';
            
            // Show receipt if exists
            const receiptImage = document.getElementById('enrollmentReceiptImage');
            const noReceiptPlaceholder = document.getElementById('enrollmentNoReceiptPlaceholder');
            
            if (receiptUrl) {
                receiptImage.src = receiptUrl;
                receiptImage.classList.remove('d-none');
                noReceiptPlaceholder.classList.add('d-none');
            } else {
                receiptImage.classList.add('d-none');
                noReceiptPlaceholder.classList.remove('d-none');
            }
            
            const modal = new bootstrap.Modal(enrollmentConfirmModal);
            modal.show();
        }
        
        if (rejectBtn && enrollmentConfirmModal) {
            e.preventDefault();
            e.stopPropagation();
            
            const enrollmentId = rejectBtn.dataset.enrollmentId;
            const userName = rejectBtn.dataset.userName;
            const rejectUrl = rejectBtn.dataset.rejectUrl;
            
            console.log('Reject button clicked:', { enrollmentId, userName, rejectUrl });
            
            document.getElementById('enrollmentConfirmId').value = enrollmentId;
            document.getElementById('enrollmentConfirmAction').value = 'reject';
            document.getElementById('enrollmentUserName').textContent = userName;
            enrollmentConfirmModal.dataset.actionUrl = rejectUrl;
            enrollmentConfirmModal.dataset.action = 'reject';
            
            const modal = new bootstrap.Modal(enrollmentConfirmModal);
            modal.show();
        }
    });
    
    // Approve action in modal
    if (approveEnrollmentBtn) {
        approveEnrollmentBtn.addEventListener('click', function() {
            handleEnrollmentAction('approve');
        });
    }
    
    // Reject action in modal
    if (rejectEnrollmentBtn) {
        rejectEnrollmentBtn.addEventListener('click', function() {
            handleEnrollmentAction('reject');
        });
    }
    
    // Edit enrollment button click
    document.addEventListener('click', function(e) {
        const editBtn = e.target.closest('.btn-edit-enrollment');
        const revokeBtn = e.target.closest('.btn-revoke-enrollment');
        
        if (editBtn) {
            e.preventDefault();
            e.stopPropagation();
            const enrollmentId = editBtn.dataset.enrollmentId;
            console.log('Edit enrollment clicked:', enrollmentId);
            Swal.fire({
                title: 'قريباً',
                text: 'ميزة تعديل التسجيل ستكون متاحة قريباً',
                icon: 'info',
                confirmButtonText: 'حسناً'
            });
        }
        
        if (revokeBtn) {
            e.preventDefault();
            e.stopPropagation();
            const enrollmentId = revokeBtn.dataset.enrollmentId;
            const userName = revokeBtn.dataset.userName;
            
            Swal.fire({
                title: 'سحب القبول؟',
                text: `هل أنت متأكد من سحب قبول ${userName}؟`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#f59e0b',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'نعم، سحب',
                cancelButtonText: 'إلغاء'
            }).then((result) => {
                if (result.isConfirmed) {
                    revokeEnrollment(enrollmentId);
                }
            });
        }
    });
    
    function revokeEnrollment(enrollmentId) {
        const formData = new FormData();
        formData.append('enrollment_id', enrollmentId);
        formData.append('csrfmiddlewaretoken', getCsrfToken());
        
        fetch(`/dashboard/courses/enrollment/${enrollmentId}/revoke/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                Swal.fire({
                    title: 'تم!',
                    text: 'تم سحب القبول بنجاح',
                    icon: 'success',
                    confirmButtonText: 'حسناً'
                }).then(() => {
                    window.location.reload();
                });
            } else {
                Swal.fire({
                    title: 'خطأ',
                    text: data.errors ? data.errors[0] : 'حدث خطأ أثناء سحب القبول',
                    icon: 'error',
                    confirmButtonText: 'حسناً'
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire({
                title: 'خطأ',
                text: 'حدث خطأ في الاتصال بالخادم',
                icon: 'error',
                confirmButtonText: 'حسناً'
            });
        });
    }
    
    function handleEnrollmentAction(action) {
        console.log('handleEnrollmentAction called:', action);
        
        const form = document.getElementById('enrollmentActionForm');
        const enrollmentId = document.getElementById('enrollmentConfirmId').value;
        const notes = form.querySelector('textarea[name="notes"]').value;
        const actionUrl = enrollmentConfirmModal.dataset.actionUrl;
        
        console.log('Action data:', { enrollmentId, action, actionUrl, notes });

        if (!actionUrl) {
            Swal.fire({
                title: 'خطأ',
                text: 'لم يتم تحديد عنوان الإجراء',
                icon: 'error',
                confirmButtonText: 'حسناً'
            });
            return;
        }

        const formData = new FormData();
        formData.append('enrollment_id', enrollmentId);
        formData.append('action', action);
        formData.append('notes', notes);
        formData.append('csrfmiddlewaretoken', getCsrfToken());

        fetch(actionUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            const modal = bootstrap.Modal.getInstance(enrollmentConfirmModal);
            modal.hide();
            
            if (data.success) {
                Swal.fire({
                    title: 'تم!',
                    text: action === 'approve' ? 'تم قبول التسجيل بنجاح' : 'تم رفض التسجيل',
                    icon: 'success',
                    confirmButtonText: 'حسناً'
                }).then(() => {
                    window.location.reload();
                });
            } else {
                Swal.fire({
                    title: 'خطأ',
                    text: data.errors ? data.errors[0] : 'حدث خطأ أثناء المعالجة',
                    icon: 'error',
                    confirmButtonText: 'حسناً'
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            const modal = bootstrap.Modal.getInstance(enrollmentConfirmModal);
            modal.hide();
            
            Swal.fire({
                title: 'خطأ',
                text: 'حدث خطأ في الاتصال بالخادم',
                icon: 'error',
                confirmButtonText: 'حسناً'
            });
        });
    }
    
    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
});