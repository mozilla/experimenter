import React from "react";

export const DESIGN_HELP = (
  <div>
    <p>Specify the design of the experiment.</p>
  </div>
);

export const PREF_KEY_HELP = (
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
