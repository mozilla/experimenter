/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { navigate } from "@reach/router";
import React, { useState } from "react";
import { Alert, Button, Card, Table } from "react-bootstrap";
import NotSet from "src/components/NotSet";
import RichText from "src/components/RichText";
import { displayConfigLabelOrNotSet } from "src/components/Summary";
import { UPDATE_EXPERIMENT_MUTATION } from "src/gql/experiments";
import { useCommonForm, useConfig, useOutcomes } from "src/hooks";
import { ReactComponent as CollapseMinus } from "src/images/minus.svg";
import { ReactComponent as ExpandPlus } from "src/images/plus.svg";
import { CHANGELOG_MESSAGES, SUBMIT_ERROR } from "src/lib/constants";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";
import {
  updateExperiment,
  updateExperimentVariables,
} from "src/types/updateExperiment";

type TableOverviewProps = {
  experiment: getExperiment_experimentBySlug;
};

interface DocSlugs {
  [key: string]: string;
}

export type SubscriberParams = {
  email: string;
  subscribed: boolean;
};

// `<tr>`s showing optional fields that are not set are not displayed.
const TableOverview = ({ experiment }: TableOverviewProps) => {
  const { applications, user } = useConfig();
  const { primaryOutcomes, secondaryOutcomes } = useOutcomes(experiment);

  const [subscribed, setSubscribed] = useState<boolean>(
    experiment.subscribers.find((s) => s.email === user) ? true : false,
  );
  const [isServerValid, setIsServerValid] = useState(true);
  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});

  const defaultValues: SubscriberParams = {
    email: user,
    subscribed: subscribed,
  };

  const { handleSubmit } = useCommonForm<keyof SubscriberParams>(
    defaultValues,
    isServerValid,
    submitErrors,
    setSubmitErrors,
  );

  const [updateExperiment] = useMutation<
    updateExperiment,
    updateExperimentVariables
  >(UPDATE_EXPERIMENT_MUTATION);

  const onSave = async () => {
    setIsServerValid(true);
    setSubmitErrors({});
    try {
      const result = await updateExperiment({
        variables: {
          input: {
            id: experiment.id,
            subscribers: [
              {
                email: user,
                subscribed: !subscribed,
              },
            ],
            changelogMessage: CHANGELOG_MESSAGES.UPDATE_SUBSCRIBERS,
          },
        },
      });

      // istanbul ignore next - can't figure out how to trigger this in a test
      if (!result.data?.updateExperiment) {
        throw new Error(SUBMIT_ERROR);
      }

      const { message } = result.data.updateExperiment;
      if (message && message !== "success" && typeof message === "object") {
        setIsServerValid(false);
        return void setSubmitErrors(message);
      } else {
        await navigate(0);
        setSubscribed(!subscribed);
      }
    } catch (error) {
      setSubmitErrors({ "*": SUBMIT_ERROR });
    }
  };

  const handleSave = handleSubmit(onSave);

  const docSlugs: DocSlugs = {
    DESKTOP: "firefox_desktop",
    FENIX: "fenix",
    IOS: "firefox_ios",
  };

  const primaryOutcomeWithLinks =
    primaryOutcomes.length > 0 &&
    primaryOutcomes
      .map((outcome, index) => (
        <a
          key={index}
          target="_blank"
          data-testid={`primary-outcome-${outcome?.slug}`}
          href={`https://mozilla.github.io/metric-hub/outcomes/${
            docSlugs[outcome?.application ?? ""]
          }/${outcome?.slug}`}
          rel="noreferrer"
        >
          {outcome?.friendlyName}
        </a>
      ))
      .reduce((acc, curr) => (
        <>
          {acc}, {curr}
        </>
      ));

  const secondaryOutcomeWithLinks =
    secondaryOutcomes.length > 0 &&
    secondaryOutcomes
      .map((outcome, index) => (
        <a
          key={index}
          target="_blank"
          data-testid={`secondary-outcome-${outcome?.slug}`}
          href={`https://mozilla.github.io/metric-hub/outcomes/${
            docSlugs[outcome?.application ?? ""]
          }/${outcome?.slug}`}
          rel="noreferrer"
        >
          {outcome?.friendlyName}
        </a>
      ))
      .reduce((acc, curr) => (
        <>
          {acc}, {curr}
        </>
      ));

  return (
    <Card className="my-4 border-left-0 border-right-0 border-bottom-0">
      <Card.Header as="h5">Overview</Card.Header>
      <Card.Body>
        <Table data-testid="table-overview">
          <tbody>
            <tr>
              <th className="border-top-0">Slug</th>
              <td
                data-testid="experiment-slug"
                className="text-monospace border-top-0"
              >
                {experiment.slug}
              </td>

              <th className="border-top-0">Experiment owner</th>
              <td data-testid="experiment-owner" className="border-top-0">
                {experiment.owner ? experiment.owner.email : <NotSet />}
              </td>
            </tr>
            <tr>
              <th>Application</th>
              <td data-testid="experiment-application">
                {displayConfigLabelOrNotSet(
                  experiment.application,
                  applications,
                )}
              </td>
              <th>Public description</th>
              <td data-testid="experiment-description">
                {experiment.publicDescription ? (
                  experiment.publicDescription
                ) : (
                  <NotSet />
                )}
              </td>
            </tr>
            <tr>
              <th>Feature config</th>
              <td data-testid="experiment-feature-config">
                {experiment.featureConfigs?.length ? (
                  experiment.featureConfigs.map((f, idx) => (
                    <React.Fragment key={f?.id || idx}>
                      <p>
                        {f?.name}
                        {f?.description?.length ? `- ${f.description}` : ""}
                      </p>
                    </React.Fragment>
                  ))
                ) : (
                  <NotSet />
                )}
              </td>

              <th>Advanced Targeting</th>
              <td data-testid="experiment-targeting-config">
                {experiment.targetingConfig?.length ? (
                  experiment.targetingConfig.map((t) => (
                    <p key={t?.label}>{`${t?.label} - ${t?.description}`}</p>
                  ))
                ) : (
                  <NotSet />
                )}
              </td>
            </tr>
            <tr>
              <th>Hypothesis</th>
              <td colSpan={3} data-testid="experiment-hypothesis">
                <RichText text={experiment.hypothesis || ""} />
              </td>
            </tr>

            {primaryOutcomes.length > 0 && (
              <tr>
                <th>Primary outcomes</th>
                <td colSpan={3} data-testid="experiment-outcome-primary">
                  {primaryOutcomeWithLinks}
                </td>
              </tr>
            )}
            {secondaryOutcomes.length > 0 && (
              <tr>
                <th>Secondary outcomes</th>
                <td colSpan={3} data-testid="experiment-outcome-secondary">
                  {secondaryOutcomeWithLinks}
                </td>
              </tr>
            )}

            <tr>
              <th>Team Projects</th>
              <td data-testid="experiment-team-projects">
                {experiment.projects!.length > 0 ? (
                  <ul className="list-unstyled mb-0">
                    {experiment.projects!.map((l) => (
                      <li key={l!.id}>{l!.name}</li>
                    ))}
                  </ul>
                ) : (
                  <NotSet />
                )}
              </td>
              <th>Subscribers</th>
              <td data-testid="experiment-subscribers">
                {experiment.subscribers!.length > 0 ? (
                  <ul className="list-unstyled mb-0">
                    {experiment.subscribers!.map((subscriber) => (
                      <li data-testid="subscriber" key={subscriber!.email}>
                        {subscriber!.email}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <NotSet />
                )}
                {!experiment.isArchived && (
                  <td className="ml-0 pl-0 border-top-0">
                    <Button
                      size="sm"
                      variant="outline-primary"
                      data-testid="add-subscriber-button"
                      onClick={handleSave}
                    >
                      {subscribed ? (
                        <div>
                          <CollapseMinus />
                          Unsubscribe
                        </div>
                      ) : (
                        <div>
                          <ExpandPlus />
                          Subscribe
                        </div>
                      )}
                    </Button>
                  </td>
                )}
                {submitErrors["*"] && (
                  <Alert data-testid="submit-error" variant="warning">
                    {submitErrors["*"]}
                  </Alert>
                )}
                {submitErrors["subscribers"] && (
                  <Alert data-testid="submit-error" variant="warning">
                    {submitErrors["subscribers"]}
                  </Alert>
                )}
              </td>
            </tr>
          </tbody>
        </Table>
      </Card.Body>
    </Card>
  );
};

export default TableOverview;
