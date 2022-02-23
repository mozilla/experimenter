/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { gql } from "@apollo/client";

export const GET_CONFIG_QUERY = gql`
  query getConfig {
    nimbusConfig {
      applications {
        label
        value
      }
      channels {
        label
        value
      }
      conclusionRecommendations {
        label
        value
      }
      applicationConfigs {
        application
        channels {
          label
          value
        }
      }
      allFeatureConfigs {
        id
        name
        slug
        description
        application
        ownerEmail
        schema
      }
      firefoxVersions {
        label
        value
      }
      outcomes {
        friendlyName
        slug
        application
        description
        isDefault
        metrics {
          slug
          friendlyName
          description
        }
      }
      owners {
        username
      }
      targetingConfigs {
        label
        value
        applicationValues
      }
      hypothesisDefault
      documentationLink {
        label
        value
      }
      maxPrimaryOutcomes
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
