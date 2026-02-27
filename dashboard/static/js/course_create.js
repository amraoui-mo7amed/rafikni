/**
 * Course Create JavaScript
 * Handles multi-step form and video upload with progress
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('CourseForm');
    const step1 = document.getElementById('step1');
    const step2 = document.getElementById('step2');
    const nextToVideosBtn = document.getElementById('nextToVideosBtn');
    const backToInfoBtn = document.getElementById('backToInfoBtn');
    const addVideoBtn = document.getElementById('addVideoBtn');
    const videosList = document.getElementById('videosList');
    const videoTemplate = document.getElementById('videoUploadTemplate');
    
    let videoCount = 0;
    let uploadedVideos = [];
    let courseId = null;

    // Navigation between steps
    nextToVideosBtn.addEventListener('click', function() {
        if (validateStep1()) {
            // First create the course
            createCourse();
        }
    });

    backToInfoBtn.addEventListener('click', function() {
        step2.style.display = 'none';
        step1.style.display = 'block';
    });

    // Add video upload item
    addVideoBtn.addEventListener('click', function() {
        addVideoUploadItem();
    });

    // Form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        finishCourseCreation();
    });

    function validateStep1() {
        const title = document.getElementById('title').value.trim();
        const teacherName = document.getElementById('teacher_name').value.trim();
        const description = document.getElementById('description').value.trim();
        const price = document.getElementById('price').value;

        if (!title) {
            showError('يرجى إدخال عنوان الدورة');
            return false;
        }
        if (!teacherName) {
            showError('يرجى إدخال اسم المعلم');
            return false;
        }
        if (!description) {
            showError('يرجى إدخال وصف الدورة');
            return false;
        }
        if (price === '' || price < 0) {
            showError('يرجى إدخال سعر صحيح');
            return false;
        }

        return true;
    }

    function createCourse() {
        const formData = new FormData(form);
        
        // Disable button during submission
        nextToVideosBtn.disabled = true;
        nextToVideosBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> جاري الإنشاء...';

        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            nextToVideosBtn.disabled = false;
            nextToVideosBtn.innerHTML = '<i class="fa-solid fa-arrow-left me-2"></i> الانتقال لرفع الفيديوهات';

            if (data.success) {
                courseId = data.course_id;
                clearErrors();
                
                // Show step 2
                step1.style.display = 'none';
                step2.style.display = 'block';
                
                // Add first video upload item automatically
                if (videoCount === 0) {
                    addVideoUploadItem();
                }
            } else {
                showErrors(data.errors);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            nextToVideosBtn.disabled = false;
            nextToVideosBtn.innerHTML = '<i class="fa-solid fa-arrow-left me-2"></i> الانتقال لرفع الفيديوهات';
            showError('حدث خطأ في الاتصال بالخادم');
        });
    }

    function addVideoUploadItem() {
        videoCount++;
        const template = videoTemplate.innerHTML;
        const html = template
            .replace(/{index}/g, videoCount)
            .replace(/{number}/g, videoCount);
        
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        const videoItem = tempDiv.firstElementChild;
        
        videosList.appendChild(videoItem);
        
        // Setup file input handler
        const fileInput = videoItem.querySelector('.video-file-input');
        const uploadArea = videoItem.querySelector('.upload-area');
        
        // Handle click on upload area to trigger file input
        uploadArea.addEventListener('click', function(e) {
            // Don't trigger if clicking on buttons or interactive elements inside
            if (e.target.closest('button') || e.target.closest('a')) {
                return;
            }
            fileInput.click();
        });
        
        fileInput.addEventListener('change', function(e) {
            handleVideoFileSelect(e, videoItem);
        });
        
        // Setup remove button
        const removeBtn = videoItem.querySelector('.btn-remove-video');
        removeBtn.addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent triggering upload area click
            videoItem.remove();
            renumberVideos();
        });
    }

    function handleVideoFileSelect(e, videoItem) {
        const file = e.target.files[0];
        if (!file) return;

        // Validate file type
        const validTypes = ['video/mp4', 'video/webm', 'video/quicktime', 'video/mov'];
        if (!validTypes.includes(file.type)) {
            showError('يرجى اختيار ملف فيديو صالح (MP4, WebM, MOV)');
            return;
        }

        // Validate file size (500MB max)
        const maxSize = 500 * 1024 * 1024;
        if (file.size > maxSize) {
            showError('حجم الملف كبير جداً. الحد الأقصى 500MB');
            return;
        }

        // Show upload progress UI
        const uploadContent = videoItem.querySelector('.upload-content');
        const uploadProgress = videoItem.querySelector('.upload-progress');
        const progressBar = uploadProgress.querySelector('.progress-bar');
        const progressText = uploadProgress.querySelector('.progress-text');
        
        uploadContent.style.display = 'none';
        uploadProgress.style.display = 'block';

        // Upload the video
        uploadVideo(file, videoItem, progressBar, progressText, uploadContent, uploadProgress);
    }

    function uploadVideo(file, videoItem, progressBar, progressText, uploadContent, uploadProgress) {
        const formData = new FormData();
        const title = videoItem.querySelector('.video-title').value || `فيديو ${videoCount}`;
        const description = videoItem.querySelector('.video-description').value || '';
        
        formData.append('video_file', file);
        formData.append('title', title);
        formData.append('description', description);
        formData.append('order', videoCount);
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

        const xhr = new XMLHttpRequest();
        
        // Track upload progress
        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 100);
                progressBar.style.width = percentComplete + '%';
                progressText.textContent = percentComplete + '%';
            }
        });

        xhr.addEventListener('load', function() {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                if (response.success) {
                    // Show success UI
                    uploadProgress.style.display = 'none';
                    const uploadSuccess = videoItem.querySelector('.upload-success');
                    const fileName = uploadSuccess.querySelector('.file-name');
                    fileName.textContent = file.name;
                    uploadSuccess.style.display = 'block';
                    
                    uploadedVideos.push({
                        video_id: response.video_id,
                        is_free: response.is_free
                    });
                    
                    // Disable inputs
                    videoItem.querySelector('.video-title').disabled = true;
                    videoItem.querySelector('.video-description').disabled = true;
                    videoItem.querySelector('.btn-remove-video').style.display = 'none';
                } else {
                    showErrors(response.errors);
                    uploadProgress.style.display = 'none';
                    uploadContent.style.display = 'block';
                }
            } else {
                showError('حدث خطأ أثناء رفع الفيديو');
                uploadProgress.style.display = 'none';
                uploadContent.style.display = 'block';
            }
        });

        xhr.addEventListener('error', function() {
            showError('حدث خطأ في الاتصال أثناء رفع الفيديو');
            uploadProgress.style.display = 'none';
            uploadContent.style.display = 'block';
        });

        xhr.open('POST', `/dashboard/courses/${courseId}/videos/upload/`);
        xhr.send(formData);
    }

    function renumberVideos() {
        const videoItems = videosList.querySelectorAll('.video-upload-item');
        videoItems.forEach((item, index) => {
            const numberBadge = item.querySelector('.video-number');
            numberBadge.textContent = index + 1;
        });
        videoCount = videoItems.length;
    }

    function finishCourseCreation() {
        // Check if all videos have files selected
        const videoItems = videosList.querySelectorAll('.video-upload-item');
        let hasPendingUploads = false;
        
        videoItems.forEach(item => {
            const fileInput = item.querySelector('.video-file-input');
            const uploadSuccess = item.querySelector('.upload-success');
            
            // Check if this video hasn't been uploaded yet (success div is hidden)
            if (uploadSuccess && uploadSuccess.style.display === 'none' && fileInput.files.length === 0) {
                hasPendingUploads = true;
            }
        });
        
        if (hasPendingUploads) {
            showError('يرجى اختيار ملف فيديو لجميع العناصر المضافة');
            return;
        }
        
        if (uploadedVideos.length === 0) {
            showError('يرجى رفع فيديو واحد على الأقل');
            return;
        }

        Swal.fire({
            title: 'تم إنشاء الدورة بنجاح!',
            text: `تم رفع ${uploadedVideos.length} فيديو بنجاح`,
            icon: 'success',
            confirmButtonText: 'حسناً',
            confirmButtonColor: '#0d6efd'
        }).then((result) => {
            if (result.isConfirmed) {
                window.location.href = '/dashboard/courses/';
            }
        });
    }

    function showError(message) {
        clearErrors();
        const errorList = document.querySelector('#CourseForm .errorList');
        if (errorList) {
            const li = document.createElement('li');
            li.className = 'error-message show';
            li.textContent = message;
            errorList.appendChild(li);
            
            setTimeout(() => {
                li.remove();
            }, 5000);
        }
    }

    function showErrors(errors) {
        clearErrors();
        const errorList = document.querySelector('#CourseForm .errorList');
        if (errorList && Array.isArray(errors)) {
            errors.forEach(error => {
                const li = document.createElement('li');
                li.className = 'error-message show';
                li.textContent = error;
                errorList.appendChild(li);
                
                setTimeout(() => {
                    li.remove();
                }, 5000);
            });
        }
    }

    function clearErrors() {
        const errorList = document.querySelector('#CourseForm .errorList');
        if (errorList) {
            errorList.innerHTML = '';
        }
    }
});