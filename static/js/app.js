/**
 * SupportDesk - Client-Side Interactive Logic
 * Vanilla JavaScript (No jQuery / Bootstrap dependencies)
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Sidebar Toggle
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.querySelector('.sidebar');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });

    // Close when clicking outside on mobile
    document.addEventListener('click', (e) => {
      if (window.innerWidth <= 992) {
        if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target) && sidebar.classList.contains('open')) {
          sidebar.classList.remove('open');
        }
      }
    });
  }

  // 2. Alert Dismissal
  const alertCloseButtons = document.querySelectorAll('.alert-close');
  alertCloseButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const alert = btn.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 250);
      }
    });
  });

  // Auto dismiss success alerts after 5 seconds
  const autoDismissAlerts = document.querySelectorAll('.alert-success');
  autoDismissAlerts.forEach(alert => {
    setTimeout(() => {
      if (alert && alert.parentElement) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 250);
      }
    }, 5000);
  });

  // 3. Auto-submit filter forms on select change
  const autoFilterSelects = document.querySelectorAll('.auto-filter');
  autoFilterSelects.forEach(select => {
    select.addEventListener('change', () => {
      const form = select.closest('form');
      if (form) {
        form.submit();
      }
    });
  });

  // 4. Copy Ticket ID helper
  const copyButtons = document.querySelectorAll('[data-copy-text]');
  copyButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const text = btn.getAttribute('data-copy-text');
      if (navigator.clipboard && text) {
        navigator.clipboard.writeText(text).then(() => {
          const originalTitle = btn.textContent;
          btn.textContent = 'Copied!';
          setTimeout(() => {
            btn.textContent = originalTitle;
          }, 1500);
        });
      }
    });
  });

  // 5. Destructive Action Confirmation
  const deleteForms = document.querySelectorAll('form[data-confirm]');
  deleteForms.forEach(form => {
    form.addEventListener('submit', (e) => {
      const message = form.getAttribute('data-confirm') || 'Are you sure you want to perform this action?';
      if (!confirm(message)) {
        e.preventDefault();
      }
    });
  });
});
