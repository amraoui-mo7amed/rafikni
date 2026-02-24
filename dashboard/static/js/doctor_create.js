// Form submission handler for doctor creation
(function() {
    'use strict';

    const form = document.getElementById('doctorCreateForm');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const submitBtn = this.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        
        // Disable submit button
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> جاري الإنشاء...';
        
        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                showSuccess(data.message);
                setTimeout(() => {
                    window.location.href = form.dataset.redirectUrl;
                }, 1500);
            } else {
                showErrors(data.errors || ['حدث خطأ غير متوقع']);
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        } catch (error) {
            console.error('Error:', error);
            showErrors(['حدث خطأ في الاتصال بالخادم']);
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    });

    function showSuccess(message) {
        const errorList = document.querySelector('#doctorCreateForm .errorList');
        if (errorList) {
            errorList.innerHTML = '';
            const li = document.createElement('li');
            li.className = 'success-message';
            li.textContent = message;
            errorList.appendChild(li);
            
            // Scroll to top to see the message
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }

    function showErrors(errors) {
        const errorList = document.querySelector('#doctorCreateForm .errorList');
        if (errorList) {
            errorList.innerHTML = '';
            errors.forEach(error => {
                const li = document.createElement('li');
                li.className = 'error-message';
                li.textContent = error;
                errorList.appendChild(li);
            });
            
            // Scroll to top to see errors
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }
})();
