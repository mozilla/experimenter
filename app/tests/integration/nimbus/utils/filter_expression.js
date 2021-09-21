Components.utils.import("resource://gre/modules/components-utils/FilterExpressions.jsm");
Components.utils.import("resource://gre/modules/components-utils/ClientEnvironment.jsm");

// Targeting

async function remoteSettings(arguments) {

    /*
        Arguments contains 2 items.
        arguments[0] - the JEXL targeting string
        arguments[1] - the experiment recipe
    */

    const TargetingContext = ChromeUtils.import(
        "resource://messaging-system/targeting/Targeting.jsm"
    );

    _experiment = JSON.parse(arguments[1]);
    const targetingContext = new TargetingContext.TargetingContext(_experiment);
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