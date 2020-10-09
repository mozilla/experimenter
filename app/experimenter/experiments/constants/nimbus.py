from django.db import models


class NimbusConstants(object):
    class Status(models.TextChoices):
        DRAFT = "Draft"
        REVIEW = "Review"
        SHIP = "Ship"
        ACCEPTED = "Accepted"
        LIVE = "Live"
        COMPLETE = "Complete"
        REJECTED = "Rejected"

    class Application(models.TextChoices):
        DESKTOP = "firefox-desktop"
        FENIX = "fenix"
        REFERENCE = "reference-browser"

    class Channel(models.TextChoices):
        DESKTOP_BETA = "Beta"
        DESKTOP_NIGHTLY = "Nightly"
        DESKTOP_RELEASE = "Release"
        FENIX_BETA = "org.mozilla.firefox.beta"
        FENIX_NIGHTLY = "org.mozilla.fenix"
        FENIX_RELEASE = "org.mozilla.firefox"
        REFERENCE_RELEASE = "org.mozilla.reference.browser"

    ApplicationChannels = {
        Application.DESKTOP: [
            Channel.DESKTOP_NIGHTLY,
            Channel.DESKTOP_BETA,
            Channel.DESKTOP_RELEASE,
        ],
        Application.FENIX: [
            Channel.FENIX_NIGHTLY,
            Channel.FENIX_BETA,
            Channel.FENIX_RELEASE,
        ],
        Application.REFERENCE: [Channel.REFERENCE_RELEASE],
    }

    class Audience(models.TextChoices):
        AUDIENCE_1 = "Audience 1"
        AUDIENCE_2 = "Audience 2"

    class Version(models.TextChoices):
        FIREFOX_80 = "80.0"
        FIREFOX_81 = "81.0"
        FIREFOX_82 = "82.0"
        FIREFOX_83 = "83.0"
        FIREFOX_84 = "84.0"
        FIREFOX_85 = "85.0"
        FIREFOX_86 = "86.0"
        FIREFOX_87 = "87.0"
        FIREFOX_88 = "88.0"
        FIREFOX_89 = "89.0"
        FIREFOX_90 = "90.0"
        FIREFOX_91 = "91.0"
        FIREFOX_92 = "92.0"
        FIREFOX_93 = "93.0"
        FIREFOX_94 = "94.0"
        FIREFOX_95 = "95.0"
        FIREFOX_96 = "96.0"
        FIREFOX_97 = "97.0"
        FIREFOX_98 = "98.0"
        FIREFOX_99 = "99.0"
        FIREFOX_100 = "100.0"

    class ProbeKind(models.TextChoices):
        EVENT = "event"
        SCALAR = "scalar"

    # Telemetry systems including Firefox Desktop Telemetry v4 and Glean
    # have limits on the length of their unique identifiers, we should
    # limit the size of our slugs to the smallest limit, which is 80
    # for Firefox Desktop Telemetry v4.
    MAX_SLUG_LEN = 80

    MAX_DURATION = 1000

    # Bucket stuff
    BUCKET_TOTAL = 10000
    BUCKET_AA_COUNT = 100
    BUCKET_RANDOMIZATION_UNIT = "normandy_id"

    OBJECTIVES_DEFAULT = """If we <do this/build this/create this change in the experiment> for <these users>, then we will see <this outcome>.
We believe this because we have observed <this> via <data source, UR, survey>.

Optional - We believe this outcome will <describe impact> on <core metric>
    """  # noqa
