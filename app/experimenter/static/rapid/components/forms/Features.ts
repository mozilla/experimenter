import { XSelectOption } from "./XSelect";

export interface Feature extends XSelectOption {
  value: string;
  label: string;
  description: string;
}

export const features: Array<Feature> = Object.entries({
  pip: {
    label: "Picture-in-picture",
    value: "pip",
    description: "Create events for picture-in-picture",
  },
  pinnedTabs: {
    label: "Pinned tabs",
    description: "Pin events for pinned tabs",
  },
}).map(([id, props]) => {
  return {
    value: id,
    ...props,
  };
});
