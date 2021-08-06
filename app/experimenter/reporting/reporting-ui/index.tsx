import React from "react";
import ReactDOM from "react-dom";

import App from "experimenter-reporting/components/App";

const applicationRoot = document.querySelector(
    '[data-react-dom-render="reporting"]',
);

if (applicationRoot) {
    ReactDOM.render(<App />, applicationRoot);
}