/**
 * Crash Game JavaScript
 * 
 * Handles:
 * - Real-time multiplier updates via AJAX polling
 * - Graph animation
 * - Bet placement and cashout
 * - Round state management
 * - History updates
 */

// Global state
let currentRound = null;
let currentMultiplier = 1.00;
let roundStatus = 'waiting';
let userBets = [];
let pollingInterval = null;
let canvas = null;
let ctx = null;
let graphData = [];

// Constants
const POLLING_INTERVAL = 100; // ms
const API_BASE = '/api/games/crash';

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeGame();
});

function initializeGame() {
    // Get canvas
    canvas = document.getElementById('crashGraph');
    ctx = canvas.getContext('2d');
    
    // Set up event listeners
    document.getElementById('betButton').addEventListener('click', placeBet);
    document.getElementById('cashoutButton').addEventListener('click', cashout);
    
    // Load history
    loadHistory();
    
    // Start polling
    startPolling();
}

function startPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    pollingInterval = setInterval(updateGameState, POLLING_INTERVAL);
    updateGameState(); // Initial call
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

async function updateGameState() {
    try {
        const response = await fetch(`${API_BASE}/current/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            console.error('Failed to fetch game state');
            return;
        }
        
        const data = await response.json();
        
        // Update current round
        currentRound = data;
        roundStatus = data.status;
        
        // Handle different states
        if (roundStatus === 'waiting') {
            handleWaitingState(data);
        } else if (roundStatus === 'active') {
            handleActiveState(data);
        } else if (roundStatus === 'crashed') {
            handleCrashedState(data);
        }
        
    } catch (error) {
        console.error('Error updating game state:', error);
    }
}

function handleWaitingState(data) {
    // Update status
    document.getElementById('statusText').textContent = 'Ожидание следующего раунда...';
    document.getElementById('countdown').textContent = `${data.seconds_until_start || 0}s`;
    
    // Update multiplier display
    document.getElementById('multiplierValue').textContent = '1.00';
    document.getElementById('multiplierDisplay').className = 'multiplier-display waiting';
    
    // Enable bet button, disable cashout
    document.getElementById('betButton').disabled = false;
    document.getElementById('cashoutButton').disabled = true;
    
    // Clear graph
    clearGraph();
}

function handleActiveState(data) {
    // Update multiplier
    currentMultiplier = parseFloat(data.current_multiplier);
    document.getElementById('multiplierValue').textContent = currentMultiplier.toFixed(2);
    document.getElementById('multiplierDisplay').className = 'multiplier-display active';
    
    // Update status
    document.getElementById('statusText').textContent = 'Раунд активен!';
    document.getElementById('countdown').textContent = '';
    
    // Update user bets
    userBets = data.user_bets || [];
    updateBetsDisplay();
    
    // Enable/disable buttons based on bets
    const hasActiveBets = userBets.some(bet => bet.status === 'active');
    document.getElementById('betButton').disabled = hasActiveBets;
    document.getElementById('cashoutButton').disabled = !hasActiveBets;
    
    // Update graph
    updateGraph(currentMultiplier);
}

function handleCrashedState(data) {
    // Update status
    document.getElementById('statusText').textContent = `КРАШ! ${data.crash_point}x`;
    document.getElementById('multiplierValue').textContent = data.crash_point;
    document.getElementById('multiplierDisplay').className = 'multiplier-display crashed';
    
    // Disable all buttons
    document.getElementById('betButton').disabled = true;
    document.getElementById('cashoutButton').disabled = true;
    
    // Play crash animation
    playCrashAnimation();
    
    // Reload history
    loadHistory();
    
    // Clear bets display after a delay
    setTimeout(() => {
        userBets = [];
        updateBetsDisplay();
    }, 2000);
}

function updateBetsDisplay() {
    const container = document.getElementById('betsContainer');
    
    if (userBets.length === 0) {
        container.innerHTML = '<p class="no-bets">Нет активных ставок</p>';
        return;
    }
    
    container.innerHTML = '';
    
    userBets.forEach(bet => {
        const betElement = document.createElement('div');
        betElement.className = `bet-item ${bet.status}`;
        
        let content = `
            <div class="bet-amount">Ставка: ${bet.bet_amount} ₽</div>
        `;
        
        if (bet.status === 'active') {
            content += `
                <div class="potential-win">Потенциальный выигрыш: ${bet.potential_win} ₽</div>
            `;
            if (bet.auto_cashout_target) {
                content += `
                    <div class="auto-cashout">Авто-кэшаут: ${bet.auto_cashout_target}x</div>
                `;
            }
        } else if (bet.status === 'cashed_out') {
            content += `
                <div class="win-amount">Выигрыш: ${bet.win_amount} ₽ (${bet.cashout_multiplier}x)</div>
            `;
        } else if (bet.status === 'lost') {
            content += `
                <div class="lost">Проиграно</div>
            `;
        }
        
        betElement.innerHTML = content;
        container.appendChild(betElement);
    });
}

async function placeBet() {
    const betAmount = parseFloat(document.getElementById('betAmount').value);
    const autoCashout = document.getElementById('autoCashout').value;
    
    if (!betAmount || betAmount < 0.01) {
        alert('Минимальная ставка: 0.01 ₽');
        return;
    }
    
    if (betAmount > 1000) {
        alert('Максимальная ставка: 1000 ₽');
        return;
    }
    
    const requestData = {
        amount: betAmount.toFixed(2)
    };
    
    if (autoCashout && parseFloat(autoCashout) >= 1.01) {
        requestData.auto_cashout_target = parseFloat(autoCashout).toFixed(2);
    }
    
    try {
        const response = await fetch(`${API_BASE}/bet/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'same-origin',
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            alert(data.error || 'Ошибка при размещении ставки');
            return;
        }
        
        // Update balance
        document.getElementById('balance').textContent = data.balance;
        
        // Disable bet button
        document.getElementById('betButton').disabled = true;
        
        // Force update game state
        updateGameState();
        
    } catch (error) {
        console.error('Error placing bet:', error);
        alert('Ошибка при размещении ставки');
    }
}

async function cashout() {
    // Find active bet
    const activeBet = userBets.find(bet => bet.status === 'active');
    if (!activeBet) {
        alert('Нет активных ставок');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/cashout/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                bet_id: activeBet.id
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            alert(data.error || 'Ошибка при кэшауте');
            return;
        }
        
        // Update balance
        document.getElementById('balance').textContent = data.balance;
        
        // Show win notification
        showWinNotification(data.win_amount, data.cashout_multiplier);
        
        // Disable cashout button
        document.getElementById('cashoutButton').disabled = true;
        
        // Force update game state
        updateGameState();
        
    } catch (error) {
        console.error('Error cashing out:', error);
        alert('Ошибка при кэшауте');
    }
}

async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE}/history/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            console.error('Failed to load history');
            return;
        }
        
        const data = await response.json();
        displayHistory(data.rounds);
        
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

function displayHistory(rounds) {
    const container = document.getElementById('historyContainer');
    container.innerHTML = '';
    
    rounds.forEach(round => {
        const crashPoint = parseFloat(round.crash_point);
        const badge = document.createElement('div');
        badge.className = 'history-badge';
        
        // Color coding
        if (crashPoint < 2.0) {
            badge.classList.add('low');
        } else if (crashPoint < 5.0) {
            badge.classList.add('medium');
        } else {
            badge.classList.add('high');
        }
        
        badge.textContent = `${crashPoint.toFixed(2)}x`;
        container.appendChild(badge);
    });
}

function clearGraph() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    graphData = [];
    drawGrid();
}

function drawGrid() {
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 1;
    
    // Horizontal lines
    for (let i = 0; i <= 10; i++) {
        const y = (canvas.height / 10) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
    }
    
    // Vertical lines
    for (let i = 0; i <= 10; i++) {
        const x = (canvas.width / 10) * i;
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
    }
}

function updateGraph(multiplier) {
    // Add data point
    graphData.push(multiplier);
    
    // Keep last 100 points
    if (graphData.length > 100) {
        graphData.shift();
    }
    
    // Clear and redraw
    clearGraph();
    
    if (graphData.length < 2) return;
    
    // Draw line
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 3;
    ctx.beginPath();
    
    const maxMultiplier = Math.max(...graphData, 2);
    const xStep = canvas.width / (graphData.length - 1);
    
    graphData.forEach((mult, index) => {
        const x = index * xStep;
        const y = canvas.height - (mult / maxMultiplier) * canvas.height * 0.9;
        
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    
    ctx.stroke();
}

function playCrashAnimation() {
    // Screen shake
    const container = document.querySelector('.crash-container');
    container.classList.add('shake');
    
    setTimeout(() => {
        container.classList.remove('shake');
    }, 500);
    
    // Red flash
    const flash = document.createElement('div');
    flash.className = 'crash-flash';
    document.body.appendChild(flash);
    
    setTimeout(() => {
        flash.remove();
    }, 300);
}

function showWinNotification(amount, multiplier) {
    const notification = document.createElement('div');
    notification.className = 'win-notification';
    notification.innerHTML = `
        <div class="win-amount">+${amount} ₽</div>
        <div class="win-multiplier">${multiplier}x</div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

function getCookie(name) {
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
