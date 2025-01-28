// Targeting

async function remoteSettings(arguments) {

    const { TargetingContext } = ChromeUtils.importESModule(
        "resource://messaging-system/targeting/Targeting.sys.mjs"
    );
    const ENVIRONMENT = {version: arguments[0], localeLanguageCode: "en-US"};
    let targeting = new TargetingContext(ENVIRONMENT);
    const EXPRESSION = `version|versionCompare('${arguments[1]}.!') >= 0 && localeLanguageCode == 'en'`;
    const actual = await targeting.evalWithDefault(EXPRESSION, ENVIRONMENT);
    return actual
}

let results = remoteSettings(arguments)

return results;
