import React from "react";
import { Button } from "react-bootstrap";
import { useHistory, useParams } from "react-router-dom";

import {
  saveExperiment,
  updateExperiment,
} from "experimenter-rapid/contexts/experiment/actions";
import {
  useExperimentDispatch,
  useExperimentState,
} from "experimenter-rapid/contexts/experiment/hooks";
import { ExperimentStatus } from "experimenter-rapid/types/experiment";

import {
  featureOptions,
  audienceOptions,
  firefoxChannelOptions,
  firefoxVersionOptions,
} from "./ExperimentFormOptions";
import { XSelect } from "./XSelect";

interface ErrorListProperties {
  errors: Array<string> | undefined;
}

const ErrorList: React.FC<ErrorListProperties> = ({ errors }) => {
  if (!errors) {
    return null;
  }

  return (
    <ul className="text-danger pl-3 my-2">
      {errors.map((e, i) => (
        <li key={i}>{e}</li>
      ))}
    </ul>
  );
};

const ExperimentForm: React.FC = () => {
  const formData = {
    ...useExperimentState(),
    ...{ status: ExperimentStatus.DRAFT },
  };

  const dispatch = useExperimentDispatch();
  const { experimentSlug } = useParams();

  const [errors, setErrors] = React.useState<{ [name: string]: Array<string> }>(
    {},
  );
  const history = useHistory();

  const handleSelectChange = (name) => {
    return (value) => {
      dispatch(updateExperiment(name, value));
    };
  };

  const handleChange = (ev) => {
    const field = ev.target;
    dispatch(updateExperiment(field.getAttribute("name"), field.value));
  };

  const handleClickSave = async () => {
    const response = await saveExperiment(experimentSlug, formData);

    const responseData = await response.json();
    if (!response.ok) {
      setErrors(responseData);
    } else {
      setErrors({});
      history.push(`/${responseData.slug}/`);
    }
  };

  return (
    <form>
      <div className="mb-4">
        <label className="font-weight-bold" htmlFor="field-name">
          Public Name
        </label>
        <p>
          Choose a name that describes the experiment you wish to run. This name
          will be public to users.
        </p>
        <input
          className="form-control w-100"
          id="field-name"
          name="name"
          type="text"
          value={formData.name}
          onChange={handleChange}
        />
        <ErrorList errors={errors.name} />
      </div>

      <div className="mb-4">
        <label className="font-weight-bold" htmlFor="field-objectives">
          Hypothesis
        </label>
        <p>
          Please describe the purpose and hypothesis of your experiment. You can
          add supporting documents here.
        </p>
        <textarea
          className="form-control w-100"
          id="field-objectives"
          name="objectives"
          rows={5}
          value={formData.objectives}
          onChange={handleChange}
        />
        <ErrorList errors={errors.objectives} />
      </div>

      <div className="mb-4">
        <label className="font-weight-bold" htmlFor="field-feature">
          Features
        </label>
        <p>
          Select the user action or feature that you&apos;d be measuring with
          this experiment.
        </p>
        <XSelect
          isMulti
          className="w-100"
          id="field-feature"
          name="features"
          options={featureOptions}
          selectValue={formData.features}
          onOptionChange={handleSelectChange("features")}
        />
        <ErrorList errors={errors.features} />
      </div>

      <div className="mb-4">
        <label className="font-weight-bold" htmlFor="field-audience">
          Audience
        </label>
        <p>Description of audience.</p>
        <XSelect
          className="w-100"
          id="field-audience"
          name="audience"
          options={audienceOptions}
          selectValue={formData.audience}
          onOptionChange={handleSelectChange("audience")}
        />
        <ErrorList errors={errors.audience} />
      </div>
      <div className="mb-4">
        <label className="font-weight-bold" htmlFor="field-firefox-min-version">
          Firefox Minimum Version
        </label>
        <p>
          Is there a minimum Firefox Release version this experiment should be
          run on?
        </p>
        <XSelect
          className="w-100"
          id="field-firefox-min-version"
          name="firefox_min_version"
          options={firefoxVersionOptions}
          selectValue={formData.firefox_min_version}
          onOptionChange={handleSelectChange("firefox_min_version")}
        />
        <ErrorList errors={errors.firefox_min_version} />
      </div>

      <div className="mb-4">
        <label className="font-weight-bold" htmlFor="field-firefox-channel">
          Firefox Channel
        </label>
        <p>What channel do you want to run this experiment on?</p>
        <XSelect
          className="w-100"
          id="field-firefox-channel"
          name="firefox_channel"
          options={firefoxChannelOptions}
          selectValue={formData.firefox_channel}
          onOptionChange={handleSelectChange("firefox_channel")}
        />
        <ErrorList errors={errors.firefox_channel} />
      </div>

      <Button onClick={handleClickSave}>Save</Button>
    </form>
  );
};

export default ExperimentForm;
