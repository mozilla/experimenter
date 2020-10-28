/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useState } from "react";
import { RouteComponentProps } from "@reach/router";
import AppLayout from "../AppLayout";
import LinkExternal from "../LinkExternal";
import FormOverview from "../FormOverview";

import { useMutation } from "@apollo/client";
import { CREATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { CreateExperimentInput } from "../../types/globalTypes";
import { createExperiment_createExperiment as CreateExperimentResult } from "../../types/createExperiment";
import { navigate } from "@reach/router";
import { SUBMIT_ERROR } from "../../lib/constants";

const TRAINING_DOC_URL =
  "https://mana.mozilla.org/wiki/display/FJT/Project+Nimbus";

type PageNewProps = {} & RouteComponentProps;

const PageNew = (props: PageNewProps) => {
  // TODO: EXP-462 Get this from constants / config loaded at app start?
  const applications = ["firefox-desktop", "fenix", "reference-browser"];

  const [createExperiment, { loading }] = useMutation<
    { createExperiment: CreateExperimentResult },
    { input: CreateExperimentInput }
  >(CREATE_EXPERIMENT_MUTATION);

  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});

  const onFormCancel = useCallback((ev: React.FormEvent) => {
    // TODO: EXP-462 cancel creation
    // navigate(".")
    console.log("CANCEL TBD");
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

        if (message !== "success" && typeof message === "object") {
          return void setSubmitErrors(message);
        }
        resetForm();
        navigate(`${nimbusExperiment!.slug}/edit/overview`);
      } catch (error) {
        setSubmitErrors({ "*": SUBMIT_ERROR });
      }
    },
    [createExperiment],
  );

  return (
    <AppLayout testid="PageNew">
      <h1 className="h2">Create a new Experiment</h1>
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
            submitErrors,
            applications,
            onSubmit: onFormSubmit,
            onCancel: onFormCancel,
          }}
        />
      </section>
    </AppLayout>
  );
};

export default PageNew;
