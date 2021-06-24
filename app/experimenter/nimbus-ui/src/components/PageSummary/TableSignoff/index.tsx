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
  <Table bordered data-testid="table-signoff" className="mb-4">
    <tbody>
      <tr data-testid="table-signoff-qa">
        <td>
          <strong>QA Sign-off</strong>
        </td>
        <td>
          {signoffRecommendations?.qaSignoff && (
            <span className="text-success">Recommended: </span>
          )}
          Please file a PI request.{" "}
          <LinkExternal href={EXTERNAL_URLS.SIGNOFF_QA}>
            Learn More
          </LinkExternal>
        </td>
      </tr>
      <tr data-testid="table-signoff-vp">
        <td>
          <strong>VP Sign-off</strong>
        </td>
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
        <td>
          <strong>Legal Sign-off</strong>
        </td>
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
