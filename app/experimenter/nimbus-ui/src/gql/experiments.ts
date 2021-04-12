/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { gql } from "@apollo/client";

export const CREATE_EXPERIMENT_MUTATION = gql`
  mutation createExperiment($input: ExperimentInput!) {
    createExperiment(input: $input) {
      message
      nimbusExperiment {
        slug
      }
    }
  }
`;

export const UPDATE_EXPERIMENT_MUTATION = gql`
  mutation updateExperiment($input: ExperimentInput!) {
    updateExperiment(input: $input) {
      message
    }
  }
`;

export const END_EXPERIMENT_MUTATION = gql`
  mutation endExperiment($input: ExperimentIdInput!) {
    endExperiment(input: $input) {
      message
    }
  }
`;

export const GET_EXPERIMENT_QUERY = gql`
  query getExperiment($slug: String!) {
    experimentBySlug(slug: $slug) {
      id
      name
      slug
      status
      publishStatus
      monitoringDashboardUrl
      isEndRequested

      hypothesis
      application
      publicDescription

      owner {
        email
      }

      referenceBranch {
        name
        slug
        description
        ratio
        featureValue
        featureEnabled
      }
      treatmentBranches {
        name
        slug
        description
        ratio
        featureValue
        featureEnabled
      }

      featureConfig {
        id
        slug
        name
        description
        application
        ownerEmail
        schema
      }

      primaryOutcomes
      secondaryOutcomes

      channel
      firefoxMinVersion
      targetingConfigSlug
      jexlTargetingExpression

      populationPercent
      totalEnrolledClients
      proposedEnrollment
      proposedDuration

      readyForReview {
        ready
        message
      }

      startDate
      computedEndDate

      riskMitigationLink

      documentationLinks {
        title
        link
      }

      isEnrollmentPaused
      enrollmentEndDate
    }
  }
`;

export const GET_EXPERIMENTS_QUERY = gql`
  query getAllExperiments {
    experiments {
      name
      owner {
        username
      }
      slug
      startDate
      proposedDuration
      proposedEnrollment
      computedEndDate
      status
      publishStatus
      isEndRequested
      monitoringDashboardUrl
      featureConfig {
        slug
        name
      }
    }
  }
`;
