document.addEventListener('DOMContentLoaded', function() {
    const viewButtons = document.querySelectorAll('.btn-view[data-payment-id]');

    viewButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const paymentId = this.dataset.paymentId;
            const detailUrl = this.dataset.detailUrl;
            const reviewUrl = this.dataset.reviewUrl;

            openPaymentModal(paymentId, detailUrl, reviewUrl);
        });
    });

    window.openPaymentModal = function(paymentId, detailUrl, reviewUrl) {
        const modal = new bootstrap.Modal(document.getElementById('paymentReviewModal'));
        const content = document.getElementById('paymentModalContent');

        content.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary"></div></div>';
        modal.show();

        fetch(detailUrl)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    content.innerHTML = data.html;
                    window.currentPaymentReviewUrl = reviewUrl;
                } else {
                    content.innerHTML = '<div class="alert alert-danger m-3">' + (data.errors ? data.errors[0] : 'حدث خطأ ما') + '</div>';
                }
            });
    };

    window.submitReview = function(paymentId, action) {
        const reviewUrl = window.currentPaymentReviewUrl;
        
        if (!reviewUrl) {
            Swal.fire('خطأ', 'حدث خطأ في تحميل النافذة', 'error');
            return;
        }

        Swal.fire({
            title: 'هل أنت متأكد؟',
            text: action === 'approve' ? 'هل تريد قبول هذا الدفع؟' : 'هل تريد رفض هذا الدفع؟',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'تأكيد',
            cancelButtonText: 'إلغاء',
            confirmButtonColor: action === 'approve' ? '#28a745' : '#dc3545',
        }).then((result) => {
            if (result.isConfirmed) {
                const formData = new FormData();
                formData.append('action', action);
                formData.append('csrfmiddlewaretoken', getCsrfToken());

                fetch(reviewUrl, {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        Swal.fire('نجاح', data.message, 'success').then(() => {
                            location.reload();
                        });
                    } else {
                        Swal.fire('خطأ', data.errors[0], 'error');
                    }
                });
            }
        });
    };

    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
});
