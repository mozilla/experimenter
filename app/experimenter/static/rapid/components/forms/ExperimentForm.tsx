import React from "react";
import { useHistory, useParams } from "react-router-dom";

import {
  useExperimentDispatch,
  useExperimentState,
} from "experimenter-rapid/contexts/experiment/hooks";

import { featureOptions, audienceOptions } from "./ExperimentFormOptions";
import { XSelect } from "./XSelect";
import {
  saveExperiment,
  updateExperiment,
  fetchExperiment,
} from "experimenter-rapid/contexts/experiment/actions";

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
  const formData = useExperimentState();
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
    let response = await saveExperiment(experimentSlug, formData);

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
        <label className="font-weight-bold" htmlFor="field-version">
          Firefox Version
        </label>
        <p>
          Is there a minimum Firefox Release version this experiment should be
          run on?
        </p>
        <XSelect
          className="w-100"
          id="field-version"
          name="version"
          options={[]}
          selectValue={null}
        />
        <ErrorList errors={errors.version} />
      </div>

      <button
        className="btn btn-primary"
        type="button"
        onClick={handleClickSave}
      >
        Save
      </button>
    </form>
  );
};

export default ExperimentForm;
