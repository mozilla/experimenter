import { data } from "@mozilla/nimbus-shared";

import { FirefoxChannel } from "experimenter-rapid/types/experiment";

import { XSelectOption } from "./XSelect";

const generateOptions = (data) => {
  const options: Array<XSelectOption> = [];
  Object.keys(data).forEach((element) => {
    const option = {
      value: element,
      label: data[element].name,
      ...data[element],
    };
    options.push(option);
  });
  return options;
};

export const audienceOptions = generateOptions(data.Audiences);

export const featureOptions = generateOptions(data.features);

export const firefoxChannelOptions = [
  { label: "Firefox Nightly", value: FirefoxChannel.NIGHTLY },
  { label: "Firefox Beta", value: FirefoxChannel.BETA },
  { label: "Firefox Release", value: FirefoxChannel.RELEASE },
];

export const firefoxVersionOptions = [
  { label: "Firefox 77.0", value: "77.0", description: "Firefox 77.0" },
  { label: "Firefox 78.0", value: "78.0", description: "Firefox 78.0" },
  { label: "Firefox 79.0", value: "79.0", description: "Firefox 79.0" },
  { label: "Firefox 80.0", value: "80.0", description: "Firefox 80.0" },
  { label: "Firefox 81.0", value: "81.0", description: "Firefox 81.0" },
  { label: "Firefox 82.0", value: "82.0", description: "Firefox 82.0" },
  { label: "Firefox 83.0", value: "83.0", description: "Firefox 83.0" },
  { label: "Firefox 84.0", value: "84.0", description: "Firefox 84.0" },
  { label: "Firefox 85.0", value: "85.0", description: "Firefox 85.0" },
  { label: "Firefox 86.0", value: "86.0", description: "Firefox 86.0" },
  { label: "Firefox 87.0", value: "87.0", description: "Firefox 87.0" },
  { label: "Firefox 88.0", value: "88.0", description: "Firefox 88.0" },
  { label: "Firefox 89.0", value: "89.0", description: "Firefox 89.0" },
  { label: "Firefox 90.0", value: "90.0", description: "Firefox 90.0" },
  { label: "Firefox 91.0", value: "91.0", description: "Firefox 91.0" },
  { label: "Firefox 92.0", value: "92.0", description: "Firefox 92.0" },
  { label: "Firefox 93.0", value: "93.0", description: "Firefox 93.0" },
  { label: "Firefox 94.0", value: "94.0", description: "Firefox 94.0" },
  { label: "Firefox 95.0", value: "95.0", description: "Firefox 95.0" },
  { label: "Firefox 96.0", value: "96.0", description: "Firefox 96.0" },
  { label: "Firefox 97.0", value: "97.0", description: "Firefox 97.0" },
  { label: "Firefox 98.0", value: "98.0", description: "Firefox 98.0" },
  { label: "Firefox 99.0", value: "99.0", description: "Firefox 99.0" },
  { label: "Firefox 100.0", value: "100.0", description: "Firefox 100.0" },
];
