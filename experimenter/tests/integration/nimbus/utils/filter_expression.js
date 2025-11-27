// Initialize TelemetryEnvironment and ExperimentAPI once at test setup
async function initialize() {
    const { TelemetryEnvironment } = ChromeUtils.importESModule("resource://gre/modules/TelemetryEnvironment.sys.mjs");
    await TelemetryEnvironment.onInitialized();

    const { ExperimentAPI } = ChromeUtils.importESModule("resource://nimbus/ExperimentAPI.sys.mjs");
    await ExperimentAPI.ready();

    return true;
}

async function remoteSettings(targetingString, recipe) {
    const { ASRouterTargeting } = ChromeUtils.importESModule("resource:///modules/asrouter/ASRouterTargeting.sys.mjs");
    const { ExperimentAPI } = ChromeUtils.importESModule("resource://nimbus/ExperimentAPI.sys.mjs");
    const { TargetingContext } = ChromeUtils.importESModule("resource://messaging-system/targeting/Targeting.sys.mjs");

    const _experiment = JSON.parse(recipe);

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
This script handles two modes:
  1. Initialization mode (1 argument): arguments[0] = callback
  2. Parallel evaluation mode (2 arguments): arguments[0] = JSON array of {slug, targeting, recipe}, arguments[1] = callback
*/

if (arguments.length === 1) {
    // Mode 1: Initialization - run once at test setup
    const [callback] = arguments;
    initialize().then(callback).catch(() => callback(false));
} else {
    // Mode 2: Parallel evaluation - evaluate all targeting expressions at once
    const [targetingTestsJson, callback] = arguments;
    const targetingTests = JSON.parse(targetingTestsJson);

    Promise.all(
        targetingTests.map(async (test) => {
            try {
                const result = await remoteSettings(test.targeting, test.recipe);
                return { slug: test.slug, result: result, error: null };
            } catch (err) {
                return { slug: test.slug, result: null, error: err.message };
            }
        })
    ).then(callback).catch(() => callback(null));
}
