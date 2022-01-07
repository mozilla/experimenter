/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Table } from "react-bootstrap";
import { EXTERNAL_URLS } from "../../../lib/constants";
import { getExperiment_experimentBySlug_signoffRecommendations } from "../../../types/getExperiment";
import LinkExternal from "../../LinkExternal";

type TableSignoffProps = {
  signoffRecommendations: getExperiment_experimentBySlug_signoffRecommendations | null;
};

const TableSignoff = ({ signoffRecommendations }: TableSignoffProps) => (
  <Table data-testid="table-signoff" className="mb-4 border rounded">
    <tbody>
      <tr data-testid="table-signoff-qa">
        <th className="w-25">QA Sign-off</th>
        <td>
          {signoffRecommendations?.qaSignoff && (
            <span className="text-success">Recommended: </span>
          )}
          Please file a QA request.{" "}
          <LinkExternal href={EXTERNAL_URLS.SIGNOFF_QA}>
            Learn More
          </LinkExternal>
        </td>
      </tr>
      <tr data-testid="table-signoff-vp">
        <th>VP Sign-off</th>
        <td>
          {signoffRecommendations?.vpSignoff && (
            <span className="text-success">Recommended: </span>
          )}
          Please email your VP.{" "}
          <LinkExternal href={EXTERNAL_URLS.SIGNOFF_VP}>
            Learn More
          </LinkExternal>
        </td>
      </tr>
      <tr data-testid="table-signoff-legal">
        <th>Legal Sign-off</th>
        <td>
          {signoffRecommendations?.legalSignoff && (
            <span className="text-success">Recommended: </span>
          )}
          Please email legal.{" "}
          <LinkExternal href={EXTERNAL_URLS.SIGNOFF_LEGAL}>
            Learn More
          </LinkExternal>
        </td>
      </tr>
    </tbody>
  </Table>
);

export default TableSignoff;
