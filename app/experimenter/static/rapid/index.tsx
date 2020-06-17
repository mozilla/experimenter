import React from "react";
import ReactDOM from "react-dom";
import { BrowserRouter } from "react-router-dom";

import App from "experimenter-rapid/components/App";

const applicationRoot = document.querySelector(
  '[data-react-dom-render="rapid"]',
);

if (applicationRoot) {
  ReactDOM.render(
    <BrowserRouter basename="/experiments/rapid">
      <App />
    </BrowserRouter>,
    applicationRoot,
  );
}
