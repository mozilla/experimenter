import React from "react";
import { useHistory } from "react-router-dom";

import { Audience, audiences } from "./Audiences";
import { Feature, features } from "./Features";
import { XSelect } from "./XSelect";

type Errors = Array<string> | undefined;

interface ErrorMap {
  [name: string]: Errors;
}

const ErrorList: React.FC<{ errors: Errors }> = ({ errors }) => {
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

interface ExperimentFormState {
  name: string;
  objectives: string;
  audienceOption: Audience | null;
  featureOptions: Array<Feature>;
  version: "";
}

const ExperimentForm: React.FC = () => {
  const [formData, setFormData] = React.useState<ExperimentFormState>({
    name: "",
    objectives: "",
    audienceOption: null,
    featureOptions: [],
    version: "",
  });
  const [errors, setErrors] = React.useState<ErrorMap>({});
  const history = useHistory();

  const handleChange = (
    ev: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    const field = ev.target;
    setFormData({
      ...formData,
      [field.getAttribute("name") as string]: field.value,
    });
  };

  const handleClickSave = async () => {
    const response = await fetch("/api/v3/experiments/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(formData),
    });
    const responseData = await response.json();
    if (!response.ok) {
      setErrors(responseData as ErrorMap);
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
        <XSelect<Feature>
          isMulti
          id="field-feature"
          name="feature"
          options={features}
          onOptionChange={(options) => {
            setFormData({
              ...formData,
              featureOptions: options,
            });
          }}
        />
        <ErrorList errors={errors.feature} />
      </div>

      <div className="mb-4">
        <label className="font-weight-bold" htmlFor="field-audience">
          Audience
        </label>
        <p>
          Select the user action or feature that you&apos;d be measuring with
          this experiment.
        </p>
        <XSelect<Audience>
          id="field-audience"
          name="audience"
          options={audiences}
          value={formData.audienceOption}
          onOptionChange={([option]) => {
            setFormData({
              ...formData,
              audienceOption: option,
            });
          }}
        />
        <ErrorList errors={errors.audience} />
      </div>

      <div className="mb-4">
        <label className="font-weight-bold" htmlFor="field-version">
          Firefox Version
        </label>
        <p>
          Optional: Is there a minimum Firefox Release version this experiment
          should be run on?
        </p>
        <input
          className="form-control w-100"
          id="field-name"
          name="version"
          type="text"
          value={formData.version}
          onChange={handleChange}
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
