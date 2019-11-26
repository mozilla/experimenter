import React from "react";

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
