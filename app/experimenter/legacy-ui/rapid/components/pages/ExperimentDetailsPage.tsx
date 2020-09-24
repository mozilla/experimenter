import React from "react";

import ExperimentDetails from "experimenter-rapid/components/experiments/ExperimentDetails";
import ExperimentProvider from "experimenter-rapid/contexts/experiment/provider";

const ExperimentDetailsPage: React.FC = () => {
  return (
    <ExperimentProvider>
      <ExperimentDetails />
    </ExperimentProvider>
  );
};

export default ExperimentDetailsPage;
