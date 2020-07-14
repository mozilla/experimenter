import { ExperimentReducerActionType } from "experimenter-types/experiment";

export const fetchExperiment = (experimentSlug) => async (
  experimentData,
  dispatch,
) => {
  const response = await fetch(`/api/v3/experiments/${experimentSlug}/`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  const data = await response.json();
  dispatch({
    type: ExperimentReducerActionType.UPDATE_STATE,
    state: data,
  });
};

export const saveExperiment = async (experimentSlug, formData) => {
  const url = experimentSlug
    ? `/api/v3/experiments/${experimentSlug}/`
    : "/api/v3/experiments/";
  return await fetch(url, {
    method: experimentSlug ? "PUT" : "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(formData),
  });
};

export const updateExperiment = (name, value) => (experimentData, dispatch) => {
  dispatch({
    type: ExperimentReducerActionType.UPDATE_STATE,
    state: {
      ...experimentData,
      [name]: value,
    },
  });
};
