// Animation on scroll
const animatedEls = document.querySelectorAll('.fade-in, .slide-up, .slide-right, .zoom-in, .animated');
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('in-view');
            observer.unobserve(entry.target);
        }
    });
}, {
    threshold: 0.15
});

animatedEls.forEach(el => observer.observe(el));

// Smooth active nav link
const sections = document.querySelectorAll('section, header');
const navLinks = document.querySelectorAll('.nav-link');
const sectionMap = {};
sections.forEach(sec => sectionMap[sec.id] = sec.offsetTop);

window.addEventListener('scroll', () => {
    const scrollPos = window.scrollY + 120;
    for (const id in sectionMap) {
        const sec = document.getElementById(id);
        if (!sec) continue;
        const top = sec.offsetTop;
        const height = sec.offsetHeight;
        if (scrollPos >= top && scrollPos < top + height) {
            navLinks.forEach(l => l.classList.remove('active'));
            const active = document.querySelector(`.nav-link[href="#${id}"]`);
            if (active) active.classList.add('active');
        }
    }
});

// Dealing with form.form 
document.addEventListener('DOMContentLoaded', function () {
    // Find all forms with the 'form' class
    const forms = document.querySelectorAll('form.form');

    forms.forEach(form => {
        const formId = form.id;
        console.log(formId);

        if (!formId) {
            console.warn('Form found without an ID, skipping error handling:', form);
            return;
        }

        // Find the associated error list
        const errorList = document.querySelector(`ul.errorList[data-target-form="${formId}"]`);
        if (!errorList) {
            console.warn(`No error list found for form ID: ${formId}`);
            return;
        }

        // Find the submit button
        const submitBtn = form.querySelector('button[type="submit"]');
        if (!submitBtn) {
            console.warn(`No submit button found in form ID: ${formId}`);
            return;
        }

        // Store original button text and create spinner element
        const originalBtnText = submitBtn.innerHTML.trim();
        const spinner = document.createElement('span');
        spinner.innerHTML = `
            <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            جاري المعالجة...
        `;
        spinner.style.display = 'none'; // Hidden by default

        form.addEventListener('submit', async function (e) {
            e.preventDefault(); // Prevent default form submission

            // Show spinner, disable button
            submitBtn.disabled = true;
            submitBtn.innerHTML = spinner.innerHTML;

            // Clear previous messages
            clearMessages(errorList);

            const formData = new FormData(form);

            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest', // Optional: Identify AJAX request
                    }
                });

                const data = await response.json();

                if (data.success) {
                    // Show success message
                    addMessage(errorList, data.message, 'success-message');

                    // Redirect after a short delay to show success message
                    if (data.redirect_url) {
                        setTimeout(() => {
                            window.location.href = data.redirect_url;
                        }, 1500);
                    }
                } else {
                    // Handle errors
                    if (data.errors && Array.isArray(data.errors)) {
                        data.errors.forEach(error => {
                            addMessage(errorList, error, 'error-message');
                        });
                    } else {
                        // Fallback for unexpected error format
                        addMessage(errorList, 'حدث خطأ غير متوقع', 'error-message');
                    }
                }
            } catch (error) {
                console.error('Error submitting form:', error);
                addMessage(errorList, 'خطأ في الاتصال بالخادم', 'error-message');
            } finally {
                // Re-enable button and restore original text
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            }
        });
    });

    // Function to clear all messages from the list
    function clearMessages(errorList) {
        Array.from(errorList.children).forEach(li => {
            // Trigger hide animation if class exists
            if (li.classList.contains('show')) {
                li.classList.remove('show');
                li.classList.add('hiding');
                // Remove from DOM after animation completes
                setTimeout(() => {
                    if (li.parentNode === errorList) { // Check if still attached
                        li.remove();
                    }
                }, 300);
            } else {
                // If not showing, remove immediately
                li.remove();
            }
        });
    }

    // Function to add a new message to the list
    function addMessage(errorList, message, type) {
        const li = document.createElement('li');
        li.className = `${type} hiding`; // Start hidden
        li.textContent = message;

        errorList.appendChild(li);

        // Trigger reflow to ensure the 'hiding' class styles are applied first
        void li.offsetWidth;

        // Now add the 'show' class to trigger the animation
        li.classList.remove('hiding');
        li.classList.add('show');
    }

});