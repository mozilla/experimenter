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
      channel {
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
        name
        slug
      }
      targetingConfigSlug {
        label
        value
      }
      hypothesisDefault
      documentationLink {
        label
        value
      }
    }
  }
`;
