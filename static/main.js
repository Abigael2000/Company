document.addEventListener("DOMContentLoaded", function () {
  // --- Mobile nav toggle with smooth animation ---
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".site-header nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      nav.classList.toggle("open");
      var isOpen = nav.classList.contains("open");
      toggle.setAttribute("aria-expanded", isOpen);
      toggle.setAttribute("aria-label", isOpen ? "Fermer le menu" : "Ouvrir le menu");
      document.querySelector(".site-header").classList.toggle("menu-open", isOpen);
    });
    
    // Close nav when a link is clicked
    var navLinks = nav.querySelectorAll("a");
    navLinks.forEach(function(link) {
      link.addEventListener("click", function() {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "Ouvrir le menu");
        document.querySelector(".site-header").classList.remove("menu-open");
      });
    });
  }

  // --- Scroll-reveal animations with stagger effect ---
  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealEls.length) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry, index) {
          if (entry.isIntersecting) {
            // Add a small delay based on element position for stagger effect
            setTimeout(function() {
              entry.target.classList.add("in-view");
            }, index * 50);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15 }
    );
    revealEls.forEach(function (el) { observer.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("in-view"); });
  }

  // --- Animated stat counters with easing ---
  var counters = document.querySelectorAll("[data-count-to]");
  if ("IntersectionObserver" in window && counters.length) {
    var counterObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var el = entry.target;
          var target = parseInt(el.getAttribute("data-count-to"), 10) || 0;
          var duration = 1200;
          var start = null;

          function easeOutQuad(t) {
            return t * (2 - t);
          }

          function step(timestamp) {
            if (!start) start = timestamp;
            var progress = Math.min((timestamp - start) / duration, 1);
            var easedProgress = easeOutQuad(progress);
            el.textContent = Math.floor(easedProgress * target);
            if (progress < 1) {
              window.requestAnimationFrame(step);
            } else {
              el.textContent = target;
            }
          }
          window.requestAnimationFrame(step);
          counterObserver.unobserve(el);
        });
      },
      { threshold: 0.5 }
    );
    counters.forEach(function (el) { counterObserver.observe(el); });
  }

  // --- Header scroll effect (background change on scroll) ---
  var header = document.querySelector(".site-header");
  if (header) {
    window.addEventListener("scroll", function() {
      header.classList.toggle("is-scrolled", window.scrollY > 10);
    });
  }

  // --- Coordinated homepage service rotation ---
  var hero = document.querySelector(".home-hero");
  var heroVisual = document.querySelector(".hero-visual");
  var heroImage = document.querySelector(".hero-image-current");
  var heroNextImage = document.querySelector(".hero-image-next");
  var heroKicker = document.querySelector("#hero-service-kicker");
  var heroTitle = document.querySelector("#hero-service-title");
  var heroDescription = document.querySelector("#hero-service-description");
  if (hero && heroVisual && heroImage && heroNextImage && heroKicker && heroTitle && heroDescription) {
    var heroServices = [
      {
        kicker: "Tourisme & voyage",
        title: "Vous accompagner vers de nouvelles opportunités.",
        description: "Des solutions de voyage professionnelles, pensées pour les entreprises, les organisations et les particuliers.",
        image: "https://images.unsplash.com/photo-1761342615545-cc970eea273d"
      },
      {
        kicker: "Conseil en ressources humaines",
        title: "Construire des équipes plus fortes.",
        description: "Des solutions humaines et pratiques pour recruter, développer et accompagner vos équipes.",
        image: "https://images.unsplash.com/photo-1758519290830-5462f4924bb5"
      },
      {
        kicker: "Logistique",
        title: "Faire avancer vos opérations.",
        description: "Un appui logistique fiable pour garder vos activités et vos marchandises en mouvement.",
        image: "https://images.unsplash.com/photo-1578857371787-189d8b9eda84"
      },
      {
        kicker: "Communication",
        title: "Faire porter votre message.",
        description: "Des solutions de communication qui rapprochent votre organisation de ses publics.",
        image: "https://images.unsplash.com/photo-1653566031535-bcf33e1c2893"
      },
      {
        kicker: "Fournitures professionnelles",
        title: "Les bons outils pour chaque journée.",
        description: "Les équipements et fournitures essentiels, réunis pour soutenir le travail de vos équipes.",
        image: "https://images.unsplash.com/photo-1497366811353-6870744d04b2"
      }
    ];
    var activeHeroService = 0;
    var heroImageRequest = 0;
    var reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var heroImageWidth = window.innerWidth <= 560 ? 960 : (window.innerWidth <= 900 ? 1200 : 1600);
    var preloadedHeroServices = {};

    function getHeroImageUrl(service) {
      return service.image + "?auto=format&fit=crop&w=" + heroImageWidth + "&q=78";
    }

    function preloadHeroService(index) {
      if (preloadedHeroServices[index]) return;
      var image = new Image();
      image.fetchPriority = "low";
      image.decoding = "async";
      image.src = getHeroImageUrl(heroServices[index]);
      preloadedHeroServices[index] = image;
    }

    function rotateHeroService(index) {
      var service = heroServices[index];
      var requestId = ++heroImageRequest;
      var nextImage = new Image();
      nextImage.onload = function () {
        if (requestId !== heroImageRequest) return;
        hero.classList.add("copy-is-changing");
        window.setTimeout(function () {
          if (requestId !== heroImageRequest) return;
          heroNextImage.src = nextImage.src;
          heroNextImage.classList.remove("is-animating");
          heroVisual.classList.add("is-sliding");
          heroKicker.textContent = String(index + 1).padStart(2, "0") + " / 05 · " + service.kicker;
          heroTitle.textContent = service.title;
          heroDescription.textContent = service.description;
          activeHeroService = index;
          preloadHeroService((index + 1) % heroServices.length);
          window.setTimeout(function () {
            heroImage.src = heroNextImage.src;
            heroVisual.classList.remove("is-sliding");
            heroNextImage.removeAttribute("src");
            heroImage.classList.remove("is-animating");
            void heroImage.offsetWidth;
            heroImage.classList.add("is-animating");
            hero.classList.remove("copy-is-changing");
          }, reducedMotion ? 0 : 850);
        }, reducedMotion ? 0 : 180);
      };
      nextImage.onerror = function () {
        if (requestId !== heroImageRequest) return;
        hero.classList.remove("copy-is-changing");
        activeHeroService = index;
      };
      nextImage.src = getHeroImageUrl(service);
    }

    window.setInterval(function () {
      if (document.visibilityState !== "visible") return;
      rotateHeroService((activeHeroService + 1) % heroServices.length);
    }, 10000);
    window.setTimeout(function () {
      preloadHeroService((activeHeroService + 1) % heroServices.length);
    }, 700);
  }

  // --- Pre-fill service dropdowns from a ?service= query param ---
  var params = new URLSearchParams(window.location.search);
  var serviceParam = params.get("service");
  if (serviceParam) {
    var select = document.querySelector('select[name="service_interest"]');
    if (select) {
      for (var i = 0; i < select.options.length; i++) {
        if (select.options[i].value === serviceParam) {
          select.selectedIndex = i;
          break;
        }
      }
    }
  }

  // --- Home page expertise filter with smooth transitions ---
  var filterButtons = document.querySelectorAll(".filter-btn");
  var divisionCards = document.querySelectorAll(".home-division-card");
  if (filterButtons.length && divisionCards.length) {
    filterButtons.forEach(function (button) {
      button.addEventListener("click", function () {
        var filter = button.getAttribute("data-filter");
        filterButtons.forEach(function (item) {
          var isActive = item === button;
          item.classList.toggle("active", isActive);
          item.setAttribute("aria-selected", isActive ? "true" : "false");
        });
        
        // Fade out, filter, fade in with animation
        divisionCards.forEach(function (card, index) {
          var matches = filter === "all" || card.getAttribute("data-division") === filter;
          if (matches) {
            card.style.opacity = "0";
            card.style.pointerEvents = "none";
            card.classList.remove("is-hidden");
            setTimeout(function() {
              card.style.transition = "opacity 0.3s ease";
              card.style.opacity = "1";
              card.style.pointerEvents = "auto";
              setTimeout(function() {
                card.style.transition = "";
              }, 300);
            }, 10);
          } else {
            card.classList.add("is-hidden");
            card.style.opacity = "0";
            card.style.pointerEvents = "none";
          }
        });
      });
    });
  }

  // --- Smooth scroll for anchor links ---
  document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      var target = document.querySelector(this.getAttribute('href'));
      if (target) {
        var headerHeight = document.querySelector('.site-header').offsetHeight || 0;
        var targetPosition = target.offsetTop - headerHeight - 20;
        window.scrollTo({
          top: targetPosition,
          behavior: 'smooth'
        });
      }
    });
  });

  // --- Interactive parallax background for hero section ---
  var heroSection = document.querySelector(".home-hero");
  if (heroSection) {
    window.addEventListener("mousemove", function(e) {
      var heroElements = heroSection.querySelectorAll(".home-hero::before, .home-hero::after");
      var x = (e.clientX / window.innerWidth) * 5;
      var y = (e.clientY / window.innerHeight) * 5;
      
      // Subtle parallax effect on hero background
      heroSection.style.backgroundPosition = x + "px " + y + "px";
    });
  }

  // --- Form input focus effects ---
  var formInputs = document.querySelectorAll("input, select, textarea");
  formInputs.forEach(function(input) {
    input.addEventListener("focus", function() {
      this.style.borderColor = "var(--secondary)";
    });
    input.addEventListener("blur", function() {
      this.style.borderColor = "var(--border)";
    });
  });

  // --- Add ripple effect to buttons ---
  var buttons = document.querySelectorAll(".btn, .filter-btn, button");
  buttons.forEach(function(button) {
    button.addEventListener("click", function(e) {
      var ripple = document.createElement("span");
      var rect = button.getBoundingClientRect();
      var size = Math.max(rect.width, rect.height);
      var x = e.clientX - rect.left - size / 2;
      var y = e.clientY - rect.top - size / 2;
      
      ripple.style.position = "absolute";
      ripple.style.width = size + "px";
      ripple.style.height = size + "px";
      ripple.style.borderRadius = "50%";
      ripple.style.backgroundColor = "rgba(255, 255, 255, 0.3)";
      ripple.style.left = x + "px";
      ripple.style.top = y + "px";
      ripple.style.pointerEvents = "none";
      ripple.style.animation = "ripple 0.6s ease-out";
      
      if (button.style.position === "" || button.style.position === "static") {
        button.style.position = "relative";
        button.style.overflow = "hidden";
      }
      
      button.appendChild(ripple);
      setTimeout(function() {
        ripple.remove();
      }, 600);
    });
  });

  // --- Add ripple animation keyframes if not already present ---
  if (!document.querySelector("style[data-ripple]")) {
    var style = document.createElement("style");
    style.setAttribute("data-ripple", "true");
    style.textContent = "@keyframes ripple { to { transform: scale(4); opacity: 0; } }";
    document.head.appendChild(style);
  }

  // --- Add intersection observer for cards to add hover state on view ---
  var cards = document.querySelectorAll(".division-card, .stat-box, .testimonial-card");
  if ("IntersectionObserver" in window && cards.length) {
    var cardObserver = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.style.cursor = "pointer";
        }
      });
    });
    cards.forEach(function(card) {
      cardObserver.observe(card);
    });
  }
});
