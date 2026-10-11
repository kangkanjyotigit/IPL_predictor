/**
 * Form Debug Helper
 * This script helps diagnose form submission issues
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Form Debug Helper loaded');
    
    // Find all forms on the page
    const forms = document.querySelectorAll('form');
    console.log(`Found ${forms.length} forms on the page`);
    
    // Add debug listeners to each form
    forms.forEach((form, index) => {
        console.log(`Form #${index+1}:`, {
            id: form.id || 'No ID',
            action: form.action,
            method: form.method,
            elements: form.elements.length
        });
        
        // Log form data on submit
        form.addEventListener('submit', function(e) {
            console.log(`Form #${index+1} (${form.id || 'No ID'}) is being submitted`);
            
            // Create FormData object to easily access form values
            const formData = new FormData(form);
            console.log('Form data:');
            
            // Log each form field
            for (let [key, value] of formData.entries()) {
                console.log(`  ${key}: ${value}`);
            }
            
            // Check for CSRF token
            const csrfToken = formData.get('csrf_token');
            if (csrfToken) {
                console.log('CSRF token is present:', csrfToken.substring(0, 10) + '...');
            } else {
                console.error('CSRF token is missing!');
                // Don't prevent form submission, just log the error
            }
        });
    });
    
    // Add special handling for auto-generate form
    const autoGenerateForm = document.getElementById('autoGenerateForm');
    if (autoGenerateForm) {
        console.log('Auto-generate form found, adding special debug handlers');
        
        // Check form structure
        const formElements = Array.from(autoGenerateForm.elements);
        formElements.forEach(element => {
            console.log('Form element:', {
                name: element.name,
                id: element.id,
                type: element.type,
                value: element.value
            });
        });
    }
});
