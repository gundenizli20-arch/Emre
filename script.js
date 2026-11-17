// ===== 1. Menu mobile : ouvrir / fermer =====
const boutonMenu = document.querySelector(".menu-toggle");

boutonMenu.addEventListener("click", () => {
  const ouvert = document.body.classList.toggle("menu-open");
  boutonMenu.setAttribute("aria-expanded", ouvert);
});

// Ferme le menu quand on clique sur un lien
document.querySelectorAll(".nav a").forEach((lien) => {
  lien.addEventListener("click", () => {
    document.body.classList.remove("menu-open");
    boutonMenu.setAttribute("aria-expanded", false);
  });
});

// ===== 2. Animation : les éléments apparaissent en défilant =====
const observateur = new IntersectionObserver((entrees) => {
  entrees.forEach((entree) => {
    if (entree.isIntersecting) {
      entree.target.classList.add("visible");
      observateur.unobserve(entree.target);
    }
  });
}, { threshold: 0.15 });

document.querySelectorAll(".reveal").forEach((el) => observateur.observe(el));

// ===== 3. Année automatique dans le pied de page =====
document.getElementById("annee").textContent = new Date().getFullYear();
