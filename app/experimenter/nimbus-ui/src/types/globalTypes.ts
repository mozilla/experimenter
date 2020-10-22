/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

/**
 * An enumeration.
 */
export enum NimbusExperimentApplication {
  FENIX = "FENIX",
  FIREFOX_DESKTOP = "FIREFOX_DESKTOP",
  REFERENCE_BROWSER = "REFERENCE_BROWSER",
}

export interface CreateExperimentInput {
  clientMutationId?: string | null;
  name: string;
  slug?: string | null;
  application: string;
  publicDescription?: string | null;
  hypothesis: string;
}

//==============================================================
// END Enums and Input Objects
//==============================================================
