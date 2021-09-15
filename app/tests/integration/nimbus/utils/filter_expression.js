Components.utils.import("resource://gre/modules/components-utils/FilterExpressions.jsm");
Components.utils.import("resource://gre/modules/components-utils/ClientEnvironment.jsm");

// Targeting

async function remoteSettings(arguments) {

    const { TargetingContext } = ChromeUtils.import(
        "resource://messaging-system/targeting/Targeting.jsm"
    );
    const ENVIRONMENT = {version: arguments[0], localeLanguageCode: arguments[1]};
    let targeting = new TargetingContext(ENVIRONMENT);
    const EXPRESSION = `${arguments[2]}`;
    const actual = await targeting.evalWithDefault(EXPRESSION, ENVIRONMENT);
    return actual
}

let results = remoteSettings(arguments)

return results;