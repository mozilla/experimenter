/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { SizingRecipe } from "@mozilla/nimbus-schemas";
import React from "react";
import { Form } from "react-bootstrap";
import { Code } from "src/components/Code";
import TooltipWithMarkdown from "src/components/PageResults/TooltipWithMarkdown";
import { ReactComponent as Info } from "src/images/info.svg";

type PopulationSizingNoDataProps = {
  availableTargets: SizingRecipe[];
  applicationName: string;
};

const popSizingNoDataMarkdown =
  "Pre-computed sizing is computed for limited targets using the [auto-sizing](https://experimenter.info/auto-sizing-cli/) tool.";

const PopulationSizingNoData = ({
  availableTargets,
  applicationName,
}: PopulationSizingNoDataProps) => {
  return (
    <>
      <Form.Label
        as="h5"
        className="d-flex align-items-center"
        data-testid="population-sizing-nodata"
      >
        Pre-computed population sizing data Not Available
        <Info
          data-tip
          data-for="auto-sizing-nodata-help"
          width="20"
          height="20"
          className="ml-1"
        />
        <TooltipWithMarkdown
          tooltipId="auto-sizing-nodata-help"
          markdown={popSizingNoDataMarkdown}
        />
      </Form.Label>
      <hr />
      <p className="text-secondary" data-testid="population-sizing-nodata-info">
        Pre-computed sizing information is available for certain targeting
        criteria. See below for target combinations with sizing available for
        the current application (<strong>{applicationName}</strong>):
      </p>
      <p data-testid="population-sizing-nodata-targets">
        {availableTargets.length > 0 ? (
          availableTargets.map((target) => (
            <Code
              codeString={JSON.stringify(target, (k, v) =>
                k === "new_or_existing" || k === "app_id" || v === null
                  ? undefined
                  : v,
              )}
              key={JSON.stringify(target)}
            />
          ))
        ) : (
          <Code codeString="No pre-computed sizing available for this application." />
        )}
      </p>
    </>
  );
};

export default React.memo(PopulationSizingNoData);
