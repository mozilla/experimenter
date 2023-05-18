/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useState } from "react";
import { Accordion, Card } from "react-bootstrap";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Figure from "react-bootstrap/Figure";
import Row from "react-bootstrap/Row";
import Table from "react-bootstrap/Table";
import CloneDialog, { useCloneDialog } from "src/components/CloneDialog";
import { Code } from "src/components/Code";
import NotSet from "src/components/NotSet";
import { useConfig } from "src/hooks";
import { ReactComponent as CollapseMinus } from "src/images/minus.svg";
import { ReactComponent as ExpandPlus } from "src/images/plus.svg";
import {
  getExperiment_experimentBySlug,
  getExperiment_experimentBySlug_referenceBranch,
  getExperiment_experimentBySlug_treatmentBranches,
} from "src/types/getExperiment";

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

  const [expandL10n, setExpandL10n] = useState(false);

  const truncatedLocalizations =
    experiment.localizations && experiment.localizations.length > 30
      ? `${experiment.localizations.substring(0, 30)}\n    ...`
      : experiment.localizations ?? "";

  return (
    <Card className="mt-4 border-left-0 border-right-0 border-bottom-0">
      <TableTitle {...{ branchCount, hasOneBranchNameSet }} />
      {branchCount === 0 || !hasOneBranchNameSet ? (
        <NotSet copy={NO_BRANCHES_COPY} />
      ) : (
        <>
          <Card.Body className="pt-0">
            {savedBranches.map((branch, key) => (
              <>
                <TableBranch key={key} {...{ experiment, branch }} />
                <hr
                  className="m-0"
                  style={{
                    background: "#e9ecef",
                    color: "#e9ecef",
                    borderColor: "#e9ecef",
                    height: "2px",
                  }}
                />
              </>
            ))}

            {experiment.isLocalized && (
              <Table data-testid="table-localizations" className="table-fixed">
                <tbody>
                  <tr id="localizations">
                    <th>
                      Localization Substitutions{" "}
                      <a href={`#localizations`}>#</a>
                    </th>
                    <td colSpan={3} data-testid="experiment-localizations">
                      <Accordion>
                        <Accordion.Toggle
                          as={Accordion}
                          eventKey="0"
                          onClick={() => setExpandL10n(!expandL10n)}
                        >
                          {expandL10n ? (
                            <>
                              <div className="float-right">
                                <Button
                                  size="sm"
                                  variant="outline-primary"
                                  data-testid="experiment-localizations-hide"
                                >
                                  <CollapseMinus />
                                  Hide
                                </Button>
                              </div>
                            </>
                          ) : (
                            <>
                              <div className="float-right">
                                <Button
                                  size="sm"
                                  variant="outline-primary"
                                  data-testid="experiment-localizations-show-more"
                                >
                                  <ExpandPlus />
                                  Show More
                                </Button>
                              </div>
                              <Code codeString={truncatedLocalizations} />
                            </>
                          )}
                        </Accordion.Toggle>

                        <Accordion.Collapse eventKey="0">
                          <Code codeString={experiment.localizations ?? ""} />
                        </Accordion.Collapse>
                      </Accordion>
                    </td>
                  </tr>
                </tbody>
              </Table>
            )}
          </Card.Body>
        </>
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
  const { allFeatureConfigs } = useConfig();
  const { name, slug, description, ratio, featureValues, screenshots } = branch;
  const cloneDialogProps = useCloneDialog(experiment, branch);
  const featureSlugs = Object.fromEntries(
    (featureValues ?? []).map((featureValue) => {
      const featureConfigId = featureValue?.featureConfig?.id;

      return [
        featureConfigId,
        allFeatureConfigs?.find((feature) => feature?.id === featureConfigId)
          ?.slug,
      ];
    }),
  );
  return (
    <Table data-testid="table-branch" className="table-fixed " id={slug}>
      <thead>
        <tr>
          <th className="border-top-0" colSpan={4} data-testid="branch-name">
            <Row>
              <Col as="h6">
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
          <th>Description</th>
          <td data-testid="branch-description">
            {description ? description : <NotSet />}
          </td>
        </tr>
        {featureValues ? (
          featureValues.map((featureValue, idx) => (
            <tr key={idx}>
              <th>{featureSlugs[featureValue!.featureConfig!.id!]} Value</th>
              <td colSpan={3} data-testid="branch-featureValue">
                {featureValue ? (
                  <Code codeString={featureValue.value!} />
                ) : (
                  <NotSet />
                )}
              </td>
            </tr>
          ))
        ) : (
          <></>
        )}

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
  );
};

export default TableBranches;
