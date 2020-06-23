import { XSelectOption } from "./XSelect";

export interface Audience extends XSelectOption {
  label: string;
  description: string;
  value: string;
  targeting?: string;
  filter_expression?: string;
}

export const audiences: Array<Audience> = Object.entries({
  all_english: {
    label: "All English users",
    description: "All users in en-* locales.",
    targeting: 'localeLanguageCode == "en"',
  },
  us_only: {
    label: "US English users",
    description: "All English users in the US.",
    targeting: 'localeLanguageCode == "en" && region == "US"',
  },
  first_run: {
    label: "English first start-up users",
    description: "English first-startup users",
    targeting:
      'localeLanguageCode == "en" && (isFirstStartup || currentExperiment.slug in activeExperiments) ',
  },
}).map(([id, props]) => {
  return {
    value: id,
    ...props,
  };
});
