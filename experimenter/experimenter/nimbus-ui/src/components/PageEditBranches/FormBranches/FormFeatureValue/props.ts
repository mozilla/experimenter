import { FieldError } from "react-hook-form";
import { getConfig_nimbusConfig_allFeatureConfigs } from "src/types/getConfig";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";

type UseCommonNestedFormProps = {
  defaultValues: Record<string, any>;
  errors: Record<string, FieldError>;
  fieldNamePrefix: string;
  reviewErrors: SerializerSet;
  reviewWarnings: SerializerSet;
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>;
  submitErrors: { [x: string]: SerializerMessage };
  touched: Record<string, boolean>;
};

export type FormFeatureValueProps = UseCommonNestedFormProps & {
  featureId: number;
  experiment: getExperiment_experimentBySlug;
};

export type FeatureValueEditorProps = UseCommonNestedFormProps & {
  featureConfig: getConfig_nimbusConfig_allFeatureConfigs;
  experiment: getExperiment_experimentBySlug;
};
