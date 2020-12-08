/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { gql } from "@apollo/client";

export const GET_CONFIG_QUERY = gql`
  query getConfig {
    nimbusConfig {
      application {
        label
        value
      }
      applicationChannels {
        label
        channels
      }
      channels {
        label
        value
      }
      featureConfig {
        id
        name
        slug
        description
        application
        ownerEmail
        schema
      }
      firefoxMinVersion {
        label
        value
      }
      probeSets {
        id
        name
        slug
        probes {
          id
          kind
          name
          eventCategory
          eventMethod
          eventObject
          eventValue
        }
      }
      targetingConfigSlug {
        label
        value
      }
      hypothesisDefault
    }
  }
`;
