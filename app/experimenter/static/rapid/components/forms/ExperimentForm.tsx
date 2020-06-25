import React from "react";
import { useHistory } from "react-router-dom";

import { audiences, AudienceOption } from "../../data/Audiences";
import { features, FeatureOption } from "../../data/Features";

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

interface FormDataUIState {
  name: string;
  objectives: string;
  audience: AudienceOption | null;
  features: Array<FeatureOption>;
}

interface FormDataSubmitState {
  name: string;
  objectives: string;
  audience: string | null;
  features: Array<string>;
}

const ExperimentForm: React.FC = () => {
  const [formData, setFormData] = React.useState<FormDataUIState>({
    name: "",
    objectives: "",
    audience: null,
    features: [],
  });
  const [errors, setErrors] = React.useState<{ [name: string]: Array<string> }>(
    {},
  );
  const history = useHistory();

  const handleChange = (ev) => {
    const field = ev.target;
    setFormData({
      ...formData,
      [field.getAttribute("name")]: field.value,
    });
  };

  function transformFormData({
    name,
    objectives,
    audience,
    features,
  }: FormDataUIState): FormDataSubmitState {
    return {
      name,
      objectives,
      audience: audience ? audience.value : null,
      features: features.map(({ value }) => value),
    };
  }

  const handleClickSave = async () => {
    const response = await fetch("/api/v3/experiments/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(transformFormData(formData)),
    });
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
          Feature
        </label>
        <p>
          Select the user action or feature that you&apos;d be measuring with
          this experiment.
        </p>
        <XSelect
          isMulti
          className="w-100"
          id="field-feature"
          name="feature"
          options={features}
          value={formData.features}
          onOptionChange={(features) => setFormData({ ...formData, features })}
        />
        <ErrorList errors={errors.feature} />
      </div>

      <div className="mb-4">
        <label className="font-weight-bold" htmlFor="field-audience">
          Audience
        </label>
        <p>Choose the set of users who will see the experiment.</p>
        <XSelect<AudienceOption>
          className="w-100"
          id="field-audience"
          isClearable={true}
          name="audience"
          options={audiences}
          placeholder="Everyone"
          onOptionChange={([audience]) =>
            setFormData({ ...formData, audience })
          }
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
        <input
          className="form-control w-100"
          id="field-version"
          name="version"
          placeholder="No minimum version"
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
