const navToggle = document.querySelector("[data-nav-toggle]");
const navLinks = document.querySelector("[data-nav-links]");

if (navToggle && navLinks) {
  navToggle.addEventListener("click", () => navLinks.classList.toggle("open"));
}

const observer = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      }
    }
  },
  { threshold: 0.12 },
);

document.querySelectorAll(".fade-in").forEach((element) => observer.observe(element));

document.querySelectorAll("[data-copy]").forEach((button) => {
  button.addEventListener("click", async () => {
    const target = document.querySelector(button.dataset.copy);
    if (!target) return;
    await navigator.clipboard.writeText(target.innerText.trim());
    const original = button.innerText;
    button.innerText = "Copied";
    window.setTimeout(() => {
      button.innerText = original;
    }, 1200);
  });
});
