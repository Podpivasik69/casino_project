// Dice Game JavaScript
let selectedNumber = null;
let isPlaying = false;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadHistory();
    
    // Add click handlers to dice numbers
    document.querySelectorAll('.dice-number').forEach(dice => {
        dice.addEventListener('click', function() {
            if (!isPlaying) {
                selectNumber(parseInt(this.dataset.number));
            }
        });
    });
});

function selectNumber(number) {
    if (isPlaying) return;
    
    selectedNumber = number;
    
    // Update UI
    document.querySelectorAll('.dice-number').forEach(dice => {
        dice.classList.remove('selected');
    });
    document.querySelector(`[data-number="${number}"]`).classList.add('selected');
    
    // Enable play button
    document.getElementById('playBtn').disabled = false;
}

function setBet(amount) {
    const betInput = document.getElementById('betAmount');
    if (amount === 0) {
        betInput.value = '0';
    } else {
        betInput.value = parseFloat(betInput.value || 0) + amount;
    }
}

async function playGame() {
    if (isPlaying || selectedNumber === null) return;
    
    const betAmount = parseFloat(document.getElementById('betAmount').value);
    
    if (betAmount < 0.01) {
        showNotification('Минимальная ставка: 0.01 ₽', 'error');
        return;
    }
    
    isPlaying = true;
    document.getElementById('playBtn').disabled = true;
    document.getElementById('resultDisplay').style.display = 'none';
    
    // Remove previous result classes
    document.querySelectorAll('.dice-number').forEach(dice => {
        dice.classList.remove('rolled', 'win', 'lose');
    });
    
    try {
        // Make API call
        const response = await fetch('/api/games/dice/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                bet_amount: betAmount.toFixed(2),
                selected_number: selectedNumber
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Start animation
            await animateDiceRoll(data.data.rolled_number);
            
            // Add rolled class to the rolled number
            const rolledDice = document.querySelector(`[data-number="${data.data.rolled_number}"]`);
            if (rolledDice) {
                rolledDice.classList.add('rolled');
                if (data.data.won) {
                    rolledDice.classList.add('win');
                } else {
                    rolledDice.classList.add('lose');
                }
            }
            
            // Wait a bit to show the result
            await new Promise(resolve => setTimeout(resolve, 600));
            
            // Update balance
            document.getElementById('balance').textContent = data.data.balance;
            
            // Show result
            showResult(data.data);
            
            // Reload history
            loadHistory();
            
            // Show notification
            if (data.data.won) {
                showNotification(`Вы выиграли ${data.data.winnings} ₽!`, 'success');
            } else {
                showNotification('Не повезло. Попробуйте еще раз!', 'info');
            }
        } else {
            showNotification(data.error || 'Ошибка при создании игры', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Произошла ошибка', 'error');
    } finally {
        isPlaying = false;
        document.getElementById('playBtn').disabled = false;
    }
}

// Simple animation function
async function animateDiceRoll(targetNumber) {
    const highlightEl = document.getElementById('diceHighlight');
    const tilePositions = getTilePositions();
    
    highlightEl.classList.add('active');
    highlightEl.classList.remove('lose');
    
    // Fast cycles (2 full cycles)
    const fastCycles = 2;
    const fastSpeed = 80; // ms per tile
    
    for (let cycle = 0; cycle < fastCycles; cycle++) {
        for (let i = 1; i <= 6; i++) {
            moveHighlightToTile(highlightEl, i, tilePositions);
            await sleep(fastSpeed);
        }
    }
    
    // Slow down to target
    let currentSpeed = fastSpeed;
    const speedIncrement = 40;
    
    for (let i = 1; i <= targetNumber; i++) {
        moveHighlightToTile(highlightEl, i, tilePositions);
        await sleep(currentSpeed);
        currentSpeed += speedIncrement; // Gradually slow down
    }
    
    // Final pause on result
    await sleep(300);
}

function getTilePositions() {
    const diceGrid = document.getElementById('diceGrid');
    const gridRect = diceGrid.getBoundingClientRect();
    const positions = {};
    
    for (let i = 1; i <= 6; i++) {
        const dice = document.querySelector(`[data-number="${i}"]`);
        const rect = dice.getBoundingClientRect();
        positions[i] = {
            x: rect.left - gridRect.left,
            y: rect.top - gridRect.top
        };
    }
    
    return positions;
}

function moveHighlightToTile(highlightEl, tileNumber, positions) {
    const pos = positions[tileNumber];
    highlightEl.style.transform = `translate(${pos.x}px, ${pos.y}px)`;
    highlightEl.style.opacity = '1';
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function showResult(gameData) {
    const resultDisplay = document.getElementById('resultDisplay');
    const resultCard = resultDisplay.querySelector('.result-card');
    const resultTitle = document.getElementById('resultTitle');
    const rolledDice = document.getElementById('rolledDice');
    const resultText = document.getElementById('resultText');
    const winningsText = document.getElementById('winningsText');
    
    // Set result
    if (gameData.won) {
        resultCard.className = 'result-card win';
        resultTitle.textContent = '🎉 Победа!';
        resultText.textContent = `Вы выбрали ${gameData.selected_number}, выпало ${gameData.rolled_number}`;
        winningsText.textContent = `Выигрыш: +${gameData.winnings} ₽`;
    } else {
        resultCard.className = 'result-card lose';
        resultTitle.textContent = '😔 Проигрыш';
        resultText.textContent = `Вы выбрали ${gameData.selected_number}, выпало ${gameData.rolled_number}`;
        winningsText.textContent = `Потеряно: -${gameData.bet_amount} ₽`;
    }
    
    rolledDice.textContent = gameData.rolled_number;
    resultDisplay.style.display = 'block';
}

async function loadHistory() {
    try {
        const response = await fetch('/api/games/dice/history/?limit=10');
        const data = await response.json();
        
        if (data.success) {
            const historyList = document.getElementById('historyList');
            
            if (data.data.games.length === 0) {
                historyList.innerHTML = '<p style="text-align: center; color: var(--gray);">История игр пуста</p>';
                return;
            }
            
            historyList.innerHTML = data.data.games.map(game => `
                <div class="history-item ${game.won ? 'win' : 'lose'}">
                    <div class="history-info">
                        <div class="history-numbers">
                            <span>Выбрано: ${game.selected_number}</span>
                            <i class="fas fa-arrow-right"></i>
                            <span>Выпало: ${game.rolled_number}</span>
                        </div>
                        <span style="color: var(--gray);">Ставка: ${game.bet_amount} ₽</span>
                    </div>
                    <div class="history-result ${game.won ? 'win' : 'lose'}">
                        ${game.won ? '+' : '-'}${game.won ? game.winnings : game.bet_amount} ₽
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}
