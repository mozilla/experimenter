import { FieldError } from "react-hook-form";
import { getConfig_nimbusConfig_allFeatureConfigs } from "src/types/getConfig";

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
};

export type FeatureValueEditorProps = UseCommonNestedFormProps & {
  featureConfig: getConfig_nimbusConfig_allFeatureConfigs;
};
