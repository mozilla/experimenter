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

export const GET_EXPERIMENT_QUERY = gql`
  query getExperiment($slug: String!) {
    experimentBySlug(slug: $slug) {
      id
      isArchived
      canEdit
      canArchive
      name
      slug
      status
      statusNext
      publishStatus
      monitoringDashboardUrl
      resultsReady

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
      computedEnrollmentDays
      computedDurationDays

      riskMitigationLink
      riskRevenue
      riskBrand
      riskPartnerRelated

      signoffRecommendations {
        qaSignoff
        vpSignoff
        legalSignoff
      }

      documentationLinks {
        title
        link
      }

      isEnrollmentPausePending
      isEnrollmentPaused
      enrollmentEndDate

      canReview
      reviewRequest {
        changedOn
        changedBy {
          email
        }
      }
      rejection {
        message
        oldStatus
        oldStatusNext
        changedOn
        changedBy {
          email
        }
      }
      timeout {
        changedOn
        changedBy {
          email
        }
      }
      recipeJson
      reviewUrl

      locales {
        id
        name
      }
      countries {
        id
        name
      }
    }
  }
`;

export const GET_EXPERIMENTS_QUERY = gql`
  query getAllExperiments {
    experiments {
      isArchived
      name
      owner {
        username
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
      slug
      application
      firefoxMinVersion
      startDate
      isEnrollmentPausePending
      isEnrollmentPaused
      proposedDuration
      proposedEnrollment
      computedEndDate
      status
      statusNext
      publishStatus
      monitoringDashboardUrl
      resultsReady
      featureConfig {
        slug
        name
      }
    }
  }
`;
