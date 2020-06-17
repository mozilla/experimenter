import React from "react";

import ExperimentForm from "experimenter-rapid/components/forms/ExperimentForm";

const ExperimentFormPage: React.FC = () => {
  return (
    <div className="col pt-3">
      <div className="mb-4">
        <div className="d-flex align-items-center">
          <h3 className="mr-3">Create a New A/A Experiment</h3>
          <span className="badge badge-secondary mb-1">Draft</span>
        </div>
        <p>
          Create and automatically launch an A/A CFR experiment. A/A experiments
          measure the accuracy of the tool.
        </p>
      </div>

      <ExperimentForm />
    </div>
  );
};

export default ExperimentFormPage;
