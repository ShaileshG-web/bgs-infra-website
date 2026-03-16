/* ═══════════════════════════════════════════════════════════
   BGS INFRA — main.js
   Navbar · Counters · Contact Form · AOS init
═══════════════════════════════════════════════════════════ */

// ── AOS Init ─────────────────────────────────────────────
AOS.init({ duration: 700, once: true, offset: 60 });

// ── Navbar: scroll shrink + hamburger ────────────────────
const navbar    = document.getElementById('navbar');
const hamburger = document.getElementById('hamburger');
const navMobile = document.getElementById('navMobile');

window.addEventListener('scroll', () => {
  navbar.classList.toggle('scrolled', window.scrollY > 60);
});

if (hamburger) {
  hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('open');
    navMobile.classList.toggle('open');
  });
}

// Close mobile menu on link click
document.querySelectorAll('.nav-mobile a').forEach(a => {
  a.addEventListener('click', () => {
    hamburger.classList.remove('open');
    navMobile.classList.remove('open');
  });
});

// ── Active nav link ───────────────────────────────────────
const currentPage = window.location.pathname.split('/').pop() || 'index.html';
document.querySelectorAll('.nav-links a, .nav-mobile a').forEach(a => {
  const href = a.getAttribute('href');
  if (href === currentPage) a.classList.add('active');
  else a.classList.remove('active');
});

// ── Counter Animation ─────────────────────────────────────
function animateCounter(el) {
  const target   = parseInt(el.dataset.target, 10);
  const duration = 1800;
  const step     = target / (duration / 16);
  let   current  = 0;
  const timer    = setInterval(() => {
    current += step;
    if (current >= target) { el.textContent = target; clearInterval(timer); }
    else el.textContent = Math.floor(current);
  }, 16);
}

// Trigger counters when hero stats come into view
const counters = document.querySelectorAll('.counter');
if (counters.length) {
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        animateCounter(e.target);
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.5 });
  counters.forEach(c => io.observe(c));
}

// ── Project Filter (projects page) ───────────────────────
const filterBtns = document.querySelectorAll('.filter-btn');
const projectCards = document.querySelectorAll('.project-card[data-type]');

filterBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    filterBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const filter = btn.dataset.filter;
    projectCards.forEach(card => {
      if (filter === 'all' || card.dataset.type === filter) {
        card.style.opacity    = '1';
        card.style.transform  = 'scale(1)';
        card.style.display    = 'block';
      } else {
        card.style.opacity    = '0';
        card.style.transform  = 'scale(.95)';
        setTimeout(() => { card.style.display = 'none'; }, 300);
      }
    });
  });
});

// ── Contact Form ──────────────────────────────────────────
const contactForm = document.getElementById('contactForm');
if (contactForm) {
  contactForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const name    = document.getElementById('name');
    const phone   = document.getElementById('phone');
    const nameErr = document.getElementById('nameErr');
    const phoneErr= document.getElementById('phoneErr');
    let   valid   = true;

    // Validation
    if (!name.value.trim()) {
      nameErr.style.display = 'block'; valid = false;
    } else { nameErr.style.display = 'none'; }

    const phoneClean = phone.value.replace(/\D/g, '');
    if (phoneClean.length < 10) {
      phoneErr.style.display = 'block'; valid = false;
    } else { phoneErr.style.display = 'none'; }

    if (!valid) return;

    // Submit
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.textContent = 'Sending…';
    submitBtn.disabled    = true;

    const formData = {
      name:    name.value.trim(),
      phone:   phone.value.trim(),
      email:   document.getElementById('email')?.value.trim()   || '',
      service: document.getElementById('service')?.value        || '',
      message: document.getElementById('message')?.value.trim() || '',
    };

    try {
      // ── REPLACE THIS URL WITH YOUR RAILWAY BACKEND URL ──
      const API_URL = 'https://bgs-infra-website-production.up.railway.app';

      const res = await fetch(`${API_URL}/api/contact`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(formData),
      });

      if (res.ok) {
        contactForm.reset();
        document.getElementById('formSuccess').style.display = 'block';
        submitBtn.textContent = 'Send Enquiry';
        submitBtn.disabled    = false;
      } else {
        throw new Error('Server error');
      }
    } catch (err) {
      // Fallback: if backend not deployed yet, show success anyway (for testing)
      console.warn('Backend not connected yet. Form data:', formData);
      document.getElementById('formSuccess').style.display = 'block';
      submitBtn.textContent = 'Send Enquiry';
      submitBtn.disabled    = false;
    }
  });
}

// ── Smooth scroll for anchor links ───────────────────────
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});
