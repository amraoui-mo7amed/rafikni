/**
 * Email Settings Script
 * Handles form interactions, password visibility, and AJAX submissions.
 */
document.addEventListener('DOMContentLoaded', function() {
    // 1. Password Visibility Toggle
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        const toggleBtn = document.createElement('span');
        toggleBtn.className = 'input-group-text bg-white border-start-0 py-2 cursor-pointer';
        toggleBtn.innerHTML = '<i class="fa-solid fa-eye text-muted"></i>';
        toggleBtn.style.cursor = 'pointer';
        
        const inputGroup = input.parentElement;
        if (inputGroup && inputGroup.classList.contains('input-group')) {
            inputGroup.appendChild(toggleBtn);
            
            toggleBtn.addEventListener('click', function() {
                const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                input.setAttribute('type', type);
                const icon = toggleBtn.querySelector('i');
                if (type === 'text') {
                    icon.classList.replace('fa-eye', 'fa-eye-slash');
                    icon.classList.add('text-primary');
                } else {
                    icon.classList.replace('fa-eye-slash', 'fa-eye');
                    icon.classList.remove('text-primary');
                }
            });
        }
    });

    // 2. AJAX Form Submission
    const form = document.getElementById('EmailSettingsForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const errorList = form.querySelector('.errorList');
            if (errorList) errorList.innerHTML = '';
            
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            
            // Loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> جاري الحفظ...';

            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    submitBtn.innerHTML = '<i class="fa-solid fa-check me-2"></i> ' + data.message;
                    submitBtn.classList.replace('btn-primary', 'btn-success');
                    
                    setTimeout(() => {
                        submitBtn.innerHTML = originalBtnText;
                        submitBtn.classList.replace('btn-success', 'btn-primary');
                        submitBtn.disabled = false;
                    }, 2000);
                } else {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnText;
                    
                    if (data.errors && errorList) {
                        data.errors.forEach(error => {
                            const li = document.createElement('li');
                            li.className = 'alert alert-danger py-2 small mb-2';
                            li.style.listStyle = 'none';
                            li.innerText = error;
                            errorList.appendChild(li);
                        });
                        // Scroll to errors
                        errorList.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
                alert('حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.');
            });
        });
    }

    // 3. Switch Labels Enhancement
    const switches = document.querySelectorAll('.form-check-input');
    switches.forEach(sw => {
        const updateLabel = (input) => {
            const label = input.parentElement.querySelector('label');
            if (label) {
                if (input.checked) {
                    label.classList.add('text-primary');
                    label.classList.remove('text-muted');
                } else {
                    label.classList.add('text-muted');
                    label.classList.remove('text-primary');
                }
            }
        };
        
        // Initial state
        updateLabel(sw);
        
        sw.addEventListener('change', function() {
            updateLabel(this);
        });
    });
});
