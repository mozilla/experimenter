import React from "react";

import ExperimentEditHeader from "experimenter-rapid/components/experiments/ExperimentEditHeader";
import ExperimentForm from "experimenter-rapid/components/forms/ExperimentForm";
import ExperimentProvider from "experimenter-rapid/contexts/experiment/provider";

const ExperimentFormPage: React.FC = () => {
  return (
    <ExperimentProvider>
      <ExperimentEditHeader />

      <ExperimentForm />
    </ExperimentProvider>
  );
};

export default ExperimentFormPage;
