/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import ConfidenceInterval from ".";
import { SIGNIFICANCE } from "../../../lib/visualization/constants";

storiesOf("pages/Results/ConfidenceInterval", module)
  .addDecorator(withLinks)
  .add("with positive significance", () => (
    <ConfidenceInterval
      upper={65}
      lower={45}
      range={65}
      significance={SIGNIFICANCE.POSITIVE}
    />
  ))
  .add("with neutral significance", () => (
    <ConfidenceInterval
      upper={65}
      lower={-45}
      range={65}
      significance={SIGNIFICANCE.NEUTRAL}
    />
  ))
  .add("with negative significance", () => (
    <ConfidenceInterval
      upper={-45}
      lower={-65}
      range={65}
      significance={SIGNIFICANCE.NEGATIVE}
    />
  ))
  .add("with small positive significance", () => (
    <ConfidenceInterval
      upper={50}
      lower={45}
      range={50}
      significance={SIGNIFICANCE.POSITIVE}
    />
  ))
  .add("with small neutral significance", () => (
    <ConfidenceInterval
      upper={2}
      lower={-2}
      range={2}
      significance={SIGNIFICANCE.NEUTRAL}
    />
  ))
  .add("with small negative significance", () => (
    <ConfidenceInterval
      upper={-45}
      lower={-50}
      range={50}
      significance={SIGNIFICANCE.NEGATIVE}
    />
  ));
