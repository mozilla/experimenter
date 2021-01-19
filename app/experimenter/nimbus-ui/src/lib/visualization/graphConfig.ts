/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */
import { FormattedAnalysisPoint } from "./types";

export const lineGraphConfig = (
  values: FormattedAnalysisPoint[],
  title: string,
) => ({
  $schema: "https://vega.github.io/schema/vega-lite/v4.json",
  width: "container",
  data: {
    values: values,
  },
  layer: [
    {
      mark: "errorband",
      encoding: {
        y: {
          field: "upper",
          type: "quantitative",
          scale: { zero: false },
          title: title,
        },
        y2: { field: "lower" },
        x: {
          field: "window_index",
          scale: {
            zero: false,
            padding: 0,
          },
          axis: {
            labelAngle: 0,
          },
          title: "Week",
        },
        color: { field: "branch", type: "nominal" },
      },
    },
    {
      mark: "line",
      encoding: {
        y: {
          field: "point",
          type: "quantitative",
        },
        x: {
          field: "window_index",
          axis: {
            labelAngle: 0,
          },
        },
        color: { field: "branch", type: "nominal" },
      },
    },
  ],
});
