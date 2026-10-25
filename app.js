/**
 * FinWise AI - Core Application Scripts
 * Theme toggle, mobile sidebar, notifications, and AI Chat client
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Light / Dark Theme Management
  const themeToggleBtn = document.getElementById('theme-toggle-btn');
  const themeIcon = document.getElementById('theme-icon');

  function getStoredTheme() {
    return localStorage.getItem('finwise_theme') || 'light';
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-bs-theme', theme);
    localStorage.setItem('finwise_theme', theme);
    if (themeIcon) {
      if (theme === 'dark') {
        themeIcon.classList.remove('bi-moon-stars');
        themeIcon.classList.add('bi-sun-fill');
      } else {
        themeIcon.classList.remove('bi-sun-fill');
        themeIcon.classList.add('bi-moon-stars');
      }
    }
    // Notify charts if initialized
    if (window.onFinWiseThemeChange) {
      window.onFinWiseThemeChange(theme);
    }
  }

  // Initial theme application
  applyTheme(getStoredTheme());

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', function () {
      const current = getStoredTheme();
      const nextTheme = current === 'dark' ? 'light' : 'dark';
      applyTheme(nextTheme);
    });
  }

  // 2. Mobile Sidebar Toggle
  const sidebarToggle = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('sidebar');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function () {
      sidebar.classList.toggle('show');
    });

    // Close when clicking outside on mobile
    document.addEventListener('click', function (e) {
      if (window.innerWidth < 992 && sidebar.classList.contains('show')) {
        if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
          sidebar.classList.remove('show');
        }
      }
    });
  }

  // 3. Auto-dismiss Flash Alerts
  const flashAlerts = document.querySelectorAll('.alert-dismissible');
  flashAlerts.forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 6000);
  });

  // 4. Auto-submit Month & Year Pickers on change
  const autoMonthSelects = document.querySelectorAll('.auto-submit-period');
  autoMonthSelects.forEach(select => {
    select.addEventListener('change', function () {
      const form = this.closest('form');
      if (form) form.submit();
    });
  });

  // 5. Interactive AI Chat Handler
  const chatForm = document.getElementById('advisor-chat-form');
  const chatInput = document.getElementById('advisor-chat-input');
  const chatMessages = document.getElementById('advisor-chat-messages');

  if (chatForm && chatInput && chatMessages) {
    chatForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      const userText = chatInput.value.trim();
      if (!userText) return;

      // Append user bubble
      appendMessage(userText, 'user');
      chatInput.value = '';

      // Append loading indicator
      const loadingId = 'loading-' + Date.now();
      appendLoading(loadingId);
      chatMessages.scrollTop = chatMessages.scrollHeight;

      // Extract CSRF token
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      const year = document.getElementById('advisor-year')?.value || new Date().getFullYear();
      const month = document.getElementById('advisor-month')?.value || (new Date().getMonth() + 1);

      try {
        const response = await fetch('/advisor/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
          },
          body: JSON.stringify({ message: userText, year: parseInt(year), month: parseInt(month) })
        });

        removeLoading(loadingId);

        if (!response.ok) {
          const errData = await response.json();
          appendMessage(`Error: ${errData.error || 'Failed to get response.'}`, 'ai');
          return;
        }

        const data = await response.json();
        appendMessage(data.reply, 'ai', data.is_live_ai);
      } catch (err) {
        removeLoading(loadingId);
        appendMessage('Connection error. Please try again.', 'ai');
      }

      chatMessages.scrollTop = chatMessages.scrollHeight;
    });

    function appendMessage(text, sender, isLive = false) {
      const bubble = document.createElement('div');
      bubble.className = `chat-bubble ${sender === 'user' ? 'bubble-user' : 'bubble-ai'}`;
      
      if (sender === 'ai') {
        const badge = isLive 
          ? '<span class="badge bg-primary mb-2 d-inline-block"><i class="bi bi-stars"></i> Gemini AI</span>' 
          : '<span class="badge bg-secondary mb-2 d-inline-block"><i class="bi bi-cpu"></i> FinWise Rule Engine</span>';
        bubble.innerHTML = `${badge}<div>${formatMarkdownToHtml(text)}</div>`;
      } else {
        bubble.textContent = text;
      }
      chatMessages.appendChild(bubble);
    }

    function appendLoading(id) {
      const loadingBubble = document.createElement('div');
      loadingBubble.id = id;
      loadingBubble.className = 'chat-bubble bubble-ai text-muted';
      loadingBubble.innerHTML = '<div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>FinWise AI is analyzing your finances...';
      chatMessages.appendChild(loadingBubble);
    }

    function removeLoading(id) {
      const el = document.getElementById(id);
      if (el) el.remove();
    }

    function formatMarkdownToHtml(md) {
      // Basic safe markdown parser for chat
      return md
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n- /g, '<br>• ');
    }
  }
});
