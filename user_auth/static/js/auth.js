/**
 * Rafikni Authentication Script
 * Handles form interactions, password visibility, and loading states.
 */

document.addEventListener('DOMContentLoaded', function() {
    // 1. Password Visibility Toggle
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    
    passwordInputs.forEach(input => {
        // Create the toggle button
        const toggleBtn = document.createElement('span');
        toggleBtn.className = 'input-group-text bg-white border-start-0 py-2 cursor-pointer';
        toggleBtn.innerHTML = '<i class="fa-solid fa-eye text-muted"></i>';
        toggleBtn.style.cursor = 'pointer';
        
        // Find the input group and append the toggle
        const inputGroup = input.parentElement;
        if (inputGroup && inputGroup.classList.contains('input-group')) {
            inputGroup.appendChild(toggleBtn);
            
            // Toggle logic
            toggleBtn.addEventListener('click', function() {
                const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                input.setAttribute('type', type);
                
                // Toggle icon
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

    // 4. Subtle Page Load Animation
    const cards = document.querySelectorAll('.glass-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'all 0.6s cubic-bezier(0.16, 1, 0.3, 1)';
        
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100 * (index + 1));
    });
});
