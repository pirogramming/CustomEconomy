document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".answer-option").forEach((opt) => {
    opt.addEventListener("click", () => {
      const grid = opt.closest(".answers-grid");
      if (!grid) return;

      grid.querySelectorAll(".answer-option").forEach(o => o.classList.remove("selected"));
      opt.classList.add("selected");

      const radio = opt.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
    });
  });
});
