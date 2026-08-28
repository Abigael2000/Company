document.addEventListener("DOMContentLoaded", function () {
  // --- Mobile nav toggle ---
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".site-header nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", nav.classList.contains("open"));
    });
  }

  // --- Scroll-reveal animations ---
  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealEls.length) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("in-view");
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

  // --- Animated stat counters ---
  var counters = document.querySelectorAll("[data-count-to]");
  if ("IntersectionObserver" in window && counters.length) {
    var counterObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var el = entry.target;
          var target = parseInt(el.getAttribute("data-count-to"), 10) || 0;
          var duration = 900;
          var start = null;

          function step(timestamp) {
            if (!start) start = timestamp;
            var progress = Math.min((timestamp - start) / duration, 1);
            el.textContent = Math.floor(progress * target);
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

  // --- Home page expertise filter ---
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
        divisionCards.forEach(function (card) {
          var matches = filter === "all" || card.getAttribute("data-division") === filter;
          card.classList.toggle("is-hidden", !matches);
        });
      });
    });
  }
});
