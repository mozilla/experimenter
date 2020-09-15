import pytest


def test_validating_filter_expressions(base_url, selenium):
    selenium.get("about:blank")
    js = """
        Components.utils.import("resource://gre/modules/components-utils/FilterExpressions.jsm");
        Components.utils.import("resource://gre/modules/components-utils/ClientEnvironment.jsm");
        Components.utils.import("resource://messaging-system/lib/RemoteSettingsExperimentLoader.jsm");

        // Filter expression
        var minFirefoxVersion = "78";
        var audienceFilterExpression = undefined;

        // Targeting
        var randomizationUnit = "userId";
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

        return myFunction(recipe);
    """
    with selenium.context(selenium.CONTEXT_CHROME):
        script = selenium.execute_script(js)
    print(script)
    assert False