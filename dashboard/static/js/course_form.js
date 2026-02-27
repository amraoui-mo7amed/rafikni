/**
 * Course Form JavaScript
 * Handles course creation/editing form validation, thumbnail preview, and drag-drop
 * Used by: create.html, edit.html
 */

// Thumbnail Preview Functionality
function previewThumbnail(input) {
    const preview = document.getElementById('thumbnail-preview');
    const placeholder = document.querySelector('.image-upload-placeholder');
    const uploadArea = document.querySelector('.image-upload-area');
    const removeBtn = document.getElementById('remove-thumbnail');
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.classList.add('active');
            if (placeholder) placeholder.style.display = 'none';
            uploadArea.classList.add('has-image');
            if (removeBtn) removeBtn.classList.add('active');
        }
        reader.readAsDataURL(input.files[0]);
    }
}

function removeThumbnail(event) {
    event.stopPropagation();
    const input = document.getElementById('thumbnail-input');
    const preview = document.getElementById('thumbnail-preview');
    const placeholder = document.querySelector('.image-upload-placeholder');
    const uploadArea = document.querySelector('.image-upload-area');
    const removeBtn = document.getElementById('remove-thumbnail');
    
    if (input) input.value = '';
    if (preview) {
        preview.src = '';
        preview.classList.remove('active');
    }
    if (placeholder) placeholder.style.display = 'block';
    if (uploadArea) uploadArea.classList.remove('has-image');
    if (removeBtn) removeBtn.classList.remove('active');
}

// Initialize form validation and drag-drop when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('CourseForm');
    const uploadArea = document.querySelector('.image-upload-area');
    
    // Form validation (for create page)
    if (form) {
        form.addEventListener('submit', function(e) {
            const title = document.getElementById('title');
            const teacherName = document.getElementById('teacher_name');
            const description = document.getElementById('description');
            
            if (title && !title.value.trim()) {
                e.preventDefault();
                showError('يرجى إدخال عنوان الدورة');
                return false;
            }
            if (teacherName && !teacherName.value.trim()) {
                e.preventDefault();
                showError('يرجى إدخال اسم المعلم');
                return false;
            }
            if (description && !description.value.trim()) {
                e.preventDefault();
                showError('يرجى إدخال وصف الدورة');
                return false;
            }
        });
    }
    
    // Drag and drop functionality
    if (uploadArea) {
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#0d6efd';
            uploadArea.style.background = '#f0f7ff';
        });
        
        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#cbd5e1';
            uploadArea.style.background = '#f8fafc';
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#cbd5e1';
            uploadArea.style.background = '#f8fafc';
            
            const input = document.getElementById('thumbnail-input');
            const files = e.dataTransfer.files;
            
            if (input && files.length > 0 && files[0].type.startsWith('image/')) {
                input.files = files;
                previewThumbnail(input);
            }
        });
    }
    
    function showError(message) {
        const errorList = document.querySelector('.errorList');
        if (errorList) {
            errorList.innerHTML = '<li class="error-message show">' + message + '</li>';
        }
    }
});