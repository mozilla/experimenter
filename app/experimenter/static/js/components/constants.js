import React from "react";

export const TYPE_ADDON = "addon";
export const TYPE_GENERIC = "generic";
export const TYPE_MESSAGE = "message";
export const TYPE_PREF = "pref";
export const TYPE_ROLLOUT = "rollout";

export const PREF_TYPE_BOOL = "boolean";
export const PREF_TYPE_INT = "integer";
export const PREF_TYPE_STR = "string";
export const PREF_TYPE_JSON_STR = "json string";

export const DESIGN_HELP = (
  <div>
    <p>Specify the design of the experiment.</p>
  </div>
);

export const PREF_NAME_HELP = (
  <div>
    <p>
      Enter the full name of the Firefox pref key that this experiment will
      control. A pref experiment can control exactly one pref, and each branch
      will receive a different value for that pref. You can find all Firefox
      prefs in about:config and any pref that appears there can be the target of
      an experiment.
    </p>
    <p>
      <strong>Example: </strong>
      browser.example.component.enable_large_sign_in_button
    </p>
  </div>
);

export const PREF_TYPE_HELP = (
  <div>
    <p>
      Select the type of the pref entered above. The pref type will be shown in
      the third column in about:config.
    </p>
    <p>
      <strong>Example:</strong> boolean
    </p>
  </div>
);

export const PREF_BRANCH_HELP = (
  <div>
    <p>
      Select the pref branch the experiment will write its pref value to. If
      you're not sure what this means, you should stick to the 'default' pref
      branch. Pref branches are a little more complicated than can be written
      here, but you can find&nbsp;
      <a href="https://developer.mozilla.org/en-US/docs/Archive/Add-ons/Code_snippets/Preferences#Default_preferences">
        more information here
      </a>
      .
    </p>
    <p>
      <strong>Example:</strong> default
    </p>
  </div>
);

export const PREF_VALUE_HELP = (
  <div>
    <p className="mt-2">
      Choose the value of the pref for the control group. This value must be
      valid JSON in order to be sent to Shield. This should be the right type
      (boolean, string, number), and should be the value that represents the
      control or default state to compare to.
    </p>
    <p>
      <strong>Boolean Example:</strong> false
    </p>
    <p>
      <strong>String Example:</strong> some text
    </p>
    <p>
      <strong>Integer Example:</strong> 13
    </p>
  </div>
);

export const ADDON_EXPERIMENT_ID_HELP = (
  <div>
    <p>
      Enter the <code>activeExperimentName</code> as it appears in the add-on.
      It may appear in <code>manifest.json</code> as
      <code> applications.gecko.id </code>
      <a
        target="_blank"
        rel="noreferrer noopener"
        href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Add-ons"
      >
        See here for more info.
      </a>
    </p>
  </div>
);

export const ADDON_RELEASE_URL_HELP = (
  <div>
    <p>
      Enter the URL where the release build of your add-on can be found. This is
      often attached to a bugzilla ticket. This MUST BE the release signed
      add-on (not the test add-on) that you want deployed.&nbsp;
      <a
        target="_blank"
        rel="noreferrer noopener"
        href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Add-ons"
      >
        See here for more info.
      </a>
    </p>
  </div>
);

export const BRANCH_RATIO_HELP = (
  <div>
    <p>
      Choose the size of this branch represented as a whole number. The size of
      all branches together must be equal to 100. It does not have to be exact,
      so these sizes are simply a recommendation of the relative distribution of
      the branches.
    </p>
    <p>
      <strong>Example:</strong> 50
    </p>
  </div>
);

export const BRANCH_NAME_HELP = (
  <div>
    <p>
      The control group should represent the users receiving the existing,
      unchanged version of what you're testing. For example, if you're testing
      making a button larger to see if users click on it more often, the control
      group would receive the existing button size. You should name your control
      branch based on the experience or functionality that group of users will
      be receiving. Don't name it 'Control Group', we already know it's the
      control group!
    </p>
    <p>
      <strong>Example:</strong> Normal Button Size
    </p>
  </div>
);

export const BRANCH_DESCRIPTION_HELP = (
  <div>
    <p>
      Describe the experience or functionality the control group will receive in
      more detail.
    </p>
    <p>
      <strong>Example:</strong> The control group will receive the existing 80px
      sign in button located at the top right of the screen.
    </p>
  </div>
);

export const ROLLOUT_DESCRIPTION_HELP = (
  <div>
    <p>
      Describe the changes that will be shipped in this rollout and how they
      fill affect users.
    </p>
  </div>
);

export const ROLLOUT_PREF_BRANCH_HELP = (
  <div>
    <p>
      Select the pref branch the experiment will write its pref value to. If
      you're not sure what this means, please read:&nbsp;
      <a href="https://docs.telemetry.mozilla.org/cookbooks/client_guidelines.html">
        more about it here
      </a>
      .
    </p>
  </div>
);

export const MESSAGE_ID_HELP = (
  <div>
    <p>Herp derp</p>
  </div>
);

export const MESSAGE_CONTENT_HELP = (
  <div>
    <p>Herp derp</p>
  </div>
);

export const VERSION_CHOICES = [
  [null, "Versions"],
  ["55.0", "Firefox 55.0"],
  ["56.0", "Firefox 56.0"],
  ["57.0", "Firefox 57.0"],
  ["58.0", "Firefox 58.0"],
  ["59.0", "Firefox 59.0"],
  ["60.0", "Firefox 60.0"],
  ["61.0", "Firefox 61.0"],
  ["62.0", "Firefox 62.0"],
  ["63.0", "Firefox 63.0"],
  ["64.0", "Firefox 64.0"],
  ["65.0", "Firefox 65.0"],
  ["66.0", "Firefox 66.0"],
  ["67.0", "Firefox 67.0"],
  ["68.0", "Firefox 68.0"],
  ["69.0", "Firefox 69.0"],
  ["70.0", "Firefox 70.0"],
  ["71.0", "Firefox 71.0"],
  ["72.0", "Firefox 72.0"],
  ["73.0", "Firefox 73.0"],
  ["74.0", "Firefox 74.0"],
  ["75.0", "Firefox 75.0"],
  ["76.0", "Firefox 76.0"],
  ["77.0", "Firefox 77.0"],
  ["78.0", "Firefox 78.0"],
  ["79.0", "Firefox 79.0"],
  ["80.0", "Firefox 80.0"],
  ["81.0", "Firefox 81.0"],
  ["82.0", "Firefox 82.0"],
  ["83.0", "Firefox 83.0"],
  ["84.0", "Firefox 84.0"],
  ["85.0", "Firefox 85.0"],
  ["86.0", "Firefox 86.0"],
  ["87.0", "Firefox 87.0"],
  ["88.0", "Firefox 88.0"],
  ["89.0", "Firefox 89.0"],
  ["90.0", "Firefox 90.0"],
  ["91.0", "Firefox 91.0"],
  ["92.0", "Firefox 92.0"],
  ["93.0", "Firefox 93.0"],
  ["94.0", "Firefox 94.0"],
  ["95.0", "Firefox 95.0"],
  ["96.0", "Firefox 96.0"],
  ["97.0", "Firefox 97.0"],
  ["98.0", "Firefox 98.0"],
  ["99.0", "Firefox 99.0"],
  ["100.0", "Firefox 100.0"],
];

export const PLAYBOOK_CHOICES = [
  [null, "Rollout Playbook"],
  ["low_risk", "Low Risk Schedule"],
  ["high_risk", "High Risk Schedule"],
  ["marketing", "Marketing Launch Schedule"],
  ["custom", "Custom Schedule"],
];

export const PLATFORM_CHOICES = [
  { value: "All Mac", label: "All Mac" },
  { value: "All Linux", label: "All Linux" },
  { value: "All Windows", label: "All Windows" },
];

export const PROPOSED_START_DATE_HELP = (
  <p>
    Choose the date you expect the delivery to be launched to users. This date
    is for planning purposes only, the actual start date is subject to the sign
    off and review processes. Please refer to the
    <a
      target="_blank"
      rel="noreferrer noopener"
      href="https://wiki.mozilla.org/RapidRelease/Calendar"
    >
      Firefox Release Calendar
    </a>
    to coordinate the timing of your delivery with the Firefox Version it will
    be deployed to.
  </p>
);

export const PROPOSED_DURATION_HELP = (
  <div>
    <p>
      Specify the duration of the delivery in days. This determines the maximum
      amount of time a user may be enrolled in the delivery. Once the delivery
      is live, users will begin to enroll. They will remain enrolled until the
      entire delivery duration has transpired. Once the delivery duration has
      elapsed, users will be unenrolled.
    </p>
    <p>
      <strong>Example:</strong> 30
    </p>
  </div>
);

export const PROPOSED_ENROLLMENT_HELP = (
  <div>
    <p>
      Some deliveries may only wish to enroll users for a limited amount of
      time. This period must be shorter than the entire delivery duration. If
      you specify a limited enrollment period, then after that period has
      expired, no additional users will be enrolled into the delivery. Users
      that have been enrolled will remain enrolled until the delivery ends.
    </p>
    <p>
      <strong>Example:</strong> 10
    </p>
  </div>
);

export const CHANNEL_HELP =
  "https://wiki.mozilla.org/Release_Management/Release_Process#Channels.2FRepositories";

export const POPULATION_PERCENT_HELP = (
  <div>
    <p>Describe the Firefox population that will receive this delivery.</p>
    <p>
      <strong>Example:</strong> 10 percent of Nightly Firefox 60.0
    </p>
  </div>
);

export const VERSION_HELP =
  "https://wiki.mozilla.org/Release_Management/Calendar";

export const ROLLOUT_PLAYBOOK_HELP =
  "https://mana.mozilla.org/wiki/pages/viewpage.action?pageId=90737068#StagedRollouts/GradualRollouts-Playbooks";

export const PLATFORM_HELP = (
  <p>Select the target platform for this delivery.</p>
);

export const CLIENT_MATCHING_HELP = (
  <div>
    <p>
      Describe the criteria a client must meet to participate in the delivery in
      addition to the version and channel filtering specified above. Explain in
      natural language how you would like clients to be filtered and the Shield
      team will implement the filtering for you, you do not need to express the
      filter in code. Each filter may be inclusive or exclusive, ie "Please
      include users from locales A, B, C and exclude those from X, Y, Z".
    </p>
    <ul>
      <li>
        <p>
          <strong>Prefs</strong> Pref and value pairs to match against.
        </p>
        <p>
          <strong>Example:</strong> browser.search.region=CA
        </p>
      </li>
      <li>
        <p>
          <strong>Experiments</strong>
          Other Shield Experiments to match against.
        </p>
        <p>
          <strong>Example:</strong>
          Exclude clients in pref-flip-other-experiment
        </p>
      </li>
    </ul>
  </div>
);

export const COUNTRIES_LOCALES_HELP = (
  <p>Applicable only if you don't select All</p>
);

export const MESSAGE_TYPE_CFR = "cfr";
export const MESSAGE_TYPE_WNP = "wnp";
export const MESSAGE_TYPE_MOMENTS = "moments";

export const MESSAGE_TYPE_CHOICES = [
  [MESSAGE_TYPE_CFR, "CFR"],
  [MESSAGE_TYPE_WNP, "What's New Panel"],
  [MESSAGE_TYPE_MOMENTS, "Moments Pages"],
];
