Components.utils.import("resource://gre/modules/components-utils/FilterExpressions.jsm");
Components.utils.import("resource://gre/modules/components-utils/ClientEnvironment.jsm");
Components.utils.import("resource://messaging-system/lib/RemoteSettingsExperimentLoader.jsm");

// Filter expression
var minFirefoxVersion = arguments[1];
var audienceFilterExpression = undefined;

// Targeting
var randomizationUnit = arguments[2];
var bucketNamespace = "foo-1232ad3";
var bucketStart = 0;
var bucketCount = 50;
var bucketTotal = 100;
var audienceTargeting = "localeLanguageCode == 'en'";

var recipe = {
// These are your preset expressions, converted to JS
filter_expression: `env.version|versionCompare('${minFirefoxVersion}') >= 0 && ${audienceFilterExpression}`,
targeting: `[${randomizationUnit}, "${bucketNamespace}"]|bucketSample(${bucketStart}, ${bucketCount}, ${bucketTotal}) && ${audienceTargeting}`
};
async function myFunction(recipe) {
    let res = await FilterExpressions.eval(recipe.filter_expression, {env: ClientEnvironmentBase});
    if (res == undefined) {
        return "undefined"
    }
    return res
};
async function remoteSettings(recipe) {
    let res = await RemoteSettingsExperimentLoader.checkTargeting(recipe);
    if (res == undefined) {
        return "undefined"
    }
    return res
}

let results = {"filter": myFunction(recipe), "remote": remoteSettings(recipe)}

return results[arguments[0]];