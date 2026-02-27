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
    
    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
});