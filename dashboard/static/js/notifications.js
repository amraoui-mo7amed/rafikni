/**
 * Notification handler using django-eventstream
 * Connects to user-specific channel and handles real-time notifications
 */

(function() {
    'use strict';

    const NotificationHandler = {
        eventSource: null,
        channel: null,
        reconnectInterval: 5000,
        reconnectAttempts: 0,
        maxReconnectAttempts: 10,
        userId: null,

        /**
         * Initialize notification handler
         * @param {number} userId - The current user's ID
         */
        init: function(userId) {
            console.log('NotificationHandler: Initializing for user:', userId);
            if (!userId) {
                console.error('NotificationHandler: User ID is required');
                return;
            }

            this.userId = userId;
            this.channel = `user-${userId}`;
            this.connect();
            this.loadUnreadCount();
            this.reloadNotifications();
        },

        /**
         * Connect to EventStream endpoint
         */
        connect: function() {
            if (this.eventSource) {
                this.eventSource.close();
            }

            // Build URL with channel parameter
            const url = `/events/?channel=${this.channel}`;
            console.log('NotificationHandler: Connecting to:', url);
            
            // Use ReconnectingEventSource if available, otherwise use standard EventSource
            if (typeof ReconnectingEventSource !== 'undefined') {
                this.eventSource = new ReconnectingEventSource(url);
            } else {
                this.eventSource = new EventSource(url);
            }

            // Handle connection open
            this.eventSource.onopen = () => {
                console.log('NotificationHandler: SSE Connection established');
                this.reconnectAttempts = 0;
            };

            // Unified event handler
            const eventHandler = (e) => {
                console.log('NotificationHandler: Event received:', e.type);
                try {
                    const data = JSON.parse(e.data);
                    this.handleNotification(data);
                } catch (err) {
                    console.error('NotificationHandler: Error parsing data:', err);
                }
            };

            this.eventSource.addEventListener('message', eventHandler);
            this.eventSource.addEventListener('notification', eventHandler);

            // Handle errors
            this.eventSource.onerror = (e) => {
                console.error('NotificationHandler: Connection error:', e);
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    setTimeout(() => this.connect(), this.reconnectInterval);
                }
            };

            // Handle stream reset
            this.eventSource.addEventListener('stream-reset', (e) => {
                console.warn('NotificationHandler: Stream reset - reloading');
                this.reloadNotifications();
            });
        },

        /**
         * Handle incoming notification
         */
        handleNotification: function(data) {
            this.incrementUnreadCount();
            this.showToast(data);
            this.prependNotificationToList(data);
        },

        /**
         * Show modern popup notification
         */
        showToast: function(notification) {
            const iconMap = {
                'success': 'check-circle',
                'error': 'exclamation-circle',
                'warning': 'exclamation-triangle',
                'info': 'info-circle'
            };
            
            const icon = iconMap[notification.type] || 'bell';
            const toast = document.createElement('div');
            toast.className = `toast notification-toast notification-${notification.type}`;
            toast.setAttribute('role', 'alert');
            toast.setAttribute('aria-live', 'assertive');
            toast.setAttribute('aria-atomic', 'true');
            
            toast.innerHTML = `
                <div class="notification-content-wrapper">
                    <div class="notification-accent"></div>
                    <div class="notification-body-main">
                        <button type="button" class="btn-close-custom" aria-label="Close">
                            <i class="fas fa-times"></i>
                        </button>
                        <div class="notification-icon-wrapper">
                            <i class="fas fa-${icon}"></i>
                        </div>
                        <div class="notification-text-wrapper">
                            <div class="fw-bold mb-1">${notification.title}</div>
                            <div class="small text-muted">${notification.message}</div>
                        </div>
                    </div>
                </div>
            `;
            
            const container = document.getElementById('toast-container') || this.createToastContainer();
            container.appendChild(toast);
            
            // Manual close button logic
            const closeBtn = toast.querySelector('.btn-close-custom');
            closeBtn.addEventListener('click', () => {
                toast.classList.add('hide');
                setTimeout(() => toast.remove(), 300);
            });

            // Bootstrap trigger
            if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
                const bsToast = new bootstrap.Toast(toast, { delay: 6000 });
                bsToast.show();
            } else {
                toast.classList.add('show');
                setTimeout(() => toast.remove(), 6000);
            }
            
            toast.addEventListener('hidden.bs.toast', () => toast.remove());
        },

        createToastContainer: function() {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
            return container;
        },

        prependNotificationToList: function(notification) {
            const list = document.querySelector('.notification-list');
            if (!list) return;
            
            const item = this.createNotificationItem(notification);
            list.insertBefore(item, list.firstChild);
            
            const emptyState = list.querySelector('.notification-empty');
            if (emptyState) emptyState.remove();
        },

        createNotificationItem: function(notification) {
            const div = document.createElement('a');
            div.className = 'dropdown-item notification-item d-flex align-items-start py-2 border-bottom';
            if (!notification.is_read) div.classList.add('bg-light');
            
            div.href = notification.link || '#';
            div.dataset.id = notification.id;
            
            const iconMap = {
                'success': 'check-circle text-success',
                'error': 'exclamation-circle text-danger',
                'warning': 'exclamation-triangle text-warning',
                'info': 'info-circle text-info'
            };
            
            const icon = iconMap[notification.type] || 'bell text-secondary';
            
            div.innerHTML = `
                <div class="me-3 mt-1">
                    <i class="fas fa-${icon}"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="fw-bold small">${notification.title}</div>
                    <div class="text-muted x-small text-truncate" style="max-width: 250px;">
                        ${notification.message}
                    </div>
                    <div class="text-muted x-small">
                        ${this.formatTime(notification.created_at)}
                    </div>
                </div>
            `;
            
            div.addEventListener('click', (e) => {
                if (!notification.is_read) {
                    this.markAsRead(notification.id).then(data => {
                        if (data.success) {
                            div.classList.remove('bg-light');
                            notification.is_read = true;
                            this.loadUnreadCount();
                        }
                    });
                }
            });
            
            return div;
        },

        formatTime: function(timestamp) {
            const date = new Date(timestamp);
            const now = new Date();
            const diff = (now - date) / 1000;
            if (diff < 60) return 'الآن';
            if (diff < 3600) return `منذ ${Math.floor(diff / 60)} دقيقة`;
            if (diff < 86400) return `منذ ${Math.floor(diff / 3600)} ساعة`;
            return date.toLocaleDateString('ar-SA');
        },

        loadUnreadCount: function() {
            fetch('/dashboard/notifications/unread-count/', {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(res => res.json())
            .then(data => { if (data.success) this.updateUnreadBadge(data.count); });
        },

        incrementUnreadCount: function() {
            const badge = document.getElementById('notification-badge');
            const currentCount = parseInt(badge?.textContent) || 0;
            this.updateUnreadBadge(currentCount + 1);
        },

        updateUnreadBadge: function(count) {
            const badge = document.getElementById('notification-badge');
            if (badge) {
                badge.textContent = count > 0 ? count : '';
                badge.classList.toggle('d-none', count === 0);
            }
            const headerCount = document.getElementById('notification-count');
            if (headerCount) {
                headerCount.textContent = `${count} جديدة`;
                headerCount.classList.toggle('d-none', count === 0);
            }
        },

        reloadNotifications: function() {
            fetch('/dashboard/notifications/list/', {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(res => res.json())
            .then(data => { if (data.success) this.renderNotificationList(data.notifications); });
        },

        renderNotificationList: function(notifications) {
            const list = document.querySelector('.notification-list');
            if (!list) return;
            list.innerHTML = '';
            if (notifications.length === 0) {
                list.innerHTML = '<div class="notification-empty text-center py-4 text-muted">لا توجد إشعارات</div>';
                return;
            }
            notifications.forEach(n => list.appendChild(this.createNotificationItem(n)));
        },

        markAsRead: function(id) {
            return fetch(`/dashboard/notifications/${id}/read/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            }).then(res => res.json());
        },

        markAllAsRead: function() {
            return fetch('/dashboard/notifications/mark-all-read/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            }).then(res => res.json()).then(data => {
                if (data.success) {
                    this.updateUnreadBadge(0);
                    document.querySelectorAll('.notification-item').forEach(i => i.classList.remove('bg-light'));
                }
            });
        },

        getCsrfToken: function() {
            const name = 'csrftoken';
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
    };

    window.NotificationHandler = NotificationHandler;
})();
