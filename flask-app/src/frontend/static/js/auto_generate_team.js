/**
 * Auto Generate Team JavaScript
 * Handles form validation, loading indicators, and team visualization
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded - auto_generate_team.js initialized');
    
    // Get form elements
    const form = document.getElementById('autoGenerateForm');
    const loadingDiv = document.getElementById('loading');
    const weightInputs = document.querySelectorAll('.weight-input');
    const feedbackDiv = document.getElementById('validation-feedback');
    const chartContainer = document.getElementById('chartData');
    
    console.log('Form found:', !!form);
    console.log('Loading div found:', !!loadingDiv);
    console.log('Weight inputs found:', weightInputs.length);
    console.log('Feedback div found:', !!feedbackDiv);
    console.log('Chart container found:', !!chartContainer);
    
    // Function to validate weights
    function validateWeights() {
        let sum = 0;
        let allValid = true;
        
        // Calculate sum of all weights
        weightInputs.forEach(function(input) {
            const value = parseFloat(input.value) || 0;
            if (value < 0 || value > 1) {
                allValid = false;
            }
            sum += value;
        });
        
        // Round sum to 2 decimal places to avoid floating point issues
        sum = Math.round(sum * 100) / 100;
        console.log('Weight validation - Sum:', sum, 'All valid:', allValid);
        
        // Update feedback
        if (feedbackDiv) {
            if (!allValid) {
                feedbackDiv.className = 'alert alert-danger';
                feedbackDiv.innerHTML = '<strong>Error:</strong> All weights must be between 0 and 1';
            } else if (sum !== 1.0) {
                feedbackDiv.className = 'alert alert-warning';
                feedbackDiv.innerHTML = '<strong>Warning:</strong> Weights must sum to 1.0. Current sum: ' + sum;
            } else {
                feedbackDiv.className = 'alert alert-success';
                feedbackDiv.innerHTML = '<strong>Perfect!</strong> Your weights sum to 1.0';
            }
        }
        
        return sum === 1.0 && allValid;
    }
    
    // Add event listeners to weight inputs
    weightInputs.forEach(function(input) {
        input.addEventListener('input', validateWeights);
    });
    
    // Add submit event listener to form
    if (form) {
        form.addEventListener('submit', function(e) {
            console.log('Form submit event triggered');
            
            // Validate weights
            if (!validateWeights()) {
                console.log('Weight validation failed, preventing form submission');
                e.preventDefault();
                return false;
            }
            
            // Show loading spinner
            if (loadingDiv) {
                console.log('Showing loading indicator');
                loadingDiv.style.display = 'block';
            }
            
            console.log('Form submission proceeding');
            return true;
        });
    }
    
    // Initialize validation on page load
    validateWeights();
    
    // Update progress bars if they exist
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(function(bar) {
        const percentage = bar.getAttribute('data-percentage');
        if (percentage) {
            bar.style.width = percentage + '%';
            bar.textContent = percentage + '%';
        }
    });
    
    // Create pie chart if team is generated
    if (chartContainer && chartContainer.getAttribute('data-generated') === 'true') {
        try {
            console.log('Team generated, creating chart');
            const ctx = document.getElementById('teamCompositionChart');
            if (ctx) {
                // Get data from data attributes
                const roleLabelsStr = chartContainer.getAttribute('data-roles');
                const roleCountsStr = chartContainer.getAttribute('data-counts');
                
                console.log('Chart data attributes - Roles:', roleLabelsStr, 'Counts:', roleCountsStr);
                
                let roleLabels = [];
                let roleCounts = [];
                
                try {
                    roleLabels = JSON.parse(roleLabelsStr || '[]');
                    
                    // Parse the counts which might be a string like "[1,2,3]"
                    if (roleCountsStr && roleCountsStr.trim()) {
                        // Remove brackets if present
                        let countsStr = roleCountsStr.trim();
                        if (countsStr.startsWith('[') && countsStr.endsWith(']')) {
                            countsStr = countsStr.substring(1, countsStr.length - 1);
                        }
                        
                        // Split by comma and convert to numbers
                        roleCounts = countsStr.split(',').map(function(item) {
                            return parseInt(item.trim(), 10);
                        });
                    }
                } catch (parseError) {
                    console.error('Error parsing chart data:', parseError);
                    console.error('roleLabelsStr:', roleLabelsStr);
                    console.error('roleCountsStr:', roleCountsStr);
                    roleLabels = [];
                    roleCounts = [];
                }
                
                console.log('Parsed chart data - Roles:', roleLabels, 'Counts:', roleCounts);
                
                // Create the chart
                if (roleLabels.length > 0 && roleCounts.length > 0) {
                    const myChart = new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: roleLabels,
                            datasets: [{
                                data: roleCounts,
                                backgroundColor: [
                                    'rgba(255, 99, 132, 0.7)',
                                    'rgba(54, 162, 235, 0.7)',
                                    'rgba(255, 206, 86, 0.7)',
                                    'rgba(75, 192, 192, 0.7)',
                                    'rgba(153, 102, 255, 0.7)'
                                ],
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                legend: {
                                    position: 'bottom'
                                },
                                title: {
                                    display: true,
                                    text: 'Team Composition by Role'
                                }
                            }
                        }
                    });
                    console.log('Chart created successfully');
                } else {
                    console.warn('No valid chart data available');
                    showChartError('No valid data available for chart visualization.');
                }
            } else {
                console.error('Chart canvas element not found');
                showChartError('Chart canvas element not found.');
            }
        } catch (error) {
            console.error('Error creating chart:', error);
            showChartError('Unable to display chart visualization.');
        }
    }
    
    // Helper function to show chart errors
    function showChartError(message) {
        const chartElement = document.getElementById('teamCompositionChart');
        if (chartElement) {
            const fallbackElement = document.createElement('div');
            fallbackElement.className = 'alert alert-warning';
            fallbackElement.textContent = message;
            chartElement.parentNode.replaceChild(fallbackElement, chartElement);
        }
    }
    
    // Check authentication status
    const navbarUserSection = document.querySelector('.navbar-nav:last-child');
    if (navbarUserSection) {
        console.log('Navbar user section HTML:', navbarUserSection.innerHTML);
        const loginLink = navbarUserSection.querySelector('a[href="/login"]');
        console.log('Login link found:', !!loginLink);
        if (loginLink) {
            console.warn('User appears to be logged out (login link visible)');
        } else {
            console.log('User appears to be logged in (no login link visible)');
        }
    }
});
