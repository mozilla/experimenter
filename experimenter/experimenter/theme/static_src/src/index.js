import Alpine from "alpinejs";

Alpine.data("sidebar", () => ({
  open: false,

  toggle() {
    this.open = !this.open;
  },
}));

Alpine.data("modal", () => ({
  isModalOpen: false,
  trapCleanup: null,
  oldData: null,
  newData: null,
  
  openModal() {
    this.isModalOpen = true
    this.trapCleanup = focusTrap(document.querySelector('#modal'))
  },
  closeModal() {
    this.isModalOpen = false
    this.oldData = null;
    this.newData = null;
    this.trapCleanup()
  },
}));

Alpine.data("redirect", () => ({
  redirectToReactRoute(slug, pageSlug) {
    window.location.href = `/nimbus/${slug}/edit/${pageSlug}`;
  },
}));

Alpine.data('slider', () => ({
                
  // set initial tab
  tab: 1,
  
  // slider tabs
  tabs: [...document.querySelectorAll('nav[role=tablist] a[role=tab]')],
  
  init() {
      // initialize main function
      this.changeSlide()
  },
  
  // main function
  changeSlide() {
      let timeInterval = this.$refs.slider.dataset.interval;
      this.tabs[this.tab].setAttribute('class', 'active')
      
      // // set interval to change slide
      // let startInterval = () => {
      //     this.tab = (this.tab < this.tabs.length - 1)? this.tab + 1 : 0;
      //     this.tabs.forEach( (tab)=> {
      //         (this.tab == this.tabs.indexOf(tab)) ?  tab.setAttribute('class', 'active') : tab.removeAttribute('class') 
      //     })
      // }
      
      // // start interval to change slide
      // let slideInterval = setInterval(startInterval, timeInterval);
      
      // // mouse over slider stops slide
      // this.$refs.slider.onmouseover = () => {
      //     if (slideInterval) { 
      //         clearInterval(slideInterval)
      //         slideInterval = null;
      //     }
      // }
      
      // // mouse out slider starts again slide
      // this.$refs.slider.onmouseout = () => {
      //     if (slideInterval === null) { 
      //         slideInterval = setInterval(startInterval, timeInterval);
      //     }
      // }
      
      // slider tabs click event 
      this.tabs.forEach( (tab)=> {
          tab.addEventListener('click', (e)=> {
              e.preventDefault()
              this.tab = this.tabs.indexOf(e.target)
              this.tabs.forEach( (tab)=> {
                  (this.tab == this.tabs.indexOf(tab)) ?  tab.setAttribute('class', 'active') : tab.removeAttribute('class') 
              }) 
          })
      })
  }
}))

window.Alpine = Alpine;

Alpine.start();
