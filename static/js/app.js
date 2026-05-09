/**
 * NETSIBLE — Global JavaScript
 * Sidebar toggle, search, flash message auto-dismiss
 */
document.addEventListener('DOMContentLoaded', () => {
    // Sidebar toggle
    const hamburger = document.getElementById('hamburger-btn');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (hamburger && sidebar) {
        hamburger.addEventListener('click', () => {
            sidebar.classList.toggle('active');
            if (overlay) overlay.classList.toggle('active');
        });
    }
    if (overlay) {
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
        });
    }

    // Auto-dismiss flash messages after 4s
    document.querySelectorAll('.alert-netsible').forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 300);
        }, 4000);
    });

    // Active sidebar link
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar-nav a').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});

/**
 * Helper: fetch wrapper with JSON
 */
async function apiFetch(url, options = {}) {
    const defaults = {
        headers: { 'Content-Type': 'application/json' },
    };
    const res = await fetch(url, { ...defaults, ...options });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}
