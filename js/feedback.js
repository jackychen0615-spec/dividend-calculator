(() => {
  const overlay = document.querySelector(".feedback-overlay");
  if (!overlay) return;

  const openBtn = document.querySelector(".feedback-btn");
  const cancelBtn = overlay.querySelector(".feedback-cancel");
  const submitBtn = overlay.querySelector(".feedback-submit");
  const stars = overlay.querySelectorAll(".feedback-stars button");
  const textarea = overlay.querySelector("textarea");
  const form = overlay.querySelector(".feedback-modal");
  const thanks = overlay.querySelector(".feedback-thanks");

  let rating = 0;

  const closeBtn = overlay.querySelector(".feedback-close");

  openBtn.addEventListener("click", () => overlay.classList.add("open"));

  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      overlay.classList.remove("open");
      resetForm();
    });
  }

  cancelBtn.addEventListener("click", () => {
    overlay.classList.remove("open");
    resetForm();
  });

  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) {
      overlay.classList.remove("open");
      resetForm();
    }
  });

  stars.forEach((star, i) => {
    star.addEventListener("click", () => {
      rating = i + 1;
      stars.forEach((s, j) => s.classList.toggle("active", j < rating));
    });
    star.addEventListener("mouseenter", () => {
      stars.forEach((s, j) => s.classList.toggle("active", j <= i));
    });
  });

  const starsContainer = overlay.querySelector(".feedback-stars");
  starsContainer.addEventListener("mouseleave", () => {
    stars.forEach((s, j) => s.classList.toggle("active", j < rating));
  });

  submitBtn.addEventListener("click", () => {
    if (rating === 0) return;

    const page = document.title;
    const message = textarea.value.trim();

    const url = "https://script.google.com/macros/s/AKfycbyvDaLq8FKcVh7f-vZT7A1aIiFVzf0kZYNSNi8jpNGGvTlLoh2At5V8FsC8BwarUWvE2A/exec";
    const payload = JSON.stringify({
      rating: rating,
      page: page,
      message: message || "(無留言)",
    });
    navigator.sendBeacon(url, new Blob([payload], { type: "text/plain" }));

    // Hide form content, show thanks with close button
    form.querySelectorAll("h3, .feedback-stars, textarea, .feedback-actions").forEach(
      (el) => (el.style.display = "none")
    );
    thanks.style.display = "block";
  });

  function resetForm() {
    rating = 0;
    stars.forEach((s) => s.classList.remove("active"));
    textarea.value = "";
    // Restore form content
    form.querySelectorAll("h3, .feedback-stars, textarea, .feedback-actions").forEach(
      (el) => (el.style.display = "")
    );
    thanks.style.display = "none";
  }
})();
