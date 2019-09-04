import jQuery from "jquery";
import bootstrap from "bootstrap";
import bsSelect from "bootstrap-select";
import popper from "popper.js";
import React from "react";
import ReactDOM from "react-dom";

import DesignForm from "./design-page";

const branchesDiv = document.getElementById("react-branches-form");
const slug = branchesDiv.dataset.experimentSlug;
const expType = branchesDiv.dataset.experimentType

window.jQuery = jQuery;
window.$ = jQuery;


ReactDOM.render(<DesignForm slug={slug} expType={expType}/>, branchesDiv);
