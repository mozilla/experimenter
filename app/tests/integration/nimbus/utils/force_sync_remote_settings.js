XPCOMUtils.defineLazyModuleGetters(this, {
  RemoteSettings: "resource://services-settings/remote-settings.js",
});

async function sync() {
  const collection = "nimbus-desktop-experiments";
  const client = RemoteSettings(collection);
  response = await client.sync();
  return response
};

sync();