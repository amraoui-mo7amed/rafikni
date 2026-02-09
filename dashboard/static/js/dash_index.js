document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const mainContainer = document.querySelector('.main-container');

    // 1. Sidebar Toggle Logic
    function toggleSidebar() {
        if (window.innerWidth > 768) {
            sidebar.classList.toggle('collapsed');
        } else {
            sidebar.classList.toggle('active');
            sidebarOverlay.classList.toggle('show');
        }
        sidebarToggle.classList.toggle('active');
    }

    sidebarToggle.addEventListener('click', function(e) {
        e.stopPropagation();
        toggleSidebar();
    });

    // 2. Close sidebar on mobile when clicking overlay or main content
    sidebarOverlay.addEventListener('click', function() {
        if (sidebar.classList.contains('active')) {
            sidebar.classList.remove('active');
            sidebarOverlay.classList.remove('show');
        }
    });

    // 3. Active Link Highlighting
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            // Auto-close on mobile after selection
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('active');
                sidebarOverlay.classList.remove('show');
            }
        });
    });
});
