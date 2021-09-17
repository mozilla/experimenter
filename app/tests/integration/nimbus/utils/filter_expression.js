Components.utils.import("resource://gre/modules/components-utils/FilterExpressions.jsm");
Components.utils.import("resource://gre/modules/components-utils/ClientEnvironment.jsm");

// Targeting

async function remoteSettings(arguments) {

    const ExperimentLoader = ChromeUtils.import(
        "resource://nimbus/lib/RemoteSettingsExperimentLoader.jsm"
    );
    let experiment_loader = new ExperimentLoader._RemoteSettingsExperimentLoader()
    const result = await experiment_loader.evaluateJexl(arguments[0], {experiment: arguments[1]})
    return result
}

let results = remoteSettings(arguments)

return results;