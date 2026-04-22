/**
 * Public Games JS - Handles Gallery and Custom COD Order Flow
 */
const GameOrderHandler = {
    init: function() {
        this.initGallery();
        this.initCustomDropdowns();
        this.initOrderForm();
    },

    /**
     * Handles the image switcher for the product gallery.
     */
    initGallery: function() {
        const thumbs = document.querySelectorAll('.gallery-thumb');
        const mainImage = document.getElementById('mainImage');
        
        if (!mainImage) return;

        thumbs.forEach(thumb => {
            thumb.addEventListener('click', () => {
                const url = thumb.dataset.image;
                if (url) {
                    mainImage.src = url;
                    thumbs.forEach(t => t.classList.remove('active'));
                    thumb.classList.add('active');
                }
            });
        });
    },

    /**
     * Implements custom dropdown logic identical to ultra_select.
     */
    initCustomDropdowns: function() {
        const containers = document.querySelectorAll('.ultra-select-container');
        
        containers.forEach(container => {
            const wrapper = container.querySelector('.ultra-select-wrapper');
            const dropdown = container.querySelector('.ultra-dropdown');
            const selectedText = container.querySelector('.ultra-selected-value');
            const hiddenInput = container.querySelector('input[type="hidden"]');
            const name = container.dataset.name;

            if (!wrapper || !dropdown) return;

            // Toggle Dropdown
            wrapper.addEventListener('click', (e) => {
                e.stopPropagation();
                // Close others
                document.querySelectorAll('.ultra-dropdown').forEach(d => {
                    if (d !== dropdown) d.classList.remove('show');
                });
                document.querySelectorAll('.ultra-select-wrapper').forEach(w => {
                    if (w !== wrapper) w.classList.remove('open');
                });

                dropdown.classList.toggle('show');
                wrapper.classList.toggle('open');
            });

            // Handle Selection
            dropdown.addEventListener('click', (e) => {
                const option = e.target.closest('.ultra-option');
                if (option) {
                    const value = option.dataset.value;
                    const text = option.textContent;
                    const code = option.dataset.code;

                    // Update UI
                    if (selectedText) selectedText.textContent = text;
                    if (hiddenInput) {
                        hiddenInput.value = value;
                        // Trigger custom change event for dependencies
                        hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                    
                    // Cleanup
                    dropdown.querySelectorAll('.ultra-option').forEach(o => o.classList.remove('active'));
                    option.classList.add('active');
                    dropdown.classList.remove('show');
                    wrapper.classList.remove('open');

                    // Special logic for Wilaya -> Commune
                    if (name === 'wilaya' && code) {
                        this.loadCommunes(code);
                    }
                }
            });
        });

        // Close dropdowns on outside click
        document.addEventListener('click', () => {
            document.querySelectorAll('.ultra-dropdown').forEach(d => d.classList.remove('show'));
            document.querySelectorAll('.ultra-select-wrapper').forEach(w => w.classList.remove('open'));
        });
    },

    /**
     * Loads communes for the selected wilaya via AJAX.
     */
    loadCommunes: function(wilayaCode) {
        const formContainer = document.querySelector('.order-form-container');
        const apiUrl = formContainer ? formContainer.dataset.communesUrl : null;
        const communeContainer = document.querySelector('#custom-select-commune');
        
        if (!apiUrl || !communeContainer) return;

        const dropdown = communeContainer.querySelector('.ultra-dropdown');
        const selectedValue = communeContainer.querySelector('.ultra-selected-value');
        const hiddenInput = communeContainer.querySelector('input[type="hidden"]');

        fetch(`${apiUrl}?wilaya_code=${wilayaCode}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && dropdown) {
                    dropdown.innerHTML = '<div class="ultra-option active" data-value="">اختر البلدية...</div>';
                    data.data.forEach(item => {
                        const option = document.createElement('div');
                        option.className = 'ultra-option';
                        option.dataset.value = item[1];
                        option.textContent = item[1];
                        dropdown.appendChild(option);
                    });

                    // Reset selection
                    if (selectedValue) selectedValue.textContent = 'اختر البلدية...';
                    if (hiddenInput) hiddenInput.value = '';
                }
            })
            .catch(err => console.error('Error loading communes:', err));
    },

    /**
     * Handles the COD order form submission.
     */
    initOrderForm: function() {
        const orderForm = document.getElementById('placeOrderForm');
        if (!orderForm) return;

        orderForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const submitUrl = orderForm.dataset.url;
            const csrfToken = orderForm.dataset.csrf;
            const submitBtn = document.getElementById('submitOrderBtn');

            if (!submitUrl) return;

            const formData = new FormData(orderForm);
            
            submitBtn.disabled = true;
            const originalHtml = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin ms-2"></i> جاري إرسال طلبك...';

            fetch(submitUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        title: 'تم بنجاح!',
                        text: data.message,
                        icon: 'success',
                        confirmButtonColor: '#0d6efd'
                    }).then(() => {
                        window.location.reload();
                    });
                } else {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalHtml;
                    Swal.fire('خطأ!', (data.errors || []).join('\n'), 'error');
                }
            })
            .catch(err => {
                console.error('Order error:', err);
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalHtml;
                Swal.fire('خطأ!', 'حدث خطأ أثناء إرسال الطلب.', 'error');
            });
        });
    }
};

document.addEventListener('DOMContentLoaded', () => {
    GameOrderHandler.init();
});
