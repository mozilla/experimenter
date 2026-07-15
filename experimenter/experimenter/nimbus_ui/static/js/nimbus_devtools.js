/* global cookieStore */

const COOKIE_NAME = "nimbus-devtools";
const ONE_DAY = 60 * 60 * 24;

function closeBanner(banner) {
  banner.classList.add("d-none");
}

async function remindLater(banner) {
  await cookieStore.set({
    name: COOKIE_NAME,
    sameSite: "strict",
    maxAge: ONE_DAY,

    value: JSON.stringify({
      dismiss: true,
    }),
  });

  closeBanner(banner);
}

async function remindNextVersion(banner, remindIfNewer) {
  await cookieStore.set({
    name: COOKIE_NAME,
    sameSite: "strict",
    value: JSON.stringify({
      remindIfNewer,
    }),
  });

  closeBanner(banner);
}

async function dismiss(banner) {
  await cookieStore.set({
    name: "nimbus-devtools",
    sameSite: "strict",
    value: JSON.stringify({
      dismiss: true,
    }),
  });

  closeBanner(banner);
}

/**
 * Compare two version 3-tuples.
 *
 * @param {[Number, Number, Number]} a The first version to compare.
 * @param {[Number, Number, Number]} b The second version to compare.
 *
 * @returns {-1 | 0 | 1} -1 if a < b, 0 if a == b, 1 if a > b
 */
function versionCompare(a, b) {
  return a[0] - b[0] || a[1] - b[1] || a[2] - b[2];
}

async function getCookie() {
  const cookie = await cookieStore.get("nimbus-devtools").catch(() => null);
  if (cookie?.value) {
    try {
      return JSON.parse(cookie.value);
    } catch (e) {
      console.error(`Invalid cookie '${cookie}'`, e);
      await cookieStore.delete("nimbus-devtools");
    }
  }

  return null;
}

export async function setupDevtoolsBanner() {
  const cookie = await getCookie();

  if (cookie?.dismiss) {
    return;
  }

  const advertiseJsonScript = document.getElementById(
    "advertise-nimbus-devtools-json",
  );
  if (!advertiseJsonScript) {
    return;
  }

  let advertiseJson;
  try {
    advertiseJson = JSON.parse(advertiseJsonScript.textContent);
  } catch {
    return;
  }

  if (typeof advertiseJson !== "object" || advertiseJson === null) {
    return;
  }

  const { availableDevtoolsVersion } = advertiseJson;
  if (
    !Array.isArray(availableDevtoolsVersion) ||
    availableDevtoolsVersion.length !== 3 ||
    availableDevtoolsVersion.some((element) => !Number.isInteger(element))
  ) {
    return;
  }

  if (
    cookie?.remindIfNewer &&
    Array.isArray(cookie.remindIfNewer) &&
    versionCompare(availableDevtoolsVersion, cookie.remindIfNewer) <= 0
  ) {
    return;
  }

  if (
    window.__NIMBUS_DEVTOOLS__ &&
    versionCompare(
      availableDevtoolsVersion,
      window.__NIMBUS_DEVTOOLS__.version,
    ) <= 0
  ) {
    return;
  }

  const banner = document.getElementById("nimbus-devtools-banner");

  banner.classList.remove("d-none");

  if (window.__NIMBUS_DEVTOOLS__?.version) {
    banner.querySelector(".old-version-placeholder").textContent =
      window.__NIMBUS_DEVTOOLS__.version.join(".");
    banner
      .querySelector(".nimbus-devtools-needs-update")
      .classList.remove("d-none");
  } else {
    banner
      .querySelector(".nimbus-devtools-needs-install")
      .classList.remove("d-none");
  }

  banner
    .querySelectorAll(".new-version-placeholder")
    .forEach((el) => (el.textContent = availableDevtoolsVersion.join(".")));

  banner
    .querySelector(".remind-later-btn")
    .addEventListener("click", () => remindLater(banner));

  banner
    .querySelector(".remind-next-version-btn")
    .addEventListener("click", () =>
      remindNextVersion(banner, availableDevtoolsVersion),
    );

  banner
    .querySelector(".dismiss-btn")
    .addEventListener("click", () => dismiss(banner));

  banner
    .querySelector(".new-version-link")
    .addEventListener("click", () => closeBanner(banner));
}
