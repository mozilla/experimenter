import React from "react";
import { Link } from "react-router-dom";

import {
  featureOptions,
  audienceOptions,
} from "../forms/ExperimentFormOptions";
import { XSelect } from "experimenter-rapid/components/forms/XSelect";
import { useExperimentState } from "experimenter-rapid/contexts/experiment/hooks";

const LabelledRow: React.FC<{ label: string; value?: string }> = ({
  children,
  label,
  value,
}) => {
  return (
    <div className="row my-3">
      <label className="col-2 d-inline-block pt-2 font-weight-bold">
        {label}
      </label>
      <span className="col-10">
        <input
          readOnly
          className="w-100"
          hidden={value ? false : true}
          type="text"
          value={value || ""}
        />
        {children}
      </span>
    </div>
  );
};

const convertOptionValueToLabel = (values, options) => {
  return options.filter((element) => values.includes(element.value));
};

const ExperimentDetails: React.FC = () => {
  const data = useExperimentState();

  const handleClickRequestApproval = () => {
    // No-op
  };

  return (
    <>
      <LabelledRow label="Experiment Owner" value={data.owner} />
      <LabelledRow label="Public Name" value={data.name}>
        <div className="my-2">
          Bugzilla ticket can be found <a href="#">here</a>.
        </div>
      </LabelledRow>
      <LabelledRow label="Hypothesis" value={data.objectives} />
      <LabelledRow label="Feature">
        <XSelect
          isMulti
          isDisabled={true}
          options={featureOptions}
          value={
            data.features
              ? convertOptionValueToLabel(data.features, featureOptions)
              : null
          }
        />
      </LabelledRow>
      <LabelledRow label="Audience">
        <XSelect
          isDisabled={true}
          options={audienceOptions}
          value={
            data.audience
              ? convertOptionValueToLabel(data.audience, audienceOptions)
              : null
          }
        />
      </LabelledRow>
      <LabelledRow label="Trigger" />
      <LabelledRow label="Firefox Version" />

      <h3 className="my-4">Results</h3>
      <p>
        The results will be available 7 days after the experiment is launched.
        An email will be sent to you once we start recording data.
      </p>
      <p>
        The results can be found here: <a href="#">(link here)</a>
      </p>

      <div className="d-flex mt-4">
        <span>
          <Link className="btn btn-secondary" to={`/${data.slug}/edit/`}>
            Back
          </Link>
        </span>

        <span className="flex-grow-1 text-right">
          <button
            className="btn btn-primary"
            type="button"
            onClick={handleClickRequestApproval}
          >
            Request Approval
          </button>
        </span>
      </div>
    </>
  );
};

export default ExperimentDetails;
