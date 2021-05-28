/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Table } from "react-bootstrap";
import {
  getExperiment_experimentBySlug,
  getExperiment_experimentBySlug_referenceBranch,
  getExperiment_experimentBySlug_treatmentBranches,
} from "../../../types/getExperiment";
import { Code } from "../../Code";
import NotSet from "../../NotSet";

export const NO_BRANCHES_COPY = "No branches have been saved yet";

type Branch =
  | getExperiment_experimentBySlug_referenceBranch
  | getExperiment_experimentBySlug_treatmentBranches;

const TableTitle = ({
  branchCount,
  hasOneBranchNameSet,
}: {
  branchCount: number;
  hasOneBranchNameSet?: boolean;
}) => (
  <h2 className="h5 mb-3" data-testid="branches-section-title">
    Branches {branchCount > 0 && hasOneBranchNameSet && `(${branchCount})`}
  </h2>
);

const TableBranches = ({
  experiment,
}: {
  experiment: getExperiment_experimentBySlug;
}) => {
  const { featureConfig } = experiment;
  const hasSchema = featureConfig?.schema !== null;
  const branches = [
    experiment.referenceBranch,
    ...(experiment.treatmentBranches || []),
  ].filter((branch): branch is Branch => branch !== null);
  const savedBranches = branches.filter((branch) => branch.slug);
  const branchCount = savedBranches.length;
  const hasOneBranchNameSet = Boolean(savedBranches);

  return (
    <>
      <TableTitle {...{ branchCount, hasOneBranchNameSet }} />
      {branchCount === 0 || !hasOneBranchNameSet ? (
        <NotSet copy={NO_BRANCHES_COPY} />
      ) : (
        <>
          {savedBranches.map((branch, key) => (
            <TableBranch key={key} {...{ hasSchema, branch }} />
          ))}
        </>
      )}
    </>
  );
};

const TableBranch = ({
  hasSchema,
  branch: { name, slug, description, ratio, featureValue, featureEnabled },
}: {
  hasSchema: boolean;
  branch: Branch;
}) => {
  return (
    <Table bordered data-testid="table-branch" className="mb-4">
      <thead className="thead-light">
        <tr>
          <th colSpan={2} data-testid="branch-name">
            {name}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th className="w-33">Slug</th>
          <td data-testid="branch-slug">{slug ? slug : <NotSet />}</td>
        </tr>
        <tr>
          <th>Description</th>
          <td data-testid="branch-description">
            {description ? description : <NotSet />}
          </td>
        </tr>
        <tr>
          <th>Ratio</th>
          <td data-testid="branch-ratio">{ratio ? ratio : <NotSet />}</td>
        </tr>
        <tr>
          <th>Enabled</th>
          <td data-testid="branch-enabled">
            {featureEnabled ? "True" : "False"}
          </td>
        </tr>
        {hasSchema && featureEnabled && (
          <tr>
            <th>Value</th>
            <td data-testid="branch-featureValue">
              {featureValue ? <Code codeString={featureValue} /> : <NotSet />}
            </td>
          </tr>
        )}
      </tbody>
    </Table>
  );
};

export default TableBranches;
