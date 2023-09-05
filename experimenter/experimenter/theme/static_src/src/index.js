import Alpine from "alpinejs";

Alpine.data("sidebar", () => ({
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

Alpine.data('slider', (id) => ({
  tab: 1,
  tabs: [],

  init() {
    this.tabs = [...this.$el.querySelectorAll('nav[role=tablist] a[role=tab]')];
    this.changeSlide();
  },

  changeSlide() {
    const activeTab = this.tabs[this.tab];
    activeTab.classList.add('active');

    this.tabs.forEach((tab, index) => {
      tab.addEventListener('click', (e) => {
        e.preventDefault();
        this.tab = index;

        this.tabs.forEach((tab, tabIndex) => {
          if (tabIndex === index) {
            tab.classList.add('active');
          } else {
            tab.classList.remove('active');
          }
        });
      });
    });
  }
}));

window.Alpine = Alpine;

Alpine.start();
