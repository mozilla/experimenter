import Alpine from 'alpinejs'

Alpine.data('dropdown', () => ({
    open: false,
 
    toggle() {
        this.open = ! this.open
    }
}))

window.Alpine = Alpine

 
Alpine.start()