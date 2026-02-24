(function() {
    const categoryInput = document.getElementById('input-category');
    if (!categoryInput) return;
    
    function updateCategoryFields() {
        const category = categoryInput.value;
        const childFields = document.getElementById('childFields');
        const elderlyFields = document.getElementById('elderlyFields');
        
        if (childFields) {
            childFields.style.display = category === 'child' ? 'block' : 'none';
        }
        if (elderlyFields) {
            elderlyFields.style.display = category === 'elderly' ? 'block' : 'none';
        }
    }
    
    // Listen for change event from ultra_select.js
    categoryInput.addEventListener('change', updateCategoryFields);
    
    // Also check on load in case there's a pre-selected value
    updateCategoryFields();
})();
