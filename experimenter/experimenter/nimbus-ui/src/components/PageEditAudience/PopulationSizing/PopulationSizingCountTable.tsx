/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";

type PopulationSizingCountTableProps = {
  percent: number;
  count: number;
};

const PopulationSizingCountTable = ({
  percent,
  count,
}: PopulationSizingCountTableProps) => (
  <table className="table-visualization-center-no-border">
    <tbody>
      <tr>
        <td className="text-right">
          <span className="text-secondary">Percent of clients: </span>
        </td>
        <td className="text-left">
          <b>{percent.toFixed(2)}%</b>
          <span className="text-secondary"> (per branch)</span>
        </td>
      </tr>
      <tr>
        <td className="text-right">
          <span className="text-secondary">Expected number of clients: </span>
        </td>
        <td className="text-left">
          <b>{count.toFixed(2)}</b>
          <span className="text-secondary"> (per branch)</span>
        </td>
      </tr>
    </tbody>
  </table>
);

export default React.memo(PopulationSizingCountTable);
