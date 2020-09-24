import App from "./App.svelte";
import "@graph-paper/core/style.css";
import "prismjs/themes/prism.css";

let app;
window.initSvelte = (target, data) => {
  if (!app) {
    app = new App({
      target,
      props: {
        experimentData: data,
      },
    });
  }
  return app;
};

export default app;
