// Initialize modules once
const { TelemetryEnvironment } = ChromeUtils.importESModule("resource://gre/modules/TelemetryEnvironment.sys.mjs");
const { ASRouterTargeting } = ChromeUtils.importESModule("resource:///modules/asrouter/ASRouterTargeting.sys.mjs");
const { ExperimentAPI } = ChromeUtils.importESModule("resource://nimbus/ExperimentAPI.sys.mjs");
const { TargetingContext } = ChromeUtils.importESModule("resource://messaging-system/targeting/Targeting.sys.mjs");

async function evaluateTargeting(targetingString, recipe) {
    const _experiment = typeof recipe === "string" ? JSON.parse(recipe) : recipe;

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
        throw err;
    }
}

async function main() {
    // Initialize once
    await TelemetryEnvironment.onInitialized();
    await ExperimentAPI.ready();

    const [testsJson, callback] = arguments;
    const tests = JSON.parse(testsJson);

    // Evaluate all targeting expressions in parallel
    const results = await Promise.all(
        tests.map(async (test) => {
            try {
                const result = await evaluateTargeting(test.targeting, test.recipe);
                return { slug: test.slug, result: result, error: null };
            } catch (err) {
                return { slug: test.slug, result: null, error: err.message };
            }
        })
    );

    callback(results);
}

main().catch(() => {
    const [, callback] = arguments;
    callback(null);
});
