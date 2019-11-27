import bootstrap from "bootstrap";
import bsSelect from "bootstrap-select";
import jQuery from "jquery";
import popper from "popper.js";
import React from "react";
import ReactDOM from "react-dom";

import DesignForm from "experimenter/components/DesignForm";

window.jQuery = jQuery;
window.$ = jQuery;
window.bsSelect = bsSelect;
window.bootstrap = bootstrap;
window.popper = popper;

const branchesDiv = document.getElementById("react-branches-form");

if (branchesDiv) {
  const experimentType = branchesDiv.dataset.experimentType;
  const isBranchedAddon = branchesDiv.dataset.isBranchedAddon === "True";
  const isMultiPref = branchesDiv.dataset.isMultiPref.toLowerCase() === "true";
  const slug = branchesDiv.dataset.experimentSlug;

  ReactDOM.render(
    <DesignForm
      experimentType={experimentType}
      isBranchedAddon={isBranchedAddon}
      isMultiPref={isMultiPref}
      slug={slug}
    />,
    branchesDiv,
  );
}
