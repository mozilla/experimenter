/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useState } from "react";
import { RouteComponentProps } from "@reach/router";
import AppLayout from "../AppLayout";
import LinkExternal from "../LinkExternal";
import FormOverview from "../FormOverview";
import { ReactComponent as DeleteIcon } from "../../images/x.svg";

import { useMutation } from "@apollo/client";
import { CREATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { CreateExperimentInput } from "../../types/globalTypes";
import { createExperiment_createExperiment as CreateExperimentResult } from "../../types/createExperiment";
import { navigate } from "@reach/router";
import { SUBMIT_ERROR } from "../../lib/constants";
import Head from "../Head";

const TRAINING_DOC_URL =
  "https://mana.mozilla.org/wiki/display/FJT/Project+Nimbus";

type PageNewProps = {} & RouteComponentProps;

const PageNew: React.FunctionComponent<PageNewProps> = () => {
  const [createExperiment, { loading }] = useMutation<
    { createExperiment: CreateExperimentResult },
    { input: CreateExperimentInput }
  >(CREATE_EXPERIMENT_MUTATION);

  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});
  const [isServerValid, setIsServerValid] = useState(true);

  const onFormCancel = useCallback(() => {
    navigate(".");
  }, []);

  const onFormSubmit = useCallback(
    async (
      { name, hypothesis, application }: Record<string, any>,
      resetForm: Function,
    ) => {
      try {
        const result = await createExperiment({
          variables: { input: { name, hypothesis, application } },
        });
        if (!result.data?.createExperiment) {
          throw new Error("Save failed, no error available");
        }
        const { message, nimbusExperiment } = result.data.createExperiment;

        if (message && message !== "success" && typeof message === "object") {
          setIsServerValid(false);
          return void setSubmitErrors(message);
        } else {
          setIsServerValid(true);
          setSubmitErrors({});
        }
        resetForm();
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
        <LinkExternal href={TRAINING_DOC_URL}>
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
