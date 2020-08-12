import App from "./App.svelte";
import "@graph-paper/core/style.css";
import "prismjs/themes/prism.css";

let app;
window.initSvelte = (target) => {
	if (!app) {
		app = new App({target});
	}
	return app;
};

export default app;
