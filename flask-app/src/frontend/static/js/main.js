// Main JavaScript file for Dream11 Prediction

// Wait for the DOM to be loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })
    
    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    })
    
    // Auto-dismiss alerts
    var alerts = document.querySelectorAll('.alert:not(.alert-permanent)')
    alerts.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert)
            bsAlert.close()
        }, 5000)
    })
    
    // Team builder form validation
    var teamBuilderForm = document.getElementById('team-builder-form')
    if (teamBuilderForm) {
        teamBuilderForm.addEventListener('submit', function(event) {
            if (!validateTeamComposition()) {
                event.preventDefault()
                event.stopPropagation()
            }
        })
    }
})

// Validate team composition
function validateTeamComposition() {
    var selectedPlayers = document.querySelectorAll('.player-checkbox:checked')
    var totalPlayers = selectedPlayers.length
    
    // Check total number of players
    if (totalPlayers !== 11) {
        showError('You must select exactly 11 players')
        return false
    }
    
    // Count players by type
    var playerCounts = {
        'wicket-keeper': 0,
        'batsman': 0,
        'all-rounder': 0,
        'bowler': 0
    }
    
    selectedPlayers.forEach(function(player) {
        var playerType = player.dataset.playerType
        playerCounts[playerType]++
    })
    
    // Validate composition
    if (playerCounts['wicket-keeper'] < 1) {
        showError('You must select at least 1 wicket-keeper')
        return false
    }
    if (playerCounts['batsman'] < 3) {
        showError('You must select at least 3 batsmen')
        return false
    }
    if (playerCounts['bowler'] < 3) {
        showError('You must select at least 3 bowlers')
        return false
    }
    if (playerCounts['all-rounder'] < 1) {
        showError('You must select at least 1 all-rounder')
        return false
    }
    
    return true
}

// Show error message
function showError(message) {
    var errorDiv = document.getElementById('team-error')
    if (errorDiv) {
        errorDiv.textContent = message
        errorDiv.style.display = 'block'
        
        // Auto-hide after 5 seconds
        setTimeout(function() {
            errorDiv.style.display = 'none'
        }, 5000)
    }
}

// Update team credits
function updateTeamCredits() {
    var selectedPlayers = document.querySelectorAll('.player-checkbox:checked')
    var totalCredits = 0
    
    selectedPlayers.forEach(function(player) {
        totalCredits += parseFloat(player.dataset.credits)
    })
    
    var creditsDisplay = document.getElementById('team-credits')
    if (creditsDisplay) {
        creditsDisplay.textContent = totalCredits.toFixed(1)
        
        // Highlight if exceeding 100 credits
        if (totalCredits > 100) {
            creditsDisplay.classList.add('text-danger')
        } else {
            creditsDisplay.classList.remove('text-danger')
        }
    }
}

// Handle player selection
function handlePlayerSelection(checkbox) {
    var playerType = checkbox.dataset.playerType
    var maxPlayers = {
        'wicket-keeper': 4,
        'batsman': 6,
        'all-rounder': 4,
        'bowler': 6
    }
    
    var selectedCount = document.querySelectorAll(`.player-checkbox[data-player-type="${playerType}"]:checked`).length
    
    if (checkbox.checked && selectedCount > maxPlayers[playerType]) {
        checkbox.checked = false
        showError(`You can't select more than ${maxPlayers[playerType]} ${playerType}s`)
        return
    }
    
    updateTeamCredits()
}

// Auto-generate team
function autoGenerateTeam(matchId) {
    fetch(`/api/team-prediction/${matchId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI with generated team
            updateTeamUI(data.team)
        } else {
            showError(data.message)
        }
    })
    .catch(error => {
        console.error('Error:', error)
        showError('Failed to generate team. Please try again.')
    })
}

// Update team UI
function updateTeamUI(team) {
    // Uncheck all players
    document.querySelectorAll('.player-checkbox').forEach(checkbox => {
        checkbox.checked = false
    })
    
    // Check selected players
    team.players.forEach(playerId => {
        var checkbox = document.querySelector(`.player-checkbox[value="${playerId}"]`)
        if (checkbox) {
            checkbox.checked = true
        }
    })
    
    // Update captain and vice-captain
    var captainSelect = document.getElementById('captain-select')
    var viceCaptainSelect = document.getElementById('vice-captain-select')
    
    if (captainSelect) {
        captainSelect.value = team.captain_id
    }
    if (viceCaptainSelect) {
        viceCaptainSelect.value = team.vice_captain_id
    }
    
    updateTeamCredits()
}
