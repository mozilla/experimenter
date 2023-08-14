import Alpine from "alpinejs";

Alpine.data("dropdown", () => ({
  open: false,

  toggle() {
    this.open = !this.open;
  },
}));

Alpine.data("redirect", () => ({
  redirectToReactRoute(slug, pageSlug) {
    window.location.href = `/nimbus/${slug}/edit/${pageSlug}`;
  },
}));

window.Alpine = Alpine;

Alpine.start();
