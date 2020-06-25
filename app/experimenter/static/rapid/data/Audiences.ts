import { defineOptionsByValue } from "../components/forms/XSelect";

export interface AudienceOption {
  label: string;
  value: string;
  description: string;
  targeting?: string;
  filter_expression?: string;
}

export const audiences = defineOptionsByValue<AudienceOption>({
  all_english: {
    label: "All English users",
    description: "All users in en-* locales.",
    targeting: 'localeLanguageCode == "en"',
  },
  us_only: {
    label: "US users (en)",
    description: "All users in the US with an en-* locale.",
    targeting: 'localeLanguageCode == "en" && region == "US"',
  },
  first_run: {
    label: "First start-up users (en)",
    description:
      "First start-up users (e.g. for about:welcome) with an en-* locale.",
    targeting:
      'localeLanguageCode == "en" && (isFirstStartup || currentExperiment.slug in activeExperiments) ',
  },
});
