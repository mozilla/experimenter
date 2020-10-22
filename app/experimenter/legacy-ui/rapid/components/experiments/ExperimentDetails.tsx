import React from "react";
import { Link } from "react-router-dom";

import useInterval from "experimenter-rapid/components/experiments/useInterval";
import { displaySelectOptionLabels } from "experimenter-rapid/components/experiments/utils";
import {
  featureOptions,
  audienceOptions,
  firefoxVersionOptions,
  firefoxChannelOptions,
} from "experimenter-rapid/components/forms/ExperimentFormOptions";
import HighlightsTable from "experimenter-rapid/components/visualization/HighlightsTable";
import Overview from "experimenter-rapid/components/visualization/Overview";
import ResultsTable from "experimenter-rapid/components/visualization/ResultsTable";
import {
  requestReview,
  fetchExperiment,
} from "experimenter-rapid/contexts/experiment/actions";
import {
  useExperimentState,
  useExperimentDispatch,
} from "experimenter-rapid/contexts/experiment/hooks";
import { ExperimentStatus } from "experimenter-rapid/types/experiment";

export const POLL_TIMEOUT = 30000;

declare global {
  interface Window {
    initSvelte(svelteRoot: HTMLElement | null): void;
  }
}

const LabelledRow: React.FC<{ label: string; value?: string }> = ({
  children,
  label,
  value,
}) => {
  return (
    <tr>
      <th style={{ whiteSpace: "nowrap", width: "1%" }}>{label}</th>
      <td>
        {value}
        {children}
      </td>
    </tr>
  );
};

const ExperimentDetails: React.FC = () => {
  const experimentData = useExperimentState();
  const visualizationRef = React.useRef(null);
  const dispatch = useExperimentDispatch();

  const handleClickRequestApproval = async () => dispatch(requestReview());

  React.useEffect(() => {
    if (!visualizationRef.current || !window.initSvelte) {
      return;
    }

    window.initSvelte(visualizationRef.current);
  });

  useInterval(() => {
    if (experimentData.slug) {
      dispatch(fetchExperiment(experimentData.slug));
    }
  }, POLL_TIMEOUT);

  let bugzilla_url;
  if (experimentData.bugzilla_url) {
    bugzilla_url = (
      <div>
        <small>
          Bugzilla ticket can be found{" "}
          <a
            href={experimentData.bugzilla_url}
            rel="noopener noreferrer"
            target="_blank"
          >
            here
          </a>
        </small>
      </div>
    );
  }

  let monitoring_url;
  if (experimentData.monitoring_dashboard_url) {
    monitoring_url = (
      <>
        <h4 className="my-4">Monitoring</h4>
        <p>
          The live monitoring dashboard can be found here:
          <a
            href={experimentData.monitoring_dashboard_url}
            rel="noopener noreferrer"
            target="_blank"
          >
            {" "}
            (link here)
          </a>
        </p>
      </>
    );
  }

  let analysis_report;
  if (
    [ExperimentStatus.LIVE, ExperimentStatus.COMPLETE].includes(
      experimentData.status,
    ) &&
    experimentData.recipe_slug
  ) {
    const slug_underscored = experimentData.recipe_slug.split("-").join("_");
    analysis_report = (
      <>
        <h2 className="font-weight-bold">Results</h2>
        {experimentData.analysis?.show_analysis ? (
          <div>
            <ResultsTable experimentData={experimentData} />
            <div ref={visualizationRef}></div>
          </div>
        ) : (
          <div>
            <p>
              The results will be available 7 days after the experiment is
              launched. An email will be sent to you once we start recording
              data.
            </p>
            <p>
              The results can be found{" "}
              <a
                href={`https://protosaur.dev/partybal/${slug_underscored}.html`}
                rel="noopener noreferrer"
                target="_blank"
              >
                here
              </a>
            </p>
          </div>
        )}
      </>
    );
  }

  const backButtonDisabled = ![
    ExperimentStatus.DRAFT,
    ExperimentStatus.REJECTED,
  ].includes(experimentData.status);

  let backButton = (
    <Link to={`/${experimentData.slug}/edit/`}>
      <button className="btn btn-primary">Back</button>
    </Link>
  );
  if (backButtonDisabled) {
    backButton = (
      <button disabled className="btn btn-secondary">
        Back
      </button>
    );
  }

  const requestButtonDisabled =
    experimentData.status !== ExperimentStatus.DRAFT;

  const buttonsShown = ![
    ExperimentStatus.LIVE,
    ExperimentStatus.COMPLETE,
  ].includes(experimentData.status);

  let changeStatusButtons;
  if (buttonsShown) {
    changeStatusButtons = (
      <div className="d-flex mt-4">
        <span>{backButton}</span>

        <span className="flex-grow-1 text-right">
          <button
            className={
              requestButtonDisabled ? "btn btn-secondary" : "btn btn-primary"
            }
            disabled={requestButtonDisabled}
            type="button"
            onClick={handleClickRequestApproval}
          >
            Request Approval
          </button>
        </span>
      </div>
    );
  }

  let rejectFeedback;

  if (experimentData.reject_feedback) {
    const messageDate = new Date(experimentData.reject_feedback.changed_on);
    rejectFeedback = (
      <>
        <h3 className="my-4">Review Feedback</h3>
        <div className="alert alert-secondary" role="alert">
          <p className="font-weight-bold"> {messageDate.toDateString()}</p>
          <p>Reject reason: {experimentData.reject_feedback.message}</p>
        </div>
      </>
    );
  }

  return (
    <div className="col pt-3">
      <div className="mb-4">
        <div className="mb-4">
          <h1 className="mb-0">
            {experimentData.name}{" "}
            <span className="badge badge-pill badge-small badge-secondary">
              {experimentData.status}
            </span>
          </h1>
          {experimentData.recipe_slug && (
            <p>
              <code>{experimentData.recipe_slug}</code>
            </p>
          )}
        </div>

        {!experimentData.analysis?.show_analysis && (
          <table className="table table-bordered mb-5">
            <tbody>
              <LabelledRow
                label="Experiment Owner"
                value={experimentData.owner}
              />
              <LabelledRow label="Public Name" value={experimentData.name}>
                {bugzilla_url}
              </LabelledRow>
              <LabelledRow
                label="Hypothesis"
                value={experimentData.objectives}
              />
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

              <LabelledRow
                label="Firefox Channel"
                value={displaySelectOptionLabels(
                  firefoxChannelOptions,
                  experimentData.firefox_channel,
                )}
              />
            </tbody>
          </table>
        )}

        {experimentData.analysis?.show_analysis && (
          <>
            <h2 className="font-weight-bold">Overview</h2>
            <h5 className="text-uppercase font-weight-bold mt-5">Hypothesis</h5>
            <p className="h5">{experimentData.objectives}</p>
            <HighlightsTable {...{ experimentData }} />
            <Overview {...{ experimentData }} />
          </>
        )}

        {monitoring_url}

        {analysis_report}

        {rejectFeedback}
        {changeStatusButtons}
      </div>
    </div>
  );
};

export default ExperimentDetails;
