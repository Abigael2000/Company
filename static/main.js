document.addEventListener("DOMContentLoaded", function () {
  // --- 1. Mobile Nav Toggle ---
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.querySelector(".site-header nav");
  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", nav.classList.contains("open"));
    });
    nav.querySelectorAll("a").forEach(link => {
      link.addEventListener("click", () => {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  // --- 2. Scroll-Reveal Animations (Staggered) ---
  const revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealEls.length) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry, index) => {
          if (entry.isIntersecting) {
            setTimeout(() => entry.target.classList.add("in-view"), index * 80);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -50px 0px" }
    );
    revealEls.forEach(el => observer.observe(el));
  } else {
    revealEls.forEach(el => el.classList.add("in-view"));
  }

  // --- 3. Animated Stat Counters ---
  const counters = document.querySelectorAll("[data-count-to]");
  if ("IntersectionObserver" in window && counters.length) {
    const counterObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;
          const el = entry.target;
          const target = parseInt(el.getAttribute("data-count-to"), 10) || 0;
          const duration = 1500;
          let start = null;

          const easeOutQuad = t => t * (2 - t);
          const step = timestamp => {
            if (!start) start = timestamp;
            const progress = Math.min((timestamp - start) / duration, 1);
            el.textContent = Math.floor(easeOutQuad(progress) * target);
            if (progress < 1) window.requestAnimationFrame(step);
            else el.textContent = target;
          };
          window.requestAnimationFrame(step);
          counterObserver.unobserve(el);
        });
      },
      { threshold: 0.5 }
    );
    counters.forEach(el => counterObserver.observe(el));
  }

  // --- 4. Header Scroll Shadow ---
  const header = document.querySelector(".site-header");
  if (header) {
    window.addEventListener("scroll", () => {
      header.style.boxShadow = window.scrollY > 20 
        ? "0 10px 30px rgba(0, 0, 0, 0.08)" 
        : "0 1px 2px 0 rgb(0 0 0 / 0.05)";
    });
  }

  // --- 5. Smooth Expertise Filtering (No Layout Shift) ---
  const filterButtons = document.querySelectorAll(".filter-btn");
  const divisionCards = document.querySelectorAll(".home-division-card");
  
  if (filterButtons.length && divisionCards.length) {
    filterButtons.forEach(button => {
      button.addEventListener("click", () => {
        const filter = button.getAttribute("data-filter");
        
        // Update active button state
        filterButtons.forEach(btn => {
          btn.classList.remove("active");
          btn.setAttribute("aria-selected", "false");
        });
        button.classList.add("active");
        button.setAttribute("aria-selected", "true");

        // Animate cards
        divisionCards.forEach(card => {
          const matches = filter === "all" || card.getAttribute("data-division") === filter;
          
          if (matches) {
            card.classList.remove("is-hidden", "fade-out");
            // Force reflow to restart animation
            void card.offsetWidth; 
            card.classList.add("fade-in");
          } else {
            card.classList.remove("fade-in");
            card.classList.add("fade-out");
            setTimeout(() => {
              if (!card.classList.contains("fade-in")) {
                card.classList.add("is-hidden");
                card.classList.remove("fade-out");
              }
            }, 300); // Matches CSS transition duration
          }
        });
      });
    });
  }

  // --- 6. 3D Tilt Micro-Interaction on Division Cards ---
  const tiltCards = document.querySelectorAll(".home-division-card");
  tiltCards.forEach(card => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      
      const rotateX = ((y - centerY) / centerY) * -4; // Max 4deg tilt
      const rotateY = ((x - centerX) / centerX) * 4;

      card.style.transform = `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-8px)`;
    });

    card.addEventListener("mouseleave", () => {
      card.style.transform = "perspective(800px) rotateX(0) rotateY(0) translateY(0)";
      card.style.transition = "transform 0.4s ease, box-shadow 0.3s ease, border-color 0.3s ease";
    });
    
    card.addEventListener("mouseenter", () => {
      card.style.transition = "none"; // Remove transition for instant follow on mousemove
    });
  });

  // --- 7. Smooth Scroll for Anchor Links ---
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        const headerHeight = document.querySelector('.site-header')?.offsetHeight || 0;
        window.scrollTo({
          top: target.offsetTop - headerHeight - 20,
          behavior: 'smooth'
        });
      }
    });
  });

  // --- 8. Subtle Ripple Effect on Primary Buttons Only ---
  const primaryButtons = document.querySelectorAll(".btn-primary, .btn-devis");
  primaryButtons.forEach(button => {
    button.addEventListener("click", function(e) {
      const ripple = document.createElement("span");
      const rect = button.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const x = e.clientX - rect.left - size / 2;
      const y = e.clientY - rect.top - size / 2;
      
      ripple.style.cssText = `
        position: absolute; width: ${size}px; height: ${size}px;
        border-radius: 50%; background: rgba(255, 255, 255, 0.3);
        left: ${x}px; top: ${y}px; pointer-events: none;
        transform: scale(0); animation: ripple 0.6s ease-out;
      `;
      
      if (getComputedStyle(button).position === "static") {
        button.style.position = "relative";
        button.style.overflow = "hidden";
      }
      
      button.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  });

  // Inject ripple keyframes if not present
  if (!document.querySelector("style[data-ripple]")) {
    const style = document.createElement("style");
    style.setAttribute("data-ripple", "true");
    style.textContent = "@keyframes ripple { to { transform: scale(4); opacity: 0; } }";
    document.head.appendChild(style);
  }
});