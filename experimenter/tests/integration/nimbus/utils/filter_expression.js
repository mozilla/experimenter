async function remoteSettings(arguments) {

    /*
        Arguments contains 2 items.
        arguments[0] - the JEXL targeting string
        arguments[1] - the experiment recipe
    */

    // See https://bugzilla.mozilla.org/show_bug.cgi?id=1868838 -
    // ASRouterTargeting was moved from browser/components/newtab into
    // browser/components/asrouter and its import path changed.
    let ASRouterTargeting;
    try {
        ASRouterTargeting = ChromeUtils.import("resource:///modules/asrouter/ASRouterTargeting.jsm");
    } catch (ex) {
        if (ex.result === Cr.NS_ERROR_FILE_NOT_FOUND) {
            ASRouterTargeting = ChromeUtils.import("resource://activity-stream/lib/ASRouterTargeting.jsm");
        } else {
            throw ex;
        }
    }
    const ExperimentManager = ChromeUtils.importESModule("resource://nimbus/lib/ExperimentManager.sys.mjs");
    const TargetingContext = ChromeUtils.importESModule("resource://messaging-system/targeting/Targeting.sys.mjs");

    const _experiment = JSON.parse(arguments[1]);

    const context = TargetingContext.TargetingContext.combineContexts(
        _experiment,
        {defaultProfile: {}}, // Workaround for supporting background tasks
        ExperimentManager.ExperimentManager.createTargetingContext(),
        ASRouterTargeting.ASRouterTargeting.Environment
    );
    const targetingContext = new TargetingContext.TargetingContext(context);
    let result = false;
    try {
        result = await targetingContext.evalWithDefault(arguments[0]);
    } catch (err) {
        result = null;
    }
    return result;
}

let results = remoteSettings(arguments);

return results;
