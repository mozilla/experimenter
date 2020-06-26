import React from "react";

import ExperimentDetails from "experimenter-rapid/components/experiments/ExperimentDetails";
import ExperimentProvider from "experimenter-rapid/contexts/experiment/provider";

const ExperimentDetailsPage: React.FC = () => {
  return (
    <ExperimentProvider>
      <div className="col pt-3">
        <div className="mb-4">
          <div className="d-flex align-items-center">
            <h3 className="mr-3">Experiment Summary</h3>
            <span className="badge badge-secondary mb-1">Draft</span>
          </div>

          <ExperimentDetails />
        </div>
      </div>
    </ExperimentProvider>
  );
};

export default ExperimentDetailsPage;
