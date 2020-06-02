import React from "react";
import ReactDOM from "react-dom";

import App from "experimenter-rapid/components/App";

const applicationRoot = document.querySelector(
  '[data-react-dom-render="rapid"]',
);

if (applicationRoot) {
  ReactDOM.render(<App />, applicationRoot);
}
