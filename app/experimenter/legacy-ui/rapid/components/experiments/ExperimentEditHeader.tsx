import React from "react";

import { useExperimentState } from "experimenter-rapid/contexts/experiment/hooks";

const ExperimentFormPage: React.FC = () => {
  const experimentData = useExperimentState();
  let pageHeading = `Create a New A/A Experiment: ${experimentData.name}`;
  if (experimentData.slug) {
    pageHeading = `Edit Experiment: ${experimentData.name}`;
  }

  return (
    <div className="mb-4">
      <div className="d-flex align-items-center">
        <h3 className="mr-3">{pageHeading}</h3>
        <span className="badge badge-secondary mb-1">
          {experimentData.status}
        </span>
      </div>
      <p>
        Create and automatically launch an A/A CFR experiment. A/A experiments
        measure the accuracy of the tool.
      </p>
    </div>
  );
};

export default ExperimentFormPage;
