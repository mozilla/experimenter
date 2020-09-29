import React from "react";
import { useHistory, useParams } from "react-router-dom";

import {
  saveExperiment,
  updateExperiment,
} from "experimenter-rapid/contexts/experiment/actions";
import {
  useExperimentDispatch,
  useExperimentState,
} from "experimenter-rapid/contexts/experiment/hooks";
import { ExperimentStatus, Variant } from "experimenter-rapid/types/experiment";

import {
  featureOptions,
  audienceOptions,
  firefoxChannelOptions,
  firefoxVersionOptions,
} from "./ExperimentFormOptions";
import { TabRoutes } from "./TabRoutes";
import { VariantValueForm } from "./VariantValueForm";
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

export const SettingsForm: React.FC = () => {
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
      dispatch(updateExperiment({ [name]: value }));
    };
  };

  const handleChange = (ev) => {
    const field = ev.target;
    dispatch(updateExperiment({ [field.getAttribute("name")]: field.value }));
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
        <p
          className="font-weight-bold"
          data-testid="field-feature-label"
          id="field-feature-label"
        >
          Features
        </p>
        <p>
          Select the user action or feature that you&apos;d be measuring with
          this experiment.
        </p>
        {/* 
          Slight hack we'll want to address in `nimbus-ui`: if an XSelect has multiple
          options, it renders `<div>`s from `react-select` which can't have a `label`
          since they're not form elements. An `aria-labelledby` works the same, but
          won't render as an attribute so it's stuck on a container div. Additionally,
          `data-testid` won't render either so the test goes by ID and not testid.
        */}
        <div aria-labelledby="field-feature-label">
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
      </div>

      <div className="mb-4">
        <p
          className="font-weight-bold"
          data-testid="field-audience-label"
          id="field-audience-label"
        >
          Audience
        </p>
        <p>Description of audience.</p>
        <div aria-labelledby="field-audience-label">
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
      </div>

      <div className="mb-4">
        <p
          className="font-weight-bold"
          data-testid="field-firefox-min-version-label"
          id="field-firefox-min-version-label"
        >
          Firefox Minimum Version
        </p>
        <p>
          Is there a minimum Firefox Release version this experiment should be
          run on?
        </p>
        <div aria-labelledby="field-firefox-min-version-label">
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
      </div>

      <div className="mb-4">
        <p
          className="font-weight-bold"
          data-testid="field-firefox-channel-label"
          id="field-firefox-channel-label"
        >
          Firefox Channel
        </p>
        <p>What channel do you want to run this experiment on?</p>
        <div aria-labelledby="field-firefox-channel">
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

export const BranchesForm: React.FC = () => {
  const formData = useExperimentState();

  const variants =
    [...formData.variants].sort((a, b) =>
      a.is_control < b.is_control ? 1 : -1,
    ) || [];

  function ratioToPercentage(ratio: number) {
    const ratioTotal: number = variants.reduce((a, b) => a + b.ratio, 0);
    return Math.round((ratio / ratioTotal) * 10000) / 100;
  }

  const dispatch = useExperimentDispatch();

  const handleVariantFieldChange = (ev, i) => {
    const field = ev.target;
    const name = field.getAttribute("name");
    handleVariantChange(name, field.value, i);
  };

  const handleVariantChange = (name, value, i) => {
    const updatedVariants: Variant[] = variants.map((v, index) => {
      if (index === i) {
        return { ...v, [name]: value };
      }

      return v;
    });

    dispatch(updateExperiment({ variants: updatedVariants }));
  };

  const NEW_BRANCH: Variant = {
    name: `variant-${variants.length}`,
    is_control: false,
    description: "An empty branch",
    value: "",
    ratio: 1,
  };

  const handleAddBranch = () => {
    const updatedVariants = [...variants, NEW_BRANCH];
    dispatch(updateExperiment({ variants: updatedVariants }));
  };

  const handleRemoveBranch = (i: number) => {
    const updatedVariants = variants.filter((v, index) => {
      return i !== index;
    });

    dispatch(updateExperiment({ variants: updatedVariants }));
  };

  return (
    <div style={{ width: "75%" }}>
      <div className="mb-4">
        <h5>Branches</h5>
        <p>You can change the configuration of a feature in each branch.</p>
      </div>
      {[...variants]
        // Sort control branch to the top

        .map((variant, i) => {
          return (
            <div key={`${i}${variants.length}`} className="card mb-4">
              <ul className="list-group list-group-flush">
                <li className="list-group-item">
                  <div className="container">
                    <div className="row">
                      <div className="col">
                        <label htmlFor={`variant-name-${i}`}>
                          Branch{" "}
                          {variant.is_control && (
                            <span className="badge badge-pill badge-primary">
                              control
                            </span>
                          )}
                        </label>
                        <input
                          className="form-control"
                          id={`variant-name-${i}`}
                          name="name"
                          type="text"
                          value={variant.name}
                          onChange={(ev) => handleVariantFieldChange(ev, i)}
                        />
                      </div>
                      <div className="col-6">
                        <label htmlFor={`variant-description-${i}`}>
                          Description
                        </label>
                        <input
                          className="form-control"
                          id={`variant-description-${i}`}
                          name="description"
                          type="text"
                          value={variant.description}
                          onChange={(ev) => handleVariantFieldChange(ev, i)}
                        />
                        <small className="form-text text-muted">
                          Only visible in internal tools behind LDAP.
                        </small>
                      </div>
                      <div className="col">
                        <label htmlFor={`variant-ratio-${i}`}>Ratio</label>
                        <div className="input-group">
                          <input
                            readOnly
                            className="form-control"
                            id={`variant-ratio-${i}`}
                            name="ratio"
                            type="number"
                            value={ratioToPercentage(variant.ratio)}
                          />
                          <div className="input-group-append">
                            <div className="input-group-text">%</div>
                          </div>
                        </div>
                      </div>
                      {!variant.is_control && (
                        <div>
                          <button
                            aria-label="Close"
                            className="close"
                            type="button"
                            onClick={() => handleRemoveBranch(i)}
                          >
                            <span>&times;</span>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </li>
                <li className="list-group-item">
                  <div className="container">
                    <div className="row">
                      <div className="col">
                        <label htmlFor={`variant-feature-${i}`}>Feature</label>
                      </div>
                    </div>
                    <div className="row mb-2">
                      <div className="col-6">
                        <fieldset disabled>
                          <input
                            readOnly
                            className="form-control disabled"
                            id={`variant-feature-${i}`}
                            type="text"
                            value="Empty"
                          />
                          <small className="form-text text-muted">
                            This will be become editable as we implement more
                            features.
                          </small>
                        </fieldset>
                      </div>
                      <div className="col-2">
                        <div className="custom-control custom-switch">
                          <input
                            readOnly
                            checked={true}
                            className="custom-control-input "
                            id={`variant-enabled-${i}`}
                            type="checkbox"
                          />
                          <label
                            className="custom-control-label"
                            htmlFor={`variant-enabled-${i}`}
                          >
                            Enabled
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>
                </li>
                <li className="list-group-item">
                  <VariantValueForm
                    key={i}
                    index={i}
                    value={variant.value}
                    onChange={handleVariantChange}
                  />
                </li>
              </ul>
            </div>
          );
        })}
      <button
        className="btn btn-primary"
        type="button"
        onClick={handleAddBranch}
      >
        Add Branch
      </button>
    </div>
  );
};

const ExperimentForm: React.FC = () => {
  return (
    <TabRoutes
      tabs={[
        {
          label: "Settings",
          path: "",
          component: SettingsForm,
        },
        {
          label: "Branches",
          path: "branches",
          component: BranchesForm,
        },
      ]}
    />
  );
};

export default ExperimentForm;
