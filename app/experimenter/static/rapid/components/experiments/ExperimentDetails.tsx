import React from "react";
import { Link } from "react-router-dom";

import {
  featureOptions,
  audienceOptions,
} from "experimenter-rapid/components/forms/ExperimentFormOptions";
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
        <input readOnly className="w-100" type="text" value={value || ""} />
        {children}
      </span>
    </div>
  );
};

const displaySelectOptionLabels = (options, values) => {
  let selectedValue = values;
  if (!Array.isArray(values)) {
    selectedValue = [values];
  }

  const selectedOption = options.reduce((filtered, element) => {
    if (selectedValue.includes(element.value)) {
      filtered.push(element.label);
    }

    return filtered;
  }, []);
  return selectedOption.join(", ");
};

const ExperimentDetails: React.FC = () => {
  const data = useExperimentState();

  const handleClickRequestApproval = () => {
    // No-op
  };

  let bugzilla_url;
  if (data.bugzilla_url) {
    bugzilla_url = (
      <div className="my-2">
        Bugzilla ticket can be found{" "}
        <a href={data.bugzilla_url ? data.bugzilla_url : "#"}>here</a>.
      </div>
    );
  }
  return (
    <>
      <LabelledRow label="Experiment Owner" value={data.owner} />
      <LabelledRow label="Public Name" value={data.name}>
        {bugzilla_url}
      </LabelledRow>
      <LabelledRow label="Hypothesis" value={data.objectives} />
      <LabelledRow
        label="Feature"
        value={displaySelectOptionLabels(featureOptions, data.features)}
      />
      <LabelledRow
        label="Audience"
        value={displaySelectOptionLabels(audienceOptions, data.audience)}
      />
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
