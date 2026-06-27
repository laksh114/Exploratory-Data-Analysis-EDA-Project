/**
 * Dashboard operations including Plotly plotting, AJAX cleaning tools, and the NLQ Chat Engine.
 */

// Global state variables
let currentDatasetId = null;

function initDashboard(datasetId) {
    currentDatasetId = datasetId;
    setupNLQChat();
    setupCleaningActions();
}

/**
 * Plot Plotly charts dynamically
 * @param {string} elementId - ID of target div element
 * @param {string} plotJson - Plotly serialized JSON string
 */
function renderPlotlyChart(elementId, plotJson) {
    const el = document.getElementById(elementId);
    if (!el || !plotJson) return;
    
    try {
        const figure = JSON.parse(plotJson);
        
        // Make plot responsive
        figure.layout.autosize = true;
        figure.layout.useResizeHandler = true;
        
        Plotly.newPlot(elementId, figure.data, figure.layout, {
            responsive: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d']
        });
    } catch (e) {
        console.error("Plotly render error:", e);
        el.innerHTML = `<div class="text-danger p-3"><i class="fas fa-exclamation-triangle me-2"></i>Error plotting figure: ${e.message}</div>`;
    }
}

/**
 * Cleaning tab Operations
 */
function setupCleaningActions() {
    // 1. Missing Value Imputation
    const imputeForm = document.getElementById('impute-form');
    if (imputeForm) {
        imputeForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const column = document.getElementById('impute-column').value;
            const strategy = document.getElementById('impute-strategy').value;
            const fillValue = document.getElementById('impute-value').value;
            
            runCleaningRequest('/clean/impute', {
                dataset_id: currentDatasetId,
                column: column,
                strategy: strategy,
                fill_value: fillValue
            }, "Missing values filled successfully!");
        });
    }
    
    // Toggle constant value input visibility
    const imputeStrategy = document.getElementById('impute-strategy');
    if (imputeStrategy) {
        imputeStrategy.addEventListener('change', (e) => {
            const valInputGroup = document.getElementById('impute-value-group');
            if (e.target.value === 'constant') {
                valInputGroup.classList.remove('d-none');
            } else {
                valInputGroup.classList.add('d-none');
            }
        });
    }
    
    // 2. Remove Duplicates
    const dupBtn = document.getElementById('btn-remove-duplicates');
    if (dupBtn) {
        dupBtn.addEventListener('click', () => {
            if (confirm("Are you sure you want to delete all duplicate records? This action cannot be undone.")) {
                runCleaningRequest('/clean/duplicates', {
                    dataset_id: currentDatasetId
                }, "Duplicate rows removed successfully!");
            }
        });
    }
    
    // 3. Outlier Clipping/Removal
    const outlierForm = document.getElementById('outlier-form');
    if (outlierForm) {
        outlierForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const column = document.getElementById('outlier-column').value;
            const strategy = document.getElementById('outlier-strategy').value;
            
            runCleaningRequest('/clean/outliers', {
                dataset_id: currentDatasetId,
                column: column,
                strategy: strategy
            }, "Outliers processed successfully!");
        });
    }
    
    // 4. Data Type Conversion
    const typeForm = document.getElementById('type-convert-form');
    if (typeForm) {
        typeForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const column = document.getElementById('convert-column').value;
            const targetType = document.getElementById('convert-type').value;
            
            runCleaningRequest('/clean/convert-type', {
                dataset_id: currentDatasetId,
                column: column,
                target_type: targetType
            }, `Casted ${column} to ${targetType} format!`);
        });
    }
}

/**
 * Runs a POST fetch request to cleaning endpoints and reloads page on success
 */
function runCleaningRequest(url, data, successMsg) {
    // Show loading indicator
    showToast("Cleaning in progress...", "info", 1500);
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(result => {
        if (result.success) {
            showToast(successMsg, "success");
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showToast(result.error || "Failed to process cleaning task.", "danger");
        }
    })
    .catch(err => {
        console.error("AJAX Error:", err);
        showToast("Server request failed. Please try again.", "danger");
    });
}

/**
 * Natural Language Query AI chat panel logic
 */
function setupNLQChat() {
    const chatInput = document.getElementById('nlq-chat-input');
    const chatBtn = document.getElementById('nlq-chat-send');
    const chatBody = document.getElementById('nlq-chat-body');
    
    if (!chatInput || !chatBtn || !chatBody) return;
    
    const sendMessage = () => {
        const queryText = chatInput.value.trim();
        if (!queryText) return;
        
        // Append user bubble
        appendChatBubble('user', queryText);
        chatInput.value = '';
        
        // Append bot loading bubble
        const loadingId = 'bot-loading-' + Date.now();
        appendChatBubble('bot', `<i class="fas fa-spinner fa-spin"></i> Analyzing dataset...`, loadingId);
        
        // Submit to API
        fetch('/nlq', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                dataset_id: currentDatasetId,
                query: queryText
            })
        })
        .then(res => res.json())
        .then(resData => {
            const loadingBubble = document.getElementById(loadingId);
            if (loadingBubble) loadingBubble.remove();
            
            if (resData.success) {
                let answerHtml = resData.answer;
                if (resData.html_table) {
                    answerHtml += `<div class="table-responsive mt-3">${resData.html_table}</div>`;
                }
                appendChatBubble('bot', answerHtml);
            } else {
                appendChatBubble('bot', `Sorry, I encountered an issue: ${resData.answer || 'Could not parse query.'}`);
            }
        })
        .catch(err => {
            const loadingBubble = document.getElementById(loadingId);
            if (loadingBubble) loadingBubble.remove();
            appendChatBubble('bot', `Connection error: Could not contact query engine.`);
            console.error(err);
        });
    };
    
    chatBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

function appendChatBubble(sender, text, elementId = null) {
    const chatBody = document.getElementById('nlq-chat-body');
    if (!chatBody) return;
    
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;
    if (elementId) bubble.id = elementId;
    bubble.innerHTML = text;
    
    chatBody.appendChild(bubble);
    chatBody.scrollTop = chatBody.scrollHeight;
}
