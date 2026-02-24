/**
 * Ultra Select Component Logic
 * Handles custom dropdown interactions, selection, and form submission.
 */

const UltraSelect = {
    init() {
        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.ultra-select-container')) {
                this.closeAll();
            }
        });
    },

    toggle(name) {
        const dropdown = document.getElementById('dropdown-' + name);
        const wrapper = dropdown.previousElementSibling;
        const container = document.getElementById('custom-select-' + name);
        
        // Close other dropdowns
        document.querySelectorAll('.ultra-dropdown').forEach(d => {
            if (d.id !== 'dropdown-' + name) d.classList.remove('show');
        });
        document.querySelectorAll('.ultra-select-wrapper').forEach(w => {
            if (w !== wrapper) w.classList.remove('open');
        });
        document.querySelectorAll('.ultra-select-container').forEach(c => {
            if (c !== container) c.classList.remove('ultra-select-open');
        });

        // Toggle current
        dropdown.classList.toggle('show');
        wrapper.classList.toggle('open');
        container.classList.toggle('ultra-select-open');
    },

    select(name, val, label) {
        const input = document.getElementById('input-' + name);
        const container = document.getElementById('custom-select-' + name);
        const display = container.querySelector('.ultra-selected-value');
        
        // Update values
        input.value = val;
        display.textContent = label;
        
        // Trigger change event so other scripts can listen
        input.dispatchEvent(new Event('change', { bubbles: true }));
        
        // Update active state in UI
        const dropdown = document.getElementById('dropdown-' + name);
        dropdown.querySelectorAll('.ultra-option').forEach(opt => {
            opt.classList.remove('active');
            if (opt.textContent.trim() === label.trim()) {
                opt.classList.add('active');
            }
        });
        
        this.closeAll();

        // Trigger form submission unless disabled
        const autoSubmit = container ? container.getAttribute('data-auto-submit') !== 'false' : true;
        
        const form = input.closest('form');
        if (form && autoSubmit) form.submit();
    },

    closeAll() {
        document.querySelectorAll('.ultra-dropdown').forEach(d => d.classList.remove('show'));
        document.querySelectorAll('.ultra-select-wrapper').forEach(w => w.classList.remove('open'));
        document.querySelectorAll('.ultra-select-container').forEach(c => c.classList.remove('ultra-select-open'));
    }
};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => UltraSelect.init());

// Export to window for inline onclick handlers
window.toggleUltraDropdown = (name) => UltraSelect.toggle(name);
window.selectUltraOption = (name, val, label) => UltraSelect.select(name, val, label);
