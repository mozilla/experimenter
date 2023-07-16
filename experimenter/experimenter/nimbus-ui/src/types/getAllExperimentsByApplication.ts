/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { NimbusExperimentApplicationEnum } from "./globalTypes";

// ====================================================
// GraphQL query operation: getAllExperimentsByApplication
// ====================================================

export interface getAllExperimentsByApplication_experimentsByApplication {
  id: number;
  name: string;
  slug: string;
  publicDescription: string | null;
}

export interface getAllExperimentsByApplication {
  /**
   * List Nimbus Experiments by application.
   */
  experimentsByApplication: getAllExperimentsByApplication_experimentsByApplication[];
}

export interface getAllExperimentsByApplicationVariables {
  application: NimbusExperimentApplicationEnum;
}
