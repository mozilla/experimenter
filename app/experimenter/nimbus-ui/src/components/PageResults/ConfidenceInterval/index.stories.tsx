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
    <div className="w-25">
      <div className="w-75">
        <ConfidenceInterval
          upper={65}
          lower={45}
          range={65}
          significance={SIGNIFICANCE.POSITIVE}
        />
      </div>
    </div>
  ))
  .add("with neutral significance", () => (
    <div className="w-25">
      <div className="w-75">
        <ConfidenceInterval
          upper={65}
          lower={-45}
          range={65}
          significance={SIGNIFICANCE.NEUTRAL}
        />
      </div>
    </div>
  ))
  .add("with negative significance", () => (
    <div className="w-25">
      <div className="w-75">
        <ConfidenceInterval
          upper={-45}
          lower={-65}
          range={65}
          significance={SIGNIFICANCE.NEGATIVE}
        />
      </div>
    </div>
  ))
  .add("with small positive significance", () => (
    <div className="w-25">
      <div className="w-75">
        <ConfidenceInterval
          upper={50}
          lower={45}
          range={50}
          significance={SIGNIFICANCE.POSITIVE}
        />
      </div>
    </div>
  ))
  .add("with small neutral significance", () => (
    <div className="w-25">
      <div className="w-75">
        <ConfidenceInterval
          upper={2}
          lower={-2}
          range={2}
          significance={SIGNIFICANCE.NEUTRAL}
        />
      </div>
    </div>
  ))
  .add("with small negative significance", () => (
    <div className="w-25">
      <div className="w-75">
        <ConfidenceInterval
          upper={-45}
          lower={-50}
          range={50}
          significance={SIGNIFICANCE.NEGATIVE}
        />
      </div>
    </div>
  ))
  .add("with 3-digit total bounds", () => (
    <div className="w-25">
      <div className="w-75">
        <ConfidenceInterval
          upper={100}
          lower={-100}
          range={100}
          significance={SIGNIFICANCE.POSITIVE}
        />
      </div>
    </div>
  ))
  .add("with 3-digit total bounds", () => (
    <div className="w-25">
      <div className="w-75">
        <ConfidenceInterval
          upper={15}
          lower={9}
          range={20}
          significance={SIGNIFICANCE.POSITIVE}
        />
      </div>
    </div>
  ))
  .add("with 4-digit total bounds and small significance", () => (
    <div className="w-25">
      <div className="w-75">
        <ConfidenceInterval
          upper={9.5}
          lower={4.5}
          range={200}
          significance={SIGNIFICANCE.POSITIVE}
        />
      </div>
    </div>
  ))
  .add("with 5-digit total bounds", () => (
    <div className="w-25">
      <div className="w-75">
        <ConfidenceInterval
          upper={123}
          lower={90}
          range={123}
          significance={SIGNIFICANCE.POSITIVE}
        />
      </div>
    </div>
  ))
  .add("with 6-digit total bounds and small significance", () => (
    <div className="w-25">
      <div className="w-75">
        <ConfidenceInterval
          upper={123}
          lower={90.5}
          range={1234}
          significance={SIGNIFICANCE.POSITIVE}
        />
      </div>
    </div>
  ))
  .add("with 10-digit total bounds", () => (
    <div className="w-25">
      <div className="w-75">
        <ConfidenceInterval
          upper={9999.9}
          lower={3333.3}
          range={9999.9}
          significance={SIGNIFICANCE.POSITIVE}
        />
      </div>
    </div>
  ))
  .add("with 10-digit total bounds and small significance", () => (
    <div className="w-25">
      <div className="w-75">
        <ConfidenceInterval
          upper={1234.5}
          lower={1100.5}
          range={1234.5}
          significance={SIGNIFICANCE.POSITIVE}
        />
      </div>
    </div>
  ))
  .add("with 12-digit total bounds", () => (
    <div className="w-25">
      <div className="w-75">
        <ConfidenceInterval
          upper={64858.6}
          lower={11854.4}
          range={64858.6}
          significance={SIGNIFICANCE.POSITIVE}
        />
      </div>
    </div>
  ));
