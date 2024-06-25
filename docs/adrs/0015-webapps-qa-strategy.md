# Implementing QA-Only Mode for Web Apps to Test Features

* **Status**: Accepted
* **Deciders**: Yashika Khurana, Jared Lockhart, Benjamin Forehand
* **Date**: 2024-06-14

## Context and Problem Statement
We have identified a significant gap in our QA testing process. Bugs are often not detected until features are live in production, despite thorough testing and QA in staging environments. This issue arises from differences in data and user interaction patterns between staging and production environments. To address this, we require a method to test features in production without affecting real users.

## Decision Drivers
- **Accuracy of Testing**: Ensuring features are tested under realistic conditions to detect bugs that may not appear in staging.
- **User Safety**: Preventing potentially disruptive features from impacting real users.
- **Efficiency**: Streamlining the testing process to facilitate rapid and effective QA cycles.

## Considered Options
- **QA-Only Preview Collection**: Introducing a new preview collection exclusively for QA testing in the production environment.
- **New QA Flag on Experimenter**: Implementing a `QA only` checkbox on the summary page for targeting purposes.

## Decision Outcome
Chosen option: "QA-Only Preview Collection," because it allows the creation of a separate preview environment (`nimbus-web-preview`) where QA can test features without impacting real users. This method offers a seamless transition from preview to launch without requiring changes to the recipe.

## Positive Consequences
- **Effective Validation**: Features are tested in the actual production environment, ensuring all configurations and data interactions are as expected.
- **Quick Issue Resolution**: Allows for the rapid detection and rectification of issues before they impact users.
- **Streamlined Processes**: Does not require cloning the experiment/rollout again once QA has tested it.
- **Consistency**: No changes are required in the recipe from preview to launch, maintaining consistency across testing and deployment phases.

## Negative Consequences
- **Resource Requirements**: Requires the setup of a separate new collection and the successful management of multiple collections by Cirrus.

## Pros and Cons of the Options

### QA-Only Preview Collection
**Workflow**:
1. **Create Experiment/Rollout**: Design and configure the experiment/rollout with all production settings intended for the final release.
2. **Push to Preview**: Launch the experiment to a separate collection called `nimbus-web-preview` that is exclusively accessed by QA.
3. **Set Preview Flag**: Implement and set the `nimbus_preview` flag in the URL (`?nimbus_preview=true`) in the implementing application when they are requesting to get the features to indicate a preview mode for QA testing.
4. **Cirrus Integration**: Configure Cirrus to fetch from both the preview and main web collections, defaulting traffic to the main web unless the preview flag is detected.
5. **Testing and Validation**: QA tests the features using the preview collection settings. This includes checking feature functionality and monitoring performance.
6. **Transition to Production**: If QA is satisfied, the preview settings are transitioned smoothly to the main production settings without requiring additional changes.

**Pros**:
- Allows specific targeting of features for testers without affecting other users.
- Minimal overhead and easy implementation.

**Cons**:
- Requires strict management to prevent misconfiguration and accidental exposure of features by Cirrus.

### New QA Flag on Experimenter
**Workflow**:
1. **Configuration Setup**: Configure the experiment/rollout with a QA-only checkbox in the audience or summary, setting the targeting context.
`Targeting: `locale == ‘en-US’ & region == ‘US’ & qa_only == 1`
`
2. **QA Activation**: Navigate to the specified URL with the `?qa_only=1` parameter to activate QA mode.
This will include the new key in the context when calling the cirrus as
`{
Locale: ‘en-US’
Region: ‘US’
‘qa_only’: urlParams.get(‘qa_only’)
}
`
3. **Test and Validate**: Perform thorough testing in the production environment while in QA mode.
4. **Review and Adjust**: Based on QA feedback, make necessary adjustments or confirm functionality.
5. **Clone and Launch**: Upon successful QA completion, clone the setup, remove the QA-only flag, and launch it for all users.

**Pros**:
- No risk to production users as testing is isolated.
- Ability to test with real data and traffic without repercussions.

**Cons**:
- Can lead to different behaviour such as what QA tested and the actual feature that gets landed
