/**
 * Course Detail Interactive Functionality
 * Handles enrollment and video player switching using Data Attributes.
 */

const CourseHandler = {
    init: function() {
        this.initVideoPlayer();
        this.initEnrollment();
        this.initPaymentSubmission();
        this.initAuthRequired();
        this.initRoleRestricted();
    },

    /**
     * Handles clicks for users with restricted roles (e.g., specialists).
     */
    initRoleRestricted: function() {
        const restrictedBtns = document.querySelectorAll('.btn-role-restricted');
        restrictedBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                Swal.fire({
                    title: 'ميزة مخصصة للمرضى',
                    text: 'هذه الدورات التعليمية مخصصة لتطوير مهارات المرضى وأسرهم. حسابك الحالي (أخصائي/مشرف) لا يملك صلاحية التسجيل.',
                    icon: 'warning',
                    confirmButtonText: 'فهمت',
                    confirmButtonColor: '#0d6efd',
                    customClass: {
                        popup: 'rounded-4 border-0 shadow-lg'
                    }
                });
            });
        });
    },

    /**
     * Handles clicks on enrollment buttons for unauthenticated users.
     */
    initAuthRequired: function() {
        const authBtns = document.querySelectorAll('.btn-auth-required');
        const container = document.querySelector('.enrollment-action-area');
        
        if (!container) return;

        const loginUrl = container.dataset.loginUrl;
        const signupUrl = container.dataset.signupUrl;
        const currentPath = container.dataset.currentPath;

        authBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                Swal.fire({
                    title: 'تسجيل الدخول مطلوب',
                    text: 'يجب أن تكون عضواً في منصة رافقني للانضمام إلى هذه الدورة التعليمية.',
                    icon: 'info',
                    showCancelButton: true,
                    confirmButtonText: 'تسجيل الدخول',
                    cancelButtonText: 'إنشاء حساب جديد',
                    confirmButtonColor: '#0d6efd',
                    cancelButtonColor: '#10b981',
                    reverseButtons: true,
                    customClass: {
                        popup: 'rounded-4 border-0 shadow-lg'
                    }
                }).then((result) => {
                    if (result.isConfirmed) {
                        window.location.href = `${loginUrl}?next=${currentPath}`;
                    } else if (result.dismiss === Swal.DismissReason.cancel) {
                        window.location.href = signupUrl;
                    }
                });
            });
        });
    },

    /**
     * Initializes video player logic for switching free previews.
     */
    initVideoPlayer: function() {
        const curriculumItems = document.querySelectorAll('.curriculum-item[data-video-url]');
        const videoPlayer = document.getElementById('mainCourseVideo');
        const videoPlaceholder = document.getElementById('videoPlaceholder');
        const playerContainer = document.getElementById('playerContainer');

        curriculumItems.forEach(item => {
            item.addEventListener('click', () => {
                const videoUrl = item.getAttribute('data-video-url');
                if (videoUrl) {
                    // Update player
                    videoPlayer.src = videoUrl;
                    videoPlaceholder.style.display = 'none';
                    playerContainer.style.display = 'block';
                    
                    // Mark active
                    curriculumItems.forEach(i => i.classList.remove('active'));
                    item.classList.add('active');

                    // Scroll to player on mobile
                    if (window.innerWidth < 992) {
                        videoPlayer.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                } else {
                    Swal.fire({
                        title: 'محتوى مغلق',
                        text: 'يجب الاشتراك في الدورة لمشاهدة هذا الفيديو.',
                        icon: 'lock',
                        confirmButtonColor: '#06b6d4'
                    });
                }
            });
        });
    },

    /**
     * Handles the enrollment AJAX request with SweetAlert confirmation.
     */
    initEnrollment: function() {
        const enrollBtns = document.querySelectorAll('.btn-enroll');
        enrollBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const enrollUrl = this.dataset.enrollUrl;
                const price = parseFloat(this.dataset.price || 0);
                const csrfToken = this.dataset.csrf;
                
                Swal.fire({
                    title: 'تأكيد التسجيل',
                    text: price === 0 ? 'هذه الدورة مجانية، هل تريد الانضمام إليها الآن؟' : 'سيتم إنشاء طلب تسجيل، وسيتعين عليك رفع إيصال الدفع لتفعيل حسابك.',
                    icon: price === 0 ? 'question' : 'info',
                    showCancelButton: true,
                    confirmButtonText: 'نعم، أريد التسجيل',
                    cancelButtonText: 'إلغاء',
                    confirmButtonColor: '#06b6d4',
                    cancelButtonColor: '#64748b',
                    background: '#ffffff',
                    customClass: { popup: 'rounded-4 border-0 shadow-lg' }
                }).then((result) => {
                    if (result.isConfirmed) {
                        const formData = new FormData();
                        formData.append('csrfmiddlewaretoken', csrfToken);
                        
                        fetch(enrollUrl, {
                            method: 'POST',
                            body: formData,
                            headers: { 'X-Requested-With': 'XMLHttpRequest' }
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                Swal.fire('تم!', data.message, 'success').then(() => {
                                    if (data.requires_payment) {
                                        window.location.reload();
                                    } else {
                                        window.location.href = data.redirect_url;
                                    }
                                });
                            } else {
                                Swal.fire('خطأ', data.errors[0], 'error');
                            }
                        });
                    }
                });
            });
        });
    },

    /**
     * Handles the payment receipt submission via AJAX.
     */
    initPaymentSubmission: function() {
        const paymentForm = document.getElementById('submitPaymentForm');
        if (paymentForm) {
            paymentForm.addEventListener('submit', function(e) {
                e.preventDefault();
                const submitUrl = this.dataset.url;
                const csrfToken = this.dataset.csrf;
                const formData = new FormData(this);
                const submitBtn = document.getElementById('submitPaymentBtn');
                
                submitBtn.disabled = true;
                const originalHtml = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin ms-2"></i> جاري الإرسال...';

                formData.append('csrfmiddlewaretoken', csrfToken);

                fetch(submitUrl, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        Swal.fire('تم الإرسال!', data.message, 'success').then(() => {
                            window.location.reload();
                        });
                    } else {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalHtml;
                        Swal.fire('خطأ', data.errors[0], 'error');
                    }
                })
                .catch(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalHtml;
                    Swal.fire('خطأ', 'حدث خطأ في الاتصال', 'error');
                });
            });
        }
    }
};

document.addEventListener('DOMContentLoaded', () => CourseHandler.init());
