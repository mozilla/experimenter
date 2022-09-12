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
      isRollout
      isArchived
      canEdit
      canArchive
      name
      slug
      status
      statusNext
      publishStatus
      monitoringDashboardUrl
      rolloutMonitoringDashboardUrl
      resultsReady

      hypothesis
      application
      publicDescription

      conclusionRecommendation
      takeawaysSummary

      owner {
        email
      }

      parent {
        name
        slug
      }

      warnFeatureSchema

      referenceBranch {
        id
        name
        slug
        description
        ratio
        featureValue
        featureEnabled
        screenshots {
          id
          description
          image
        }
      }

      treatmentBranches {
        id
        name
        slug
        description
        ratio
        featureValue
        featureEnabled
        screenshots {
          id
          description
          image
        }
      }

      featureConfigs {
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
      firefoxMaxVersion
      targetingConfigSlug
      targetingConfig {
        label
        value
        applicationValues
        description
        stickyRequired
        isFirstRunRequired
      }
      isSticky
      isFirstRun
      jexlTargetingExpression

      populationPercent
      totalEnrolledClients
      proposedEnrollment
      proposedDuration

      readyForReview {
        ready
        message
        warnings
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
      languages {
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
      isRollout
      name
      owner {
        username
      }
      featureConfigs {
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
      firefoxMaxVersion
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
      rolloutMonitoringDashboardUrl
      resultsReady
      featureConfig {
        slug
        name
      }
      channel
      isRollout
      populationPercent
    }
  }
`;

export const CLONE_EXPERIMENT_MUTATION = gql`
  mutation cloneExperiment($input: ExperimentCloneInput!) {
    cloneExperiment(input: $input) {
      message
      nimbusExperiment {
        slug
      }
    }
  }
`;
