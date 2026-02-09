/**
 * Email Settings Script
 * Handles interactions and SMTP connection testing.
 */
document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('EmailSettingsForm');
    const testBtn = document.getElementById('testConnectionBtn');

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

            toggleBtn.addEventListener('click', function () {
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

    // 2. Switch Labels Color Sync
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
        updateLabel(sw);
        sw.addEventListener('change', function () {
            updateLabel(this);
        });
    });

    // 3. Test Connection Logic (AJAX)
    if (testBtn && form) {
        testBtn.addEventListener('click', function (e) {
            e.preventDefault();

            const formData = new FormData(form);
            const originalBtnText = testBtn.innerHTML;
            const errorList = form.querySelector('.errorList');
            
            if (errorList) {
                errorList.innerHTML = '';
            }

            // Loading state
            testBtn.disabled = true;
            testBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> جاري التجربة...';

            fetch('/dashboard/settings/email/test/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                testBtn.disabled = false;
                testBtn.innerHTML = originalBtnText;

                if (data.success) {
                    testBtn.classList.replace('btn-outline-primary', 'btn-success');
                    testBtn.classList.add('text-white');
                    testBtn.innerHTML = '<i class="fa-solid fa-check me-2"></i> اتصل بنجاح';
                    
                    setTimeout(() => {
                        testBtn.innerHTML = originalBtnText;
                        testBtn.classList.replace('btn-success', 'btn-outline-primary');
                        testBtn.classList.remove('text-white');
                    }, 3000);
                } else {
                    if (data.errors && errorList) {
                        data.errors.forEach(error => {
                            const li = document.createElement('li');
                            li.className = 'alert alert-warning py-2 small mb-2';
                            li.style.listStyle = 'none';
                            li.innerText = error;
                            errorList.appendChild(li);
                        });
                        errorList.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                testBtn.disabled = false;
                testBtn.innerHTML = originalBtnText;
            });
        });
    }
});
