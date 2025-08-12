// Algorand Compliance Frontend JavaScript

// Initialize all tooltips
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Copy to clipboard with toast notification
function setupCopyToClipboard() {
    document.querySelectorAll('.copy-icon').forEach(icon => {
        icon.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-clipboard-text');
            navigator.clipboard.writeText(textToCopy).then(() => {
                // Create toast
                const toast = document.createElement('div');
                toast.className = 'position-fixed bottom-0 end-0 p-3';
                toast.style.zIndex = '11';
                
                toast.innerHTML = `
                    <div id="liveToast" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                        <div class="toast-header">
                            <i class="fas fa-check-circle me-2 text-success"></i>
                            <strong class="me-auto">Copied!</strong>
                            <small>just now</small>
                            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                        </div>
                        <div class="toast-body">
                            <small class="text-muted">${textToCopy.substring(0, 30)}${textToCopy.length > 30 ? '...' : ''}</small>
                        </div>
                    </div>
                `;
                
                document.body.appendChild(toast);
                const bsToast = new bootstrap.Toast(toast.querySelector('.toast'));
                bsToast.show();
                
                // Remove toast after it's hidden
                toast.addEventListener('hidden.bs.toast', function () {
                    document.body.removeChild(toast);
                });
            });
        });
    });
}

// Hash preview on file upload
function setupFileHashPreview() {
    const fileInput = document.getElementById('document');
    const previewElement = document.getElementById('hashPreview');
    
    if (fileInput && previewElement) {
        fileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = async function(e) {
                    try {
                        // Compute SHA-256 hash of the file
                        const hashBuffer = await crypto.subtle.digest('SHA-256', e.target.result);
                        const hashArray = Array.from(new Uint8Array(hashBuffer));
                        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
                        
                        // Update preview
                        previewElement.innerHTML = `<div class="alert alert-info">
                            <i class="fas fa-fingerprint me-2"></i>
                            <strong>Document Hash Preview:</strong><br>
                            <small class="hash-code">${hashHex}</small>
                        </div>`;
                        previewElement.style.display = 'block';
                    } catch (e) {
                        console.error('Error generating hash:', e);
                    }
                };
                reader.readAsArrayBuffer(this.files[0]);
            }
        });
    }
}

// Compliance status visualization
function drawComplianceStatus(canvasId, status) {
    const canvas = document.getElementById(canvasId);
    if (canvas) {
        const ctx = canvas.getContext('2d');
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = canvas.width / 2 - 10;
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw circle
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI, false);
        ctx.lineWidth = 5;
        
        // Set color based on status
        if (status === 'compliant') {
            ctx.strokeStyle = '#198754'; // Bootstrap success
            ctx.fillStyle = 'rgba(25, 135, 84, 0.1)';
        } else if (status === 'expired') {
            ctx.strokeStyle = '#dc3545'; // Bootstrap danger
            ctx.fillStyle = 'rgba(220, 53, 69, 0.1)';
        } else {
            ctx.strokeStyle = '#ffc107'; // Bootstrap warning
            ctx.fillStyle = 'rgba(255, 193, 7, 0.1)';
        }
        
        ctx.stroke();
        ctx.fill();
        
        // Draw icon
        ctx.fillStyle = ctx.strokeStyle;
        ctx.font = 'bold 24px "Font Awesome 5 Free"';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        if (status === 'compliant') {
            ctx.fillText('\uf058', centerX, centerY); // fa-check-circle
        } else if (status === 'expired') {
            ctx.fillText('\uf057', centerX, centerY); // fa-times-circle
        } else {
            ctx.fillText('\uf017', centerX, centerY); // fa-clock
        }
    }
}

// Update countdown timers
function updateCountdowns() {
    document.querySelectorAll('.countdown-timer').forEach(timer => {
        const targetDate = new Date(timer.getAttribute('data-expiry'));
        const now = new Date();
        const diff = targetDate - now;
        
        if (diff <= 0) {
            timer.innerHTML = '<span class="text-danger">Expired</span>';
            timer.closest('tr').classList.add('table-danger');
        } else {
            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            
            if (days > 30) {
                timer.innerHTML = `<span class="text-success">${days} days</span>`;
            } else if (days > 7) {
                timer.innerHTML = `<span class="text-warning">${days} days, ${hours} hours</span>`;
            } else {
                timer.innerHTML = `<span class="text-danger">${days}d ${hours}h ${minutes}m</span>`;
            }
        }
    });
}

// Transaction monitoring with real-time API calls
function setupTransactionMonitoring() {
    const transactionMonitor = document.getElementById('transaction-monitor');
    if (!transactionMonitor) return;
    
    // Get the app ID from the URL if available
    let appId = null;
    const urlPath = window.location.pathname;
    const contractMatch = urlPath.match(/\/contracts\/([0-9]+)/); 
    if (contractMatch && contractMatch[1]) {
        appId = contractMatch[1];
    }
    
    // If we're on a contract detail page, fetch real transactions
    if (appId) {
        fetchTransactions(appId, transactionMonitor);
    } else {
        // Otherwise, use simulated transactions for the home page
        simulateTransactions(transactionMonitor);
    }
    
    // Setup auto-refresh every 30 seconds
    setInterval(() => {
        if (appId) {
            fetchTransactions(appId, transactionMonitor);
        }
    }, 30000);
}

// Fetch real transactions from API
function fetchTransactions(appId, container) {
    // Show loading indicator
    container.innerHTML = `
        <div class="d-flex align-items-center justify-content-center" style="height: 120px;">
            <div class="text-center text-muted">
                <i class="fas fa-sync fa-spin mb-3 display-6"></i>
                <p>Loading blockchain transactions...</p>
            </div>
        </div>
    `;
    
    // Fetch transactions from API
    fetch(`/api/transactions/${appId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            renderTransactions(data.transactions, container);
        })
        .catch(error => {
            // Handle errors gracefully
            console.error('Error fetching transactions:', error);
            container.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Unable to fetch transactions.</strong> Please try again later.
                    <div class="mt-2 small">${error.message}</div>
                </div>
                <div class="text-center mt-3">
                    <button class="btn btn-sm btn-outline-primary retry-btn">
                        <i class="fas fa-sync me-1"></i> Retry
                    </button>
                </div>
            `;
            
            // Add retry functionality
            const retryBtn = container.querySelector('.retry-btn');
            if (retryBtn) {
                retryBtn.addEventListener('click', () => fetchTransactions(appId, container));
            }
        });
}

// Simulate transactions for the dashboard
function simulateTransactions(container) {
    const txStatuses = [
        { type: 'Contract Deployment', status: 'success', time: '2 mins ago', txId: '3XYZ...A7B9' },
        { type: 'Document Registration', status: 'success', time: '15 mins ago', txId: 'HJ78...9Z10' },
        { type: 'Account Opt-In', status: 'pending', time: 'just now', txId: 'QW12...C3PO' }
    ];
    
    renderTransactions(txStatuses, container);
}

// Render transactions in container
function renderTransactions(transactions, container) {
    // If no transactions, show a message
    if (!transactions || transactions.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No transactions found for this contract yet.
            </div>
        `;
        return;
    }
    
    let html = `<div class="list-group">`;
    
    transactions.forEach(tx => {
        const statusClass = tx.status === 'success' || tx.status === 'confirmed' ? 'text-success' : 
                          tx.status === 'pending' ? 'text-warning' : 'text-danger';
        const statusIcon = tx.status === 'success' || tx.status === 'confirmed' ? 'check-circle' : 
                          tx.status === 'pending' ? 'clock' : 'times-circle';
        
        // Format timestamp if available
        let timeDisplay = tx.time || 'recent';
        if (tx.timestamp) {
            const txTime = new Date(tx.timestamp * 1000);
            const now = new Date();
            const diffMs = now - txTime;
            const diffMins = Math.round(diffMs / 60000);
            
            if (diffMins < 1) {
                timeDisplay = 'just now';
            } else if (diffMins < 60) {
                timeDisplay = `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
            } else {
                const diffHours = Math.floor(diffMins / 60);
                if (diffHours < 24) {
                    timeDisplay = `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
                } else {
                    timeDisplay = txTime.toLocaleString();
                }
            }
        }
                          
        html += `
            <div class="list-group-item list-group-item-action">
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${tx.type}</h6>
                    <small>${timeDisplay}</small>
                </div>
                <div class="d-flex justify-content-between">
                    <small class="text-muted">
                        <span class="d-none d-md-inline">Transaction ID: </span>
                        ${tx.txId}
                    </small>
                    <small class="${statusClass}">
                        <i class="fas fa-${statusIcon} me-1"></i>
                        ${tx.status}
                    </small>
                </div>
            </div>
        `;
    });
    
    html += `
        </div>
        <div class="mt-3 text-center d-flex justify-content-between align-items-center">
            <small class="text-muted">Last updated: ${new Date().toLocaleTimeString()}</small>
            <button class="btn btn-sm btn-outline-primary">
                <i class="fas fa-list me-1"></i> View All Transactions
            </button>
        </div>
    `;
    
    container.innerHTML = html;
}

// Initialize document preview
function setupDocumentPreview() {
    const previewButton = document.getElementById('previewDocument');
    const previewContainer = document.getElementById('documentPreviewContainer');
    
    if (previewButton && previewContainer) {
        previewButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (previewContainer.style.display === 'block') {
                previewContainer.style.display = 'none';
                previewButton.innerHTML = '<i class="fas fa-eye me-2"></i>Preview Document';
            } else {
                previewContainer.style.display = 'block';
                previewButton.innerHTML = '<i class="fas fa-eye-slash me-2"></i>Hide Preview';
                
                // Simulate document preview (this would be replaced with actual document content)
                const previewContent = `
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <span><i class="fas fa-file-alt me-2"></i>Document Preview</span>
                            <button type="button" class="btn-close" aria-label="Close"></button>
                        </div>
                        <div class="card-body">
                            <div class="p-3 bg-light border rounded">
                                <h5>Compliance Document</h5>
                                <p>This is a preview of the document content. In a real implementation, 
                                the actual document content would be displayed here.</p>
                                <pre class="bg-dark text-light p-2">{"version": "1.0.0", "status": "pending"}</pre>
                            </div>
                        </div>
                    </div>
                `;
                
                previewContainer.innerHTML = previewContent;
                
                // Add close button functionality
                const closeBtn = previewContainer.querySelector('.btn-close');
                if (closeBtn) {
                    closeBtn.addEventListener('click', function() {
                        previewContainer.style.display = 'none';
                        previewButton.innerHTML = '<i class="fas fa-eye me-2"></i>Preview Document';
                    });
                }
            }
        });
    }
}

// Initialize the application when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initTooltips();
    
    // Setup copy to clipboard
    setupCopyToClipboard();
    
    // Setup file hash preview
    setupFileHashPreview();
    
    // Draw compliance status if canvas exists
    if (document.getElementById('statusVisual')) {
        // Get status from data attribute (default to 'pending')
        const statusElement = document.getElementById('statusVisual');
        const status = statusElement.getAttribute('data-status') || 'pending';
        drawComplianceStatus('statusVisual', status);
    }
    
    // Start countdown timers
    updateCountdowns();
    setInterval(updateCountdowns, 60000); // Update every minute
    
    // Setup document preview
    setupDocumentPreview();
    
    // Setup real-time transaction monitoring
    setupTransactionMonitoring();
    
    // Setup form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
});

// Document hash live preview
function updateDocumentHashPreview(input) {
    const file = input.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const content = e.target.result;
            // This is just a preview - actual hashing is done server-side
            document.getElementById('hashPreview').textContent = 'File selected: ' + file.name;
            document.getElementById('hashPreviewContainer').style.display = 'block';
        };
        reader.readAsText(file);
    }
}

// Countdown timer for document expiration
function initExpiryCountdown() {
    const expiryElements = document.querySelectorAll('[data-expiry-timestamp]');
    
    expiryElements.forEach(element => {
        const timestamp = parseInt(element.dataset.expiryTimestamp);
        
        function updateCountdown() {
            const now = Math.floor(Date.now() / 1000);
            const timeLeft = timestamp - now;
            
            if (timeLeft <= 0) {
                element.innerHTML = '<span class="badge bg-danger">Expired</span>';
                return;
            }
            
            const days = Math.floor(timeLeft / 86400);
            const hours = Math.floor((timeLeft % 86400) / 3600);
            const minutes = Math.floor((timeLeft % 3600) / 60);
            
            element.innerHTML = `<span class="badge bg-success">Valid: ${days}d ${hours}h ${minutes}m</span>`;
        }
        
        updateCountdown();
        setInterval(updateCountdown, 60000); // Update every minute
    });
}

// Copy text to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Show toast or feedback
        const toast = document.getElementById('copyToast');
        const toastInstance = new bootstrap.Toast(toast);
        toastInstance.show();
    });
}

// Initialize tooltips
function initTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
}

// Contract status visualization
function initStatusVisualization() {
    const statusElement = document.getElementById('complianceStatus');
    if (statusElement) {
        const status = statusElement.dataset.status;
        
        if (status === 'compliant') {
            const canvas = document.getElementById('statusVisual');
            if (canvas) {
                const ctx = canvas.getContext('2d');
                
                // Draw compliance seal
                ctx.beginPath();
                ctx.arc(75, 75, 50, 0, Math.PI * 2);
                ctx.fillStyle = '#198754';
                ctx.fill();
                
                ctx.beginPath();
                ctx.arc(75, 75, 40, 0, Math.PI * 2);
                ctx.fillStyle = 'white';
                ctx.fill();
                
                ctx.beginPath();
                ctx.arc(75, 75, 30, 0, Math.PI * 2);
                ctx.fillStyle = '#198754';
                ctx.fill();
                
                ctx.font = '15px Arial';
                ctx.fillStyle = 'white';
                ctx.textAlign = 'center';
                ctx.fillText('VERIFIED', 75, 80);
            }
        }
    }
}

// Document preview function
function previewDocument(url) {
    const previewContainer = document.getElementById('documentPreview');
    const previewFrame = document.getElementById('previewFrame');
    
    previewFrame.src = url;
    previewContainer.style.display = 'block';
    
    // Scroll to preview
    previewContainer.scrollIntoView({ behavior: 'smooth' });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initTooltips();
    initExpiryCountdown();
    initStatusVisualization();
    
    // Initialize any toast elements
    const toastElList = document.querySelectorAll('.toast')
    const toastList = [...toastElList].map(toastEl => new bootstrap.Toast(toastEl))
});
