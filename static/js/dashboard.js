/**
 * AI Crypto Trading Bot - Dashboard JavaScript
 * Handles real-time updates, chart rendering, and user interactions
 */

// Global variables
let pnlChart = null;
let signalChart = null;
let refreshInterval = null;
let sessionStartTime = new Date();
let logModal = null;

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');

    // Initialize Bootstrap modal
    logModal = new bootstrap.Modal(document.getElementById('logModal'));

    // Initialize charts
    initializePnLChart();
    initializeSignalChart();

    // Start auto-refresh
    startAutoRefresh();

    // Initial data load
    refreshData();

    // Update session timer
    updateSessionTimer();
    setInterval(updateSessionTimer, 1000);

    // Setup event listeners
    setupEventListeners();

    console.log('Dashboard initialized successfully');
});

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Trading mode selector
    document.getElementById('tradingModeSelect').addEventListener('change', function(e) {
        changeTradingMode(e.target.value);
    });

    // Log type selector
    document.getElementById('logTypeSelect').addEventListener('change', function() {
        loadLogs();
    });

    // Log search
    document.getElementById('logSearch').addEventListener('input', function(e) {
        filterLogs(e.target.value);
    });
}

/**
 * Start auto-refresh (every 30 seconds)
 */
function startAutoRefresh() {
    refreshInterval = setInterval(refreshData, 30000);
    console.log('Auto-refresh started (30 second interval)');
}

/**
 * Stop auto-refresh
 */
function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        console.log('Auto-refresh stopped');
    }
}

/**
 * Refresh all dashboard data
 */
async function refreshData() {
    console.log('Refreshing dashboard data...');

    try {
        await Promise.all([
            updateBotStatus(),
            updateMarketData(),
            updatePerformanceMetrics(),
            updateRecentTrades(),
            updateRecentSignals(),
            updateOpenPositions(),
            updateSystemHealth(),
            updateMarketContext(),
            updateChartAnalysis()
        ]);

        console.log('Dashboard data refreshed successfully');
    } catch (error) {
        console.error('Error refreshing dashboard:', error);
        showNotification('Error refreshing dashboard data', 'danger');
    }
}

/**
 * Update bot status
 */
async function updateBotStatus() {
    try {
        const response = await fetch('/api/bot-status');
        const data = await response.json();

        document.getElementById('botStatus').textContent = data.status;
        document.getElementById('botStatus').className = `badge ${data.status === 'RUNNING' ? 'bg-success' : 'bg-danger'}`;

        document.getElementById('botPid').textContent = data.pid;
        document.getElementById('botLastUpdate').textContent = formatTimestamp(data.last_update);

        document.getElementById('tradeExecution').textContent = data.trade_execution ? 'ENABLED' : 'DISABLED';
        document.getElementById('tradeExecution').className = `badge ${data.trade_execution ? 'bg-success' : 'bg-warning'}`;

        document.getElementById('tradingMode').textContent = data.trading_mode.toUpperCase();
        document.getElementById('totalSignals').textContent = formatNumber(data.total_signals);
        document.getElementById('openPositions').textContent = data.open_positions;
    } catch (error) {
        console.error('Error updating bot status:', error);
    }
}

/**
 * Update market data
 */
async function updateMarketData() {
    try {
        const response = await fetch('/api/market-data');
        const data = await response.json();

        document.getElementById('currentPrice').textContent = formatPrice(data.price);
        document.getElementById('rsi').textContent = formatNumber(data.rsi, 1);
        document.getElementById('vwap').textContent = formatPrice(data.vwap);

        const signalBadge = document.getElementById('currentSignal');
        signalBadge.textContent = `${data.signal} (${data.signal_strength})`;
        signalBadge.className = `badge signal-${data.signal.toLowerCase()}`;
    } catch (error) {
        console.error('Error updating market data:', error);
    }
}

/**
 * Update performance metrics
 */
async function updatePerformanceMetrics() {
    try {
        const response = await fetch('/api/performance-metrics');
        const data = await response.json();

        document.getElementById('winRate').textContent = `${data.win_rate}%`;
        document.getElementById('totalPnl').textContent = formatPrice(data.total_pnl);
        document.getElementById('totalPnl').className = data.total_pnl >= 0 ? 'text-success' : 'text-danger';

        document.getElementById('avgWin').textContent = formatPrice(data.avg_win);
        document.getElementById('avgLoss').textContent = formatPrice(data.avg_loss);
        document.getElementById('totalTrades').textContent = data.total_trades;
        document.getElementById('winningTrades').textContent = data.winning_trades;
        document.getElementById('losingTrades').textContent = data.losing_trades;
        document.getElementById('maxLoss').textContent = formatPrice(Math.abs(data.max_loss));

        // Calculate risk-reward ratio
        const riskReward = data.avg_loss !== 0 ? (data.avg_win / Math.abs(data.avg_loss)).toFixed(2) : '0.00';
        document.getElementById('riskReward').textContent = `1:${riskReward}`;

    } catch (error) {
        console.error('Error updating performance metrics:', error);
    }
}

/**
 * Update recent trades table
 */
async function updateRecentTrades() {
    try {
        const response = await fetch('/api/recent-trades?limit=10');
        const data = await response.json();

        const tbody = document.getElementById('recentTradesTable');
        tbody.innerHTML = '';

        if (data.trades && data.trades.length > 0) {
            data.trades.forEach(trade => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${formatTimestamp(trade.timestamp)}</td>
                    <td><span class="badge ${trade.side === 'BUY' ? 'bg-success' : 'bg-danger'}">${trade.side}</span></td>
                    <td>$${formatPrice(trade.entry_price)}</td>
                    <td class="${trade.pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}">$${formatPrice(trade.pnl)}</td>
                `;
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No trades yet</td></tr>';
        }
    } catch (error) {
        console.error('Error updating recent trades:', error);
    }
}

/**
 * Update recent signals table
 */
async function updateRecentSignals() {
    try {
        const response = await fetch('/api/recent-signals?limit=10');
        const data = await response.json();

        const tbody = document.getElementById('recentSignalsTable');
        tbody.innerHTML = '';

        if (data.signals && data.signals.length > 0) {
            data.signals.forEach(signal => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${formatTimestamp(signal.timestamp)}</td>
                    <td><span class="badge signal-${signal.signal.toLowerCase()}">${signal.signal}</span></td>
                    <td>${signal.signal_strength}</td>
                    <td>$${formatPrice(signal.price)}</td>
                `;
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No signals yet</td></tr>';
        }
    } catch (error) {
        console.error('Error updating recent signals:', error);
    }
}

/**
 * Update open positions table
 */
async function updateOpenPositions() {
    try {
        const response = await fetch('/api/open-positions');
        const data = await response.json();

        const tbody = document.getElementById('openPositionsTable');
        const livePosition = document.getElementById('livePosition');

        tbody.innerHTML = '';
        livePosition.innerHTML = '';

        if (data.positions && data.positions.length > 0) {
            data.positions.forEach(pos => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${formatTimestamp(pos.timestamp)}</td>
                    <td><span class="badge ${pos.side === 'LONG' ? 'bg-success' : 'bg-danger'}">${pos.side}</span></td>
                    <td>$${formatPrice(pos.entry_price)}</td>
                    <td>$${formatPrice(pos.current_price || pos.entry_price)}</td>
                    <td>${pos.size}</td>
                    <td class="${pos.unrealized_pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}">$${formatPrice(pos.unrealized_pnl || 0)}</td>
                `;
            });

            // Update live position display
            const firstPos = data.positions[0];
            livePosition.innerHTML = `
                <p><strong>Side:</strong> <span class="badge ${firstPos.side === 'LONG' ? 'bg-success' : 'bg-danger'}">${firstPos.side}</span></p>
                <p><strong>Size:</strong> ${firstPos.size}</p>
                <p><strong>Entry:</strong> $${formatPrice(firstPos.entry_price)}</p>
            `;
        } else {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No open positions</td></tr>';
            livePosition.innerHTML = '<p class="text-center text-muted">No open positions</p>';
        }
    } catch (error) {
        console.error('Error updating open positions:', error);
    }
}

/**
 * Update system health metrics
 */
async function updateSystemHealth() {
    try {
        const response = await fetch('/api/system-health');
        const data = await response.json();

        // CPU
        const cpuProgress = document.getElementById('cpuProgress');
        cpuProgress.style.width = `${data.cpu_usage}%`;
        cpuProgress.textContent = `${data.cpu_usage.toFixed(1)}%`;
        cpuProgress.className = `progress-bar ${getHealthColor(data.cpu_usage)}`;

        // Memory
        const memoryProgress = document.getElementById('memoryProgress');
        memoryProgress.style.width = `${data.memory_usage}%`;
        memoryProgress.textContent = `${data.memory_usage.toFixed(1)}%`;
        memoryProgress.className = `progress-bar ${getHealthColor(data.memory_usage)}`;
        document.getElementById('memoryDetails').textContent = `${data.memory_available} GB / ${data.memory_total} GB`;

        // Disk
        const diskProgress = document.getElementById('diskProgress');
        diskProgress.style.width = `${data.disk_usage}%`;
        diskProgress.textContent = `${data.disk_usage.toFixed(1)}%`;
        diskProgress.className = `progress-bar ${getHealthColor(data.disk_usage)}`;
        document.getElementById('diskDetails').textContent = `${data.disk_available} GB / ${data.disk_total} GB`;

    } catch (error) {
        console.error('Error updating system health:', error);
    }
}

/**
 * Update market context
 */
async function updateMarketContext() {
    try {
        const response = await fetch('/api/market-context');
        const data = await response.json();

        document.getElementById('btcPrice').textContent = `$${formatPrice(data.btc_price)}`;
        document.getElementById('btcChange').textContent = `${data.btc_change >= 0 ? '+' : ''}${data.btc_change.toFixed(2)}%`;
        document.getElementById('btcChange').className = data.btc_change >= 0 ? 'text-success' : 'text-danger';

        document.getElementById('ethPrice').textContent = `$${formatPrice(data.eth_price)}`;
        document.getElementById('ethChange').textContent = `${data.eth_change >= 0 ? '+' : ''}${data.eth_change.toFixed(2)}%`;
        document.getElementById('ethChange').className = data.eth_change >= 0 ? 'text-success' : 'text-danger';

        document.getElementById('btcDominance').textContent = `${data.btc_dominance}%`;
        document.getElementById('fearGreed').textContent = data.fear_greed_index;
        document.getElementById('marketTrend').textContent = data.market_trend;
        document.getElementById('marketRegime').textContent = data.market_regime;

    } catch (error) {
        console.error('Error updating market context:', error);
    }
}

/**
 * Update chart analysis
 */
async function updateChartAnalysis() {
    try {
        const response = await fetch('/api/chart-analysis');
        const data = await response.json();

        document.getElementById('aiRecommendation').textContent = data.recommendation;
        document.getElementById('aiRecommendation').className = `badge signal-${data.recommendation.toLowerCase()}`;

        document.getElementById('aiConfidence').textContent = data.confidence;
        document.getElementById('aiPrice').textContent = `$${formatPrice(data.price)}`;
        document.getElementById('aiChange').textContent = `${data.change_24h >= 0 ? '+' : ''}${data.change_24h}%`;

        // Key observations
        const obsDiv = document.getElementById('keyObservations');
        obsDiv.innerHTML = '';
        if (data.key_observations && data.key_observations.length > 0) {
            data.key_observations.forEach(obs => {
                const li = document.createElement('li');
                li.textContent = obs;
                obsDiv.appendChild(li);
            });
        }

        // Risk factors
        const riskDiv = document.getElementById('riskFactors');
        riskDiv.innerHTML = '';
        if (data.risk_factors && data.risk_factors.length > 0) {
            data.risk_factors.forEach(risk => {
                const li = document.createElement('li');
                li.textContent = risk;
                riskDiv.appendChild(li);
            });
        }

        document.getElementById('aiAnalysis').textContent = data.analysis;

    } catch (error) {
        console.error('Error updating chart analysis:', error);
    }
}

/**
 * Initialize PnL Chart
 */
function initializePnLChart() {
    const ctx = document.getElementById('pnlChart');
    if (!ctx) return;

    pnlChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Cumulative PnL',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'PnL ($)'
                    }
                }
            }
        }
    });
}

/**
 * Initialize Signal Strength Chart
 */
function initializeSignalChart() {
    const ctx = document.getElementById('signalChart');
    if (!ctx) return;

    signalChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Buy Signals',
                    data: [],
                    backgroundColor: 'rgba(40, 167, 69, 0.6)',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Sell Signals',
                    data: [],
                    backgroundColor: 'rgba(220, 53, 69, 0.6)',
                    borderColor: 'rgba(220, 53, 69, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Signal Strength'
                    },
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * Toggle pause/resume trading
 */
async function togglePause() {
    try {
        const response = await fetch('/api/control/pause', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success) {
            showNotification(data.paused ? 'Trading paused' : 'Trading resumed', 'success');
            await updateBotStatus();
        } else {
            showNotification('Failed to toggle pause', 'danger');
        }
    } catch (error) {
        console.error('Error toggling pause:', error);
        showNotification('Error toggling pause', 'danger');
    }
}

/**
 * Emergency close all positions
 */
async function emergencyClose() {
    if (!confirm('Are you sure you want to close all positions immediately? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch('/api/control/emergency-close', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Emergency close initiated', 'warning');
            await refreshData();
        } else {
            showNotification('Failed to initiate emergency close', 'danger');
        }
    } catch (error) {
        console.error('Error in emergency close:', error);
        showNotification('Error in emergency close', 'danger');
    }
}

/**
 * Change trading mode
 */
async function changeTradingMode(mode) {
    try {
        const response = await fetch('/api/control/trading-mode', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ mode })
        });

        const data = await response.json();

        if (data.success) {
            showNotification(`Trading mode changed to ${mode.toUpperCase()}`, 'success');
            await updateBotStatus();
        } else {
            showNotification('Failed to change trading mode', 'danger');
        }
    } catch (error) {
        console.error('Error changing trading mode:', error);
        showNotification('Error changing trading mode', 'danger');
    }
}

/**
 * View logs
 */
function viewLogs() {
    logModal.show();
    loadLogs();
}

/**
 * Load logs
 */
async function loadLogs() {
    const logType = document.getElementById('logTypeSelect').value;

    try {
        const response = await fetch(`/api/logs?type=${logType}&lines=200`);
        const data = await response.json();

        const logContent = document.getElementById('logContent');
        logContent.textContent = data.logs.join('\n');

        // Auto-scroll to bottom if enabled
        if (document.getElementById('autoScrollLogs').checked) {
            logContent.scrollTop = logContent.scrollHeight;
        }
    } catch (error) {
        console.error('Error loading logs:', error);
        document.getElementById('logContent').textContent = 'Error loading logs';
    }
}

/**
 * Filter logs
 */
function filterLogs(searchTerm) {
    const logContent = document.getElementById('logContent');
    const allLogs = logContent.textContent.split('\n');

    if (!searchTerm) {
        loadLogs();
        return;
    }

    const filtered = allLogs.filter(line =>
        line.toLowerCase().includes(searchTerm.toLowerCase())
    );

    logContent.textContent = filtered.join('\n');
}

/**
 * Download logs
 */
function downloadLogs() {
    const logContent = document.getElementById('logContent').textContent;
    const blob = new Blob([logContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trading-bot-logs-${new Date().toISOString()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Update session timer
 */
function updateSessionTimer() {
    const now = new Date();
    const elapsed = Math.floor((now - sessionStartTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;

    const timerElement = document.getElementById('sessionTimer');
    if (timerElement) {
        timerElement.textContent = `Session: ${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
}

/**
 * Utility Functions
 */

function formatPrice(price) {
    return parseFloat(price).toFixed(4);
}

function formatNumber(num, decimals = 0) {
    return parseFloat(num).toFixed(decimals);
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getHealthColor(percentage) {
    if (percentage < 60) return 'bg-success';
    if (percentage < 80) return 'bg-warning';
    return 'bg-danger';
}

function showNotification(message, type = 'info') {
    // Create toast notification
    const toastHTML = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    // Add to page
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    toastContainer.insertAdjacentHTML('beforeend', toastHTML);

    // Show toast
    const toastElement = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastElement);
    toast.show();

    // Remove after hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Export functions for use in HTML
window.refreshData = refreshData;
window.togglePause = togglePause;
window.emergencyClose = emergencyClose;
window.viewLogs = viewLogs;
window.loadLogs = loadLogs;
window.downloadLogs = downloadLogs;
