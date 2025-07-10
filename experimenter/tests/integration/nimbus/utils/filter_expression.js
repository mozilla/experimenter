async function remoteSettings(targetingString, recipe) {
    const { TelemetryEnvironment } = ChromeUtils.importESModule("resource://gre/modules/TelemetryEnvironment.sys.mjs");
    await TelemetryEnvironment.onInitialized();

    const { ASRouterTargeting } = ChromeUtils.importESModule("resource:///modules/asrouter/ASRouterTargeting.sys.mjs");
    const { ExperimentAPI } = ChromeUtils.importESModule("resource://nimbus/ExperimentAPI.sys.mjs");
    const { TargetingContext } = ChromeUtils.importESModule("resource://messaging-system/targeting/Targeting.sys.mjs");

    const _experiment = JSON.parse(recipe);
    await ExperimentAPI.ready();

    const context = TargetingContext.combineContexts(
        _experiment,
        {
            defaultProfile: {},
            attributionData: {},
            isMSIX: {},
            isDefaultHandler: {},
            defaultPDFHandler: {}
        }, // Workaround for supporting background tasks
        ExperimentAPI.manager.createTargetingContext(),
        ASRouterTargeting.Environment
    );
    const targetingContext = new TargetingContext(context);
    try {
        const evalResult = await targetingContext.evalWithDefault(targetingString);
        return evalResult !== undefined;
    } catch (err) {
        return null;
    }
}

/*
Arguments contains 3 items.
arguments[0] - the JEXL targeting string
arguments[1] - the experiment recipe
arguments[3] - the callback from selenium
*/
const [targetingString, recipe, callback] = arguments;

remoteSettings(targetingString, recipe)
  .then(result => {
    callback(result);
  })
  .catch(err => {
    callback(null);
  });
