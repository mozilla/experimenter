import { defineOptionsByValue } from "../components/forms/XSelect";

export interface FeatureOption {
  label: string;
  value: string;
  description: string;
}

export const features = defineOptionsByValue<FeatureOption>({
  picture_in_picture: {
    description: `Counts the number of times that a client opens a Firefox Picture-in-Picture
    window from videos. PiP can be opened by clicking on the PiP overlay or the
    video's context menu.`,
    label: "Picture-in-Picture",
  },
  pinned_tabs: {
    description: `Counts the number of times that a client pinned a tab during the
    experiment. This doesn't measure whether users already had tabs pinned
    when the experiment began.`,
    label: "Pinned Tabs",
  },
});
