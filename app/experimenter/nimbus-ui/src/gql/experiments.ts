/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { gql } from "@apollo/client";

export const CREATE_EXPERIMENT_MUTATION = gql`
  mutation createExperiment($input: CreateExperimentInput!) {
    createExperiment(input: $input) {
      clientMutationId
      message
      status
      nimbusExperiment {
        name
        slug
        hypothesis
        application
      }
    }
  }
`;

export const UPDATE_EXPERIMENT_OVERVIEW_MUTATION = gql`
  mutation updateExperimentOverview($input: UpdateExperimentInput!) {
    updateExperimentOverview(input: $input) {
      clientMutationId
      message
      status
      nimbusExperiment {
        name
        hypothesis
        publicDescription
      }
    }
  }
`;

export const UPDATE_EXPERIMENT_STATUS_MUTATION = gql`
  mutation updateExperimentStatus($input: UpdateExperimentStatusInput!) {
    updateExperimentStatus(input: $input) {
      clientMutationId
      message
      status
      nimbusExperiment {
        status
      }
    }
  }
`;

export const UPDATE_EXPERIMENT_BRANCHES_MUTATION = gql`
  mutation updateExperimentBranches($input: UpdateExperimentBranchesInput!) {
    updateExperimentBranches(input: $input) {
      clientMutationId
      message
      status
      nimbusExperiment {
        id
        featureConfig {
          name
        }
        referenceBranch {
          name
          description
          ratio
        }
        treatmentBranches {
          name
          description
          ratio
        }
      }
    }
  }
`;

export const UPDATE_EXPERIMENT_PROBESETS_MUTATION = gql`
  mutation updateExperimentProbeSets($input: UpdateExperimentProbeSetsInput!) {
    updateExperimentProbeSets(input: $input) {
      clientMutationId
      nimbusExperiment {
        id
        primaryProbeSets {
          id
          name
        }
        secondaryProbeSets {
          id
          name
        }
      }
      message
      status
    }
  }
`;

export const UPDATE_EXPERIMENT_AUDIENCE_MUTATION = gql`
  mutation updateExperimentAudience($input: UpdateExperimentAudienceInput!) {
    updateExperimentAudience(input: $input) {
      clientMutationId
      message
      status
      nimbusExperiment {
        id
        totalEnrolledClients
        channel
        firefoxMinVersion
        populationPercent
        proposedDuration
        proposedEnrollment
        targetingConfigSlug
      }
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
      monitoringDashboardUrl

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

      primaryProbeSets {
        id
        slug
        name
      }

      secondaryProbeSets {
        id
        slug
        name
      }

      channel
      firefoxMinVersion
      targetingConfigSlug

      populationPercent
      totalEnrolledClients
      proposedEnrollment
      proposedDuration

      readyForReview {
        ready
        message
      }

      startDate
      endDate
    }
  }
`;

// TODO: Only the first 50 until we add pagination.
export const GET_EXPERIMENTS_QUERY = gql`
  query getAllExperiments {
    experiments(limit: 50) {
      name
      owner {
        username
      }
      slug
      startDate
      proposedDuration
      proposedEnrollment
      endDate
      status
      monitoringDashboardUrl
      featureConfig {
        slug
        name
      }
    }
  }
`;
