/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { navigate, RouteComponentProps } from "@reach/router";
import React, { useCallback, useState } from "react";
import AppLayout from "src/components/AppLayout";
import FormOverview from "src/components/FormOverview";
import Head from "src/components/Head";
import LinkExternal from "src/components/LinkExternal";
import { CREATE_EXPERIMENT_MUTATION } from "src/gql/experiments";
import { ReactComponent as DeleteIcon } from "src/images/x.svg";
import {
  CHANGELOG_MESSAGES,
  EXTERNAL_URLS,
  SAVE_FAILED_NO_ERROR,
  SUBMIT_ERROR,
} from "src/lib/constants";
import { createExperiment_createExperiment as CreateExperimentResult } from "src/types/createExperiment";
import { ExperimentInput } from "src/types/globalTypes";

type PageNewProps = Record<string, any> & RouteComponentProps;

const PageNew: React.FunctionComponent<PageNewProps> = () => {
  const [createExperiment, { loading }] = useMutation<
    { createExperiment: CreateExperimentResult },
    { input: ExperimentInput }
  >(CREATE_EXPERIMENT_MUTATION);

  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});
  const [isServerValid, setIsServerValid] = useState(true);

  const onFormCancel = useCallback(() => {
    navigate(".");
  }, []);

  const onFormSubmit = useCallback(
    async ({ name, hypothesis, application }: Record<string, any>) => {
      try {
        const result = await createExperiment({
          variables: {
            input: {
              name,
              hypothesis,
              application,
              changelogMessage: CHANGELOG_MESSAGES.CREATED_EXPERIMENT,
            },
          },
        });
        if (!result.data?.createExperiment) {
          throw new Error(SAVE_FAILED_NO_ERROR);
        }
        const { message, nimbusExperiment } = result.data.createExperiment;

        if (message && message !== "success" && typeof message === "object") {
          setIsServerValid(false);
          return void setSubmitErrors(message);
        } else {
          setIsServerValid(true);
          setSubmitErrors({});
        }
        navigate(`${nimbusExperiment!.slug}/edit/overview`);
      } catch (error) {
        setSubmitErrors({ "*": `${SUBMIT_ERROR}` });
      }
    },
    [createExperiment],
  );

  return (
    <AppLayout testid="PageNew">
      <Head title="New Experiment" />

      <div className="d-flex justify-content-between">
        <h1 className="h2">Create a new Experiment</h1>
        <button title="Cancel" className="btn pr-0" onClick={onFormCancel}>
          <DeleteIcon width="18" height="18" />{" "}
        </button>
      </div>

      <p>
        Before launching an experiment, review the{" "}
        <LinkExternal href={EXTERNAL_URLS.TRAINING_AND_PLANNING_DOC}>
          training and planning documentation
        </LinkExternal>
        .
      </p>
      <section>
        <FormOverview
          {...{
            isLoading: loading,
            isServerValid,
            submitErrors,
            setSubmitErrors,
            onSubmit: onFormSubmit,
            onCancel: onFormCancel,
          }}
        />
      </section>
    </AppLayout>
  );
};

export default PageNew;
