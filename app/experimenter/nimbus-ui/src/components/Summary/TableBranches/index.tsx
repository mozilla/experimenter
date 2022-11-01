/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Card } from "react-bootstrap";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Figure from "react-bootstrap/Figure";
import Row from "react-bootstrap/Row";
import Table from "react-bootstrap/Table";
import {
  getExperiment_experimentBySlug,
  getExperiment_experimentBySlug_referenceBranch,
  getExperiment_experimentBySlug_treatmentBranches,
} from "../../../types/getExperiment";
import CloneDialog, { useCloneDialog } from "../../CloneDialog";
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
  <Card.Header as="h5" data-testid="branches-section-title">
    {" "}
    Branches {branchCount > 0 && hasOneBranchNameSet && `(${branchCount})`}
  </Card.Header>
);

const TableBranches = ({
  experiment,
}: {
  experiment: getExperiment_experimentBySlug;
}) => {
  const branches = [
    experiment.referenceBranch,
    ...(experiment.treatmentBranches || []),
  ].filter((branch): branch is Branch => branch !== null);
  const savedBranches = branches.filter((branch) => branch.slug);
  const branchCount = savedBranches.length;
  const hasOneBranchNameSet = Boolean(savedBranches);

  return (
    <Card className="mt-4" border="light">
      <TableTitle {...{ branchCount, hasOneBranchNameSet }} />
      {branchCount === 0 || !hasOneBranchNameSet ? (
        <NotSet copy={NO_BRANCHES_COPY} />
      ) : (
        <Card.Body>
          {savedBranches.map((branch, key) => (
            <TableBranch key={key} {...{ experiment, branch }} />
          ))}
        </Card.Body>
      )}
    </Card>
  );
};

const TableBranch = ({
  experiment,
  branch,
}: {
  experiment: getExperiment_experimentBySlug;
  branch: Branch;
}) => {
  const {
    name,
    slug,
    description,
    ratio,
    featureValue,
    featureEnabled,
    screenshots,
  } = branch;
  const cloneDialogProps = useCloneDialog(experiment, branch);
  return (
    <Card className="mb-3" border="light" bg="light">
      <Card.Body>
        <Table data-testid="table-branch" className="table-fixed" id={slug}>
          <colgroup>
            <col className="w-25" />
            <col />
          </colgroup>
          <thead className="thead-light">
            <tr>
              <th colSpan={4} className="bg-light" data-testid="branch-name">
                <Container>
                  <Row>
                    <Col>
                      <a href={`#${slug}`}>#</a> {name}
                    </Col>
                    {!experiment.isRollout && (
                      <Col className="text-right">
                        <Button
                          data-testid="promote-rollout"
                          variant="outline-primary"
                          size="sm"
                          onClick={cloneDialogProps.onShow}
                        >
                          Promote to Rollout
                        </Button>
                        <CloneDialog {...cloneDialogProps} />
                      </Col>
                    )}
                  </Row>
                </Container>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th>Slug</th>
              <td data-testid="branch-slug">{slug ? slug : <NotSet />}</td>
              <th>Ratio</th>
              <td data-testid="branch-ratio">{ratio ? ratio : <NotSet />}</td>
            </tr>
            <tr>
              <th>Enabled</th>
              <td data-testid="branch-enabled">
                {featureEnabled ? "True" : "False"}
              </td>

              <th>Description</th>
              <td data-testid="branch-description">
                {description ? description : <NotSet />}
              </td>
            </tr>
            <tr>
              {featureEnabled && (
                <>
                  <th>Value</th>
                  <td colSpan={3} data-testid="branch-featureValue">
                    {featureValue ? (
                      <Code codeString={featureValue} />
                    ) : (
                      <NotSet />
                    )}
                  </td>
                </>
              )}
            </tr>
            {screenshots && screenshots.length > 0 && (
              <tr>
                <th>Screenshots</th>
                <td colSpan={3} data-testid="branch-screenshots">
                  {screenshots.map((screenshot, idx) => (
                    <Figure
                      data-testid="branch-screenshot"
                      className="d-block"
                      key={idx}
                    >
                      <Figure.Caption>{screenshot.description}</Figure.Caption>
                      {screenshot.image ? (
                        <Figure.Image
                          fluid
                          src={screenshot.image}
                          alt={screenshot.description || ""}
                        />
                      ) : (
                        <NotSet />
                      )}
                    </Figure>
                  ))}
                </td>
              </tr>
            )}
          </tbody>
        </Table>
      </Card.Body>
    </Card>
  );
};

export default TableBranches;
