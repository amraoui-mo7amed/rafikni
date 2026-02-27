/**
 * Course List JavaScript
 * Handles enrollment, view modal, and payment
 */

document.addEventListener('DOMContentLoaded', function() {
    // Enroll buttons
    const enrollButtons = document.querySelectorAll('.btn-enroll');
    const submitPaymentBtn = document.getElementById('submitPaymentBtn');
    const deleteButtons = document.querySelectorAll('.btn-delete-course');

    let currentEnrollmentId = null;
    let currentCourseId = null;
    let paymentModal = null;
    
    // Only initialize payment modal if it exists
    const paymentModalEl = document.getElementById('paymentModal');
    if (paymentModalEl) {
        paymentModal = new bootstrap.Modal(paymentModalEl);
    }
    
    console.log('Found delete buttons:', deleteButtons.length);
    console.log('Payment modal exists:', !!paymentModalEl);

    // Handle enroll button clicks
    enrollButtons.forEach(button => {
        button.addEventListener('click', function() {
            const courseId = this.dataset.courseId;
            const coursePrice = parseFloat(this.dataset.coursePrice);

            if (coursePrice === 0) {
                // Free course - enroll directly
                enrollInCourse(courseId, this);
            } else {
                // Paid course - show payment modal
                currentCourseId = courseId;
                document.getElementById('paymentAmount').textContent = coursePrice + ' د.ج';
                document.getElementById('paymentAmountInput').value = coursePrice;
                
                // First enroll to get enrollment ID
                enrollInCourse(courseId, null, true);
            }
        });
    });

    // Handle payment submission
    if (submitPaymentBtn) {
        submitPaymentBtn.addEventListener('click', function() {
            submitPayment();
        });
    }

    // Handle delete buttons
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const deleteUrl = this.dataset.deleteUrl;
            console.log('Delete button clicked, URL:', deleteUrl);
            if (deleteUrl) {
                confirmDelete(deleteUrl);
            } else {
                console.error('No delete URL found on button');
            }
        });
    });

    function enrollInCourse(courseId, buttonElement, isPaymentFlow = false) {
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
            if (data.success) {
                if (isPaymentFlow && data.requires_payment) {
                    currentEnrollmentId = data.enrollment_id;
                    document.getElementById('enrollmentId').value = data.enrollment_id;
                    if (paymentModal) {
                        paymentModal.show();
                    }
                } else if (!isPaymentFlow) {
                    // Free course enrolled successfully
                    Swal.fire({
                        title: 'تم التسجيل بنجاح!',
                        text: 'يمكنك الآن مشاهدة الدورة',
                        icon: 'success',
                        confirmButtonText: 'مشاهدة الدورة',
                        confirmButtonColor: '#0d6efd'
                    }).then((result) => {
                        if (result.isConfirmed && data.redirect_url) {
                            window.location.href = data.redirect_url;
                        }
                    });

                    // Update button
                    if (buttonElement) {
                        buttonElement.innerHTML = '<i class="fa-solid fa-play me-2"></i> مشاهدة';
                        buttonElement.classList.remove('btn-primary');
                        buttonElement.classList.add('btn-success');
                        buttonElement.disabled = false;
                        buttonElement.onclick = () => {
                            window.location.href = data.redirect_url;
                        };
                    }
                }
            } else {
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
            Swal.fire({
                title: 'خطأ',
                text: 'حدث خطأ في الاتصال بالخادم',
                icon: 'error',
                confirmButtonText: 'حسناً'
            });
        });
    }

    function submitPayment() {
        const receiptImage = document.querySelector('input[name="receipt_image"]');
        const amount = document.getElementById('paymentAmountInput').value;
        const notes = document.querySelector('textarea[name="notes"]');
        
        const receiptFile = receiptImage && receiptImage.files ? receiptImage.files[0] : null;
        const notesValue = notes ? notes.value : '';

        if (!receiptFile) {
            showPaymentError('يرجى رفع صورة الإيصال');
            return;
        }

        if (!amount || amount <= 0) {
            showPaymentError('يرجى إدخال المبلغ المحول');
            return;
        }

        const formData = new FormData();
        formData.append('receipt_image', receiptFile);
        formData.append('amount', amount);
        formData.append('notes', notesValue);
        formData.append('csrfmiddlewaretoken', getCsrfToken());

        submitPaymentBtn.disabled = true;
        submitPaymentBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> جاري الإرسال...';

        fetch(`/dashboard/courses/payment/${currentEnrollmentId}/submit/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            submitPaymentBtn.disabled = false;
            submitPaymentBtn.innerHTML = '<i class="fa-solid fa-paper-plane me-2"></i> إرسال الإيصال';

            if (data.success) {
                if (paymentModal) {
                    paymentModal.hide();
                }
                clearPaymentErrors();
                
                Swal.fire({
                    title: 'تم إرسال الإيصال!',
                    text: 'سيتم مراجعة الدفع والتواصل معك قريباً',
                    icon: 'success',
                    confirmButtonText: 'حسناً',
                    confirmButtonColor: '#0d6efd'
                }).then(() => {
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    } else {
                        window.location.reload();
                    }
                });
            } else {
                showPaymentErrors(data.errors);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            submitPaymentBtn.disabled = false;
            submitPaymentBtn.innerHTML = '<i class="fa-solid fa-paper-plane me-2"></i> إرسال الإيصال';
            showPaymentError('حدث خطأ في الاتصال بالخادم');
        });
    }

    function confirmDelete(deleteUrl) {
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
                    window.location.reload();
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

    function showPaymentError(message) {
        clearPaymentErrors();
        const errorList = document.querySelector('#paymentForm .errorList');
        if (errorList) {
            const li = document.createElement('li');
            li.className = 'error-message show';
            li.textContent = message;
            errorList.appendChild(li);
        }
    }

    function showPaymentErrors(errors) {
        clearPaymentErrors();
        const errorList = document.querySelector('#paymentForm .errorList');
        if (errorList && Array.isArray(errors)) {
            errors.forEach(error => {
                const li = document.createElement('li');
                li.className = 'error-message show';
                li.textContent = error;
                errorList.appendChild(li);
            });
        }
    }

    function clearPaymentErrors() {
        const errorList = document.querySelector('#paymentForm .errorList');
        if (errorList) {
            errorList.innerHTML = '';
        }
    }

    function getCsrfToken() {
        const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
        return tokenInput ? tokenInput.value : '';
    }
});