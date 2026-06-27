/**
 * Global JavaScript helper methods for theme, toaster notifications, and utilities.
 */

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    setupToasterContainer();
});

/**
 * Initialize theme based on user preferences or saved value.
 */
function initTheme() {
    const savedTheme = localStorage.getItem('insightx-theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Update theme toggle icons if present
    updateThemeToggleUI(savedTheme);
    
    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('insightx-theme', newTheme);
            updateThemeToggleUI(newTheme);
            showToast(`Switched to ${newTheme} mode!`, 'info');
        });
    }
}

function updateThemeToggleUI(theme) {
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
        if (theme === 'dark') {
            themeIcon.className = 'fas fa-sun';
        } else {
            themeIcon.className = 'fas fa-moon';
        }
    }
}

/**
 * Toast Notification Setup
 */
function setupToasterContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }
}

/**
 * Display a Toast Notification
 * @param {string} message - Toast contents (supports HTML)
 * @param {string} type - 'success', 'danger', 'warning', 'info'
 * @param {number} duration - ms before hiding
 */
function showToast(message, type = 'info', duration = 3500) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `custom-toast ${type}`;
    
    let iconClass = 'fa-info-circle';
    if (type === 'success') iconClass = 'fa-check-circle';
    else if (type === 'danger') iconClass = 'fa-exclamation-circle';
    else if (type === 'warning') iconClass = 'fa-exclamation-triangle';
    
    toast.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas ${iconClass} me-3" style="font-size: 1.2rem;"></i>
            <span>${message}</span>
        </div>
        <button class="btn-close btn-close-white ms-3" style="font-size: 0.8rem; filter: invert(1);" onclick="this.parentElement.remove()"></button>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards';
        toast.addEventListener('animationend', () => {
            toast.remove();
        });
    }, duration);
}

// Add animation slideOut keyframe to styles
const styleSheet = document.createElement("style");
styleSheet.innerText = `
@keyframes slideOut {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(120%); opacity: 0; }
}
`;
document.head.appendChild(styleSheet);
