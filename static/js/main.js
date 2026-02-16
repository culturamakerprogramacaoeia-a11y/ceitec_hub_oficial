// CEITEC HUB - Interatividade Premium gege1

document.addEventListener('DOMContentLoaded', () => {
    initMenu();
    initAlerts();
});

function initMenu() {
    const toggle = document.getElementById('menuToggle');
    const menu = document.getElementById('navMenu');

    if (toggle) {
        toggle.addEventListener('click', () => {
            menu.classList.toggle('active');
        });
    }

    // Suporte para dropdown no mobile
    const dropdowns = document.querySelectorAll('.dropdown');
    dropdowns.forEach(dd => {
        const btn = dd.querySelector('.dropbtn');
        if (btn) {
            btn.addEventListener('click', (e) => {
                if (window.innerWidth <= 768) {
                    e.preventDefault();
                    dd.classList.toggle('active');
                }
            });
        }
    });
}

function initAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(50px)';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
}

// Utilitário para formatar números
function formatScore(num) {
    return new Intl.NumberFormat('pt-BR').format(num);
}

// Filtro de Galeria (Robótica)
function filterGallery(category) {
    const items = document.querySelectorAll('.project-item');
    items.forEach(item => {
        if (category === 'all' || item.dataset.category === category) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}
