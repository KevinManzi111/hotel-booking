document.addEventListener('DOMContentLoaded', () => {
  const imageSelector = '.room-card-image, .detail-image img, .trip-summary > img, .booking-thumb img, .confirmation-room img';
  document.querySelectorAll(imageSelector).forEach((image) => {
    image.addEventListener('error', () => {
      const fallback = document.createElement('div');
      fallback.className = 'room-placeholder image-fallback';
      fallback.setAttribute('role', 'img');
      fallback.setAttribute('aria-label', `${image.alt || 'Room'} image unavailable`);
      fallback.innerHTML = '<i class="bi bi-image" aria-hidden="true"></i><span>Image unavailable</span>';
      image.replaceWith(fallback);
    }, { once: true });
  });

  document.querySelectorAll('form[data-confirm]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });

  document.querySelectorAll('.form-field.has-error').forEach((group) => {
    const control = group.querySelector('input, select, textarea');
    if (control) control.setAttribute('aria-invalid', 'true');
  });
  const firstInvalid = document.querySelector('.form-field.has-error input, .form-field.has-error select, .form-field.has-error textarea');
  if (firstInvalid) firstInvalid.focus();

  document.querySelectorAll('form').forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (event.defaultPrevented || !form.checkValidity()) return;
      const submitter = event.submitter || form.querySelector('button[type="submit"]');
      if (!submitter || submitter.classList.contains('dropdown-item')) return;
      submitter.classList.add('is-loading');
      submitter.setAttribute('aria-busy', 'true');
      const label = submitter.textContent.trim();
      submitter.dataset.label = label;
      submitter.innerHTML = `<span class="spinner-border spinner-border-sm" aria-hidden="true"></span><span>${label}</span>`;
    });
  });

  const checkIn = document.querySelector('input[name="check_in"]');
  const checkOut = document.querySelector('input[name="check_out"]');
  if (checkIn && checkOut) checkIn.addEventListener('change', () => {
    checkOut.min = checkIn.value;
    if (checkOut.value && checkOut.value <= checkIn.value) checkOut.value = '';
  });

  const initToasts = () => {
    const stack = document.querySelector('[data-toast-stack]');
    if (!stack || stack.dataset.initialized === 'true') return;
    stack.dataset.initialized = 'true';
    const seen = new Set();
    stack.querySelectorAll('[data-toast]').forEach((toast, index) => {
      const signature = `${toast.dataset.level}:${toast.querySelector('.toast-copy')?.textContent.trim()}`;
      if (seen.has(signature)) { toast.remove(); return; }
      seen.add(signature);
      toast.dataset.initialized = 'true';
      let timer;
      const dismiss = () => {
        if (toast.classList.contains('toast-leaving')) return;
        window.clearTimeout(timer);
        toast.classList.add('toast-leaving');
        window.setTimeout(() => {
          toast.remove();
          if (!stack.querySelector('[data-toast]')) stack.remove();
        }, 240);
      };
      toast.querySelector('[data-toast-dismiss]')?.addEventListener('click', dismiss, { once: true });
      const timeout = { success: 5500, info: 5500, warning: 10000, error: 12000 }[toast.dataset.level];
      if (timeout) timer = window.setTimeout(dismiss, timeout + index * 350);
    });
  };
  initToasts();

  const sidebar = document.querySelector('.dashboard-sidebar');
  const sidebarToggle = document.querySelector('[data-sidebar-toggle]');
  const sidebarScrim = document.querySelector('[data-sidebar-scrim]');
  const setSidebar = (open) => {
    sidebar?.classList.toggle('open', open);
    document.body.classList.toggle('sidebar-open', open);
    sidebarToggle?.setAttribute('aria-expanded', String(open));
  };
  sidebarToggle?.addEventListener('click', () => setSidebar(!sidebar?.classList.contains('open')));
  sidebarScrim?.addEventListener('click', () => setSidebar(false));

  document.querySelectorAll('.auth-slides').forEach((slides) => {
    const images = [...slides.querySelectorAll('img')];
    if (images.length < 2 || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    let current = 0;
    window.setInterval(() => {
      images[current].classList.remove('active');
      current = (current + 1) % images.length;
      images[current].classList.add('active');
    }, 6500);
  });

  document.querySelectorAll('input[type="password"]').forEach((input) => {
    const wrap = document.createElement('div');
    wrap.className = 'password-input';
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);
    const toggle = document.createElement('button');
    toggle.type = 'button'; toggle.className = 'password-toggle';
    toggle.setAttribute('aria-label', 'Show password');
    toggle.innerHTML = '<i class="bi bi-eye" aria-hidden="true"></i>';
    toggle.addEventListener('click', () => {
      const showing = input.type === 'text';
      input.type = showing ? 'password' : 'text';
      toggle.setAttribute('aria-label', showing ? 'Show password' : 'Hide password');
      toggle.innerHTML = `<i class="bi ${showing ? 'bi-eye' : 'bi-eye-slash'}" aria-hidden="true"></i>`;
    });
    wrap.appendChild(toggle);
  });

  const wizard = document.querySelector('[data-signup-wizard]');
  if (wizard) {
    const steps = [...wizard.querySelectorAll('[data-signup-step]')];
    const indicators = [...document.querySelectorAll('[data-step-indicator]')];
    let current = wizard.querySelector('[data-signup-step] .has-error')?.closest('[data-signup-step]')?.dataset.signupStep || '1';
    const showStep = (number) => {
      current = String(number);
      steps.forEach((step) => { step.hidden = step.dataset.signupStep !== current; });
      indicators.forEach((item) => {
        item.classList.toggle('active', item.dataset.stepIndicator === current);
        item.classList.toggle('complete', Number(item.dataset.stepIndicator) < Number(current));
      });
      steps.find((step) => step.dataset.signupStep === current)?.querySelector('input, button')?.focus();
    };
    const validateStep = () => {
      const step = steps.find((item) => item.dataset.signupStep === current);
      if (current === '1') wizard.querySelector('#id_password2')?.setCustomValidity('');
      const controls = [...step.querySelectorAll('input')];
      const valid = controls.every((control) => control.reportValidity());
      if (current === '1') {
        const p1 = wizard.querySelector('#id_password1'); const p2 = wizard.querySelector('#id_password2');
        if (p1?.value !== p2?.value) { p2.setCustomValidity('Passwords do not match.'); p2.reportValidity(); return false; }
        p2?.setCustomValidity('');
      }
      return valid;
    };
    wizard.querySelectorAll('[data-next-step]').forEach((button) => button.addEventListener('click', () => {
      if (!validateStep()) return;
      if (current === '2') {
        const review = wizard.querySelector('[data-signup-review]');
        review.innerHTML = [['Name', `${wizard.querySelector('#id_first_name').value} ${wizard.querySelector('#id_last_name').value}`], ['Email', wizard.querySelector('#id_email').value], ['Username', wizard.querySelector('#id_username').value]].map(([label, value]) => `<div><dt>${label}</dt><dd>${value}</dd></div>`).join('');
      }
      showStep(Number(current) + 1);
    }));
    wizard.querySelectorAll('[data-prev-step]').forEach((button) => button.addEventListener('click', () => showStep(Number(current) - 1)));
    showStep(current);

    const username = wizard.querySelector('[data-username-check]');
    const usernameStatus = wizard.querySelector('[data-username-status]');
    let usernameTimer; let lastUsername = '';
    username?.addEventListener('input', () => {
      window.clearTimeout(usernameTimer); usernameStatus.textContent = ''; usernameStatus.className = 'inline-status';
      const value = username.value.trim();
      if (value.length < 3 || value === lastUsername) return;
      usernameTimer = window.setTimeout(async () => {
        lastUsername = value; usernameStatus.classList.add('checking'); usernameStatus.textContent = 'Checking availability…';
        const data = new FormData(); data.append('username', value); data.append('csrfmiddlewaretoken', wizard.querySelector('[name="csrfmiddlewaretoken"]').value);
        try {
          const response = await fetch(wizard.dataset.usernameUrl, {method: 'POST', body: data, headers: {'X-Requested-With': 'XMLHttpRequest'}});
          const result = await response.json();
          usernameStatus.className = `inline-status ${result.available ? 'available' : 'unavailable'}`;
          usernameStatus.textContent = result.message;
        } catch (_) { usernameStatus.className = 'inline-status unavailable'; usernameStatus.textContent = 'Availability could not be checked. Registration will still validate it securely.'; }
      }, 450);
    });
    const password = wizard.querySelector('#id_password1');
    password?.addEventListener('input', () => {
      const value = password.value; let score = 0;
      if (value.length >= 8) score++; if (value.length >= 12) score++; if (/[A-Z]/.test(value) && /[a-z]/.test(value)) score++; if (/\d|[^A-Za-z]/.test(value)) score++;
      const labels = ['Too short', 'Developing', 'Good', 'Strong', 'Strong'];
      wizard.querySelector('[data-password-label]').textContent = labels[score];
      wizard.querySelector('[data-password-bar]').style.width = `${score * 25}%`;
    });
  }
});
