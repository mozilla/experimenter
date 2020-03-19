import bootstrap from "bootstrap";
import bsSelect from "bootstrap-select";
import jQuery from "jquery";
import popper from "popper.js";
import React from "react";
import ReactDOM from "react-dom";

import DesignForm from "experimenter/components/DesignForm";
import TimelinePopForm from "experimenter/components/TimelinePopForm";

window.jQuery = jQuery;
window.$ = jQuery;
window.bsSelect = bsSelect;
window.bootstrap = bootstrap;
window.popper = popper;

const branchesDiv = document.getElementById("react-branches-form");
const timelinePopDiv = document.getElementById("react-timelinepop-form");

if (branchesDiv) {
  const experimentType = branchesDiv.dataset.experimentType;
  const isBranchedAddon = branchesDiv.dataset.isBranchedAddon === "True";
  const isMultiPref = branchesDiv.dataset.isMultiPref.toLowerCase() === "true";
  const rolloutType = branchesDiv.dataset.rolloutType || "addon";
  const slug = branchesDiv.dataset.experimentSlug;

  ReactDOM.render(
    <DesignForm
      experimentType={experimentType}
      isBranchedAddon={isBranchedAddon}
      isMultiPref={isMultiPref}
      rolloutType={rolloutType}
      slug={slug}
    />,
    branchesDiv,
  );
}

if (timelinePopDiv) {
  const experimentType = timelinePopDiv.dataset.experimentType;
  const slug = timelinePopDiv.dataset.experimentSlug;
  const shouldHavePopPercent = timelinePopDiv.dataset.shouldHavePopPercent;
  const allCountries = JSON.parse(timelinePopDiv.dataset.allCountries);
  const allLocales = JSON.parse(timelinePopDiv.dataset.allLocales);
  ReactDOM.render(
    <TimelinePopForm
      experimentType={experimentType}
      slug={slug}
      shouldHavePopPercent={shouldHavePopPercent}
      allCountries={allCountries}
      allLocales={allLocales}
    />,
    timelinePopDiv,
  );
}
