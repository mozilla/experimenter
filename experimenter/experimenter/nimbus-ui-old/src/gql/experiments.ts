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
      canPublishToPreview
      name
      slug
      status
      statusNext
      publishStatus
      monitoringDashboardUrl
      rolloutMonitoringDashboardUrl
      resultsExpectedDate
      resultsReady
      showResultsUrl
      audienceUrl

      hypothesis
      application
      publicDescription

      conclusionRecommendations
      takeawaysGainAmount
      takeawaysMetricGain
      takeawaysQbrLearning
      takeawaysSummary

      owner {
        email
      }
      subscribers {
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
        featureValues {
          featureConfig {
            id
          }
          value
        }
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
        featureValues {
          featureConfig {
            id
          }
          value
        }
        screenshots {
          id
          description
          image
        }
      }

      preventPrefConflicts

      featureConfigs {
        id
        slug
        name
        description
        application
        ownerEmail
        schema
        enabled
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
      isWeb
      excludedExperimentsBranches {
        excludedExperiment {
          id
          slug
          name
          publicDescription
          referenceBranch {
            slug
          }
          treatmentBranches {
            slug
          }
          isArchived
        }
        branchSlug
      }
      requiredExperimentsBranches {
        requiredExperiment {
          id
          slug
          name
          publicDescription
          referenceBranch {
            slug
          }
          treatmentBranches {
            slug
          }
          isArchived
        }
        branchSlug
      }
      jexlTargetingExpression

      populationPercent
      totalEnrolledClients
      proposedEnrollment
      proposedDuration
      proposedReleaseDate

      readyForReview {
        ready
        message
        warnings
      }

      startDate
      computedDurationDays
      computedEndDate
      computedEnrollmentDays
      computedEnrollmentEndDate

      riskMitigationLink
      riskRevenue
      riskBrand
      riskMessage
      riskPartnerRelated

      isLocalized
      localizations

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
        code
      }
      countries {
        id
        name
        code
      }
      languages {
        id
        name
        code
      }
      projects {
        id
        name
      }
      isRolloutDirty
      qaComment
      qaStatus
      excludedLiveDeliveries
      featureHasLiveMultifeatureExperiments
      liveExperimentsInNamespace

      legalSignoff
      qaSignoff
      vpSignoff
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
      }
      targetingConfig {
        label
        value
        description
        applicationValues
        stickyRequired
        isFirstRunRequired
      }
      slug
      application
      firefoxMinVersion
      firefoxMaxVersion
      startDate
      isRolloutDirty
      isEnrollmentPausePending
      proposedDuration
      proposedEnrollment
      computedEndDate
      computedEnrollmentEndDate
      status
      statusNext
      publishStatus
      qaStatus
      monitoringDashboardUrl
      rolloutMonitoringDashboardUrl
      resultsReady
      showResultsUrl
      channel
      populationPercent
      projects {
        id
        name
      }
      subscribers {
        username
      }
      takeawaysMetricGain
      takeawaysQbrLearning
    }
  }
`;

export const GET_ALL_EXPERIMENTS_BY_APPLICATION_QUERY = gql`
  query getAllExperimentsByApplication(
    $application: NimbusExperimentApplicationEnum!
  ) {
    experimentsByApplication(application: $application) {
      id
      name
      slug
      publicDescription
      referenceBranch {
        slug
      }
      treatmentBranches {
        slug
      }
      isArchived
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
