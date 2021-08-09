Components.utils.import("resource://gre/modules/components-utils/FilterExpressions.jsm");
Components.utils.import("resource://gre/modules/components-utils/ClientEnvironment.jsm");
// Components.utils.import("resource://messaging-system/lib/RemoteSettingsExperimentLoader.jsm");

// Targeting

async function remoteSettings(arguments) {

    const { TargetingContext } = ChromeUtils.import(
        "resource://messaging-system/targeting/Targeting.jsm"
    );
    const ENVIRONMENT = {version: arguments[0], localeLanguageCode: "en-US"};
    let targeting = new TargetingContext(ENVIRONMENT);
    const EXPRESSION = `version|versionCompare('${arguments[1]}.!') >= 0 && localeLanguageCode == 'en'`;
    const actual = await targeting.evalWithDefault(EXPRESSION, ENVIRONMENT);
    return actual
}

let results = remoteSettings(arguments)

return results;