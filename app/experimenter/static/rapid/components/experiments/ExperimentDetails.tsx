import React from "react";
import { Link } from "react-router-dom";

import {
  featureOptions,
  audienceOptions,
  firefoxVersionOptions,
} from "experimenter-rapid/components/forms/ExperimentFormOptions";
import { requestReview } from "experimenter-rapid/contexts/experiment/actions";
import {
  useExperimentState,
  useExperimentDispatch,
} from "experimenter-rapid/contexts/experiment/hooks";
import { ExperimentStatus } from "experimenter-rapid/types/experiment";

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
  const experimentData = useExperimentState();
  const dispatch = useExperimentDispatch();

  const handleClickRequestApproval = async () => dispatch(requestReview());

  let bugzilla_url;
  if (experimentData.bugzilla_url) {
    bugzilla_url = (
      <div className="my-2">
        Bugzilla ticket can be found{" "}
        <a
          href={experimentData.bugzilla_url}
          rel="noopener noreferrer"
          target="_blank"
        >
          here
        </a>
      </div>
    );
  }

  const buttonsDisabled = experimentData.status !== ExperimentStatus.DRAFT;
  const buttonsShown = ![
    ExperimentStatus.LIVE,
    ExperimentStatus.COMPLETE,
  ].includes(experimentData.status);

  let changeStatusButtons;
  if (buttonsShown) {
    if (buttonsDisabled) {
      changeStatusButtons = (
        <div className="d-flex mt-4">
          <span>
            <button disabled className="btn btn-secondary">
              Back
            </button>
          </span>

          <span className="flex-grow-1 text-right">
            <button disabled className="btn btn-secondary" type="button">
              Request Approval
            </button>
          </span>
        </div>
      );
    } else {
      changeStatusButtons = (
        <div className="d-flex mt-4">
          <span>
            <Link
              className="btn btn-primary"
              to={`/${experimentData.slug}/edit/`}
            >
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
      );
    }
  }

  return (
    <div className="col pt-3">
      <div className="mb-4">
        <div className="d-flex align-items-center">
          <h3 className="mr-3">Experiment Summary</h3>
          <span className="badge badge-secondary mb-1">
            {experimentData.status}
          </span>
        </div>
        <LabelledRow label="Experiment Owner" value={experimentData.owner} />
        <LabelledRow label="Public Name" value={experimentData.name}>
          {bugzilla_url}
        </LabelledRow>
        <LabelledRow label="Hypothesis" value={experimentData.objectives} />
        <LabelledRow
          label="Feature"
          value={displaySelectOptionLabels(
            featureOptions,
            experimentData.features,
          )}
        />
        <LabelledRow
          label="Audience"
          value={displaySelectOptionLabels(
            audienceOptions,
            experimentData.audience,
          )}
        />
        <LabelledRow
          label="Firefox Minimum Version"
          value={displaySelectOptionLabels(
            firefoxVersionOptions,
            experimentData.firefox_min_version,
          )}
        />

        <h3 className="my-4">Results</h3>
        <p>
          The results will be available 7 days after the experiment is launched.
          An email will be sent to you once we start recording data.
        </p>
        <p>
          The results can be found here: <a href="#">(link here)</a>
        </p>
        {changeStatusButtons}
      </div>
    </div>
  );
};

export default ExperimentDetails;
