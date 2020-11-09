import re

from django.conf import settings


class ExperimentConstants(object):
    # Model Constants
    MAX_DURATION = 1000

    # Type stuff
    TYPE_PREF = "pref"
    TYPE_ADDON = "addon"
    TYPE_GENERIC = "generic"
    TYPE_ROLLOUT = "rollout"
    TYPE_MESSAGE = "message"
    TYPE_RAPID = "rapid"

    TYPE_CHOICES = (
        (TYPE_PREF, "Pref-Flip Experiment"),
        (TYPE_ADDON, "Add-On Experiment"),
        (TYPE_GENERIC, "Generic Experiment"),
        (TYPE_ROLLOUT, "Staged Rollout"),
        (TYPE_MESSAGE, "Message Router Content Experiment"),
        (TYPE_RAPID, "Rapid Experiment"),
    )

    @classmethod
    def FEATURE_TYPE_CHOICES(cls):  # pragma: no cover
        choices = (
            (cls.TYPE_PREF, "Pref-Flip Experiment"),
            (cls.TYPE_ADDON, "Add-On Experiment"),
            (cls.TYPE_GENERIC, "Generic Experiment"),
            (cls.TYPE_ROLLOUT, "Staged Rollout"),
            (cls.TYPE_MESSAGE, "Message Router Content Experiment"),
        )

        if settings.FEATURE_MESSAGE_TYPE:
            choices += ((cls.TYPE_RAPID, "Rapid Experiment"),)

        return choices

    # Message stuff
    MESSAGE_DEFAULT_LOCALES = ("en-AU", "en-GB", "en-CA", "en-NZ", "en-ZA", "en-US")
    MESSAGE_DEFAULT_COUNTRIES = ("US", "CA", "GB", "DE", "FR")

    MESSAGE_TYPE_CFR = "cfr"
    MESSAGE_TYPE_WELCOME = "about:welcome"

    MESSAGE_TYPE_CHOICES = (
        (MESSAGE_TYPE_CFR, "CFR"),
        (MESSAGE_TYPE_WELCOME, "about:welcome"),
    )

    MESSAGE_TEMPLATE_DOOR = "cfr_doorhanger"
    MESSAGE_TEMPLATE_URL = "cfr_urlbar_chiclet"
    MESSAGE_TEMPLATE_MILESTONE = "milestone_message"

    MESSAGE_TEMPLATE_CHOICES = (
        (MESSAGE_TEMPLATE_DOOR, "CFR Doorhanger"),
        (MESSAGE_TEMPLATE_URL, "CFR Urlbar Chiclet"),
        (MESSAGE_TEMPLATE_MILESTONE, "Milestone Message"),
    )

    # Rapid stuff
    RAPID_AA = "cfr a/a"

    RAPID_TYPE_CHOICES = ((RAPID_AA, "Rapid CFR A/A Experiment"),)

    RAPID_FEATURE_CHOICES = (("FEATURE 1", "FEATURE 1"), ("FEATURE 2", "FEATURE 2"))

    RAPID_AUDIENCE_CHOICES = (("AUDIENCE 1", "AUDIENCE 1"), ("AUDIENCE 2", "AUDIENCE 2"))

    # Rollout stuff
    ROLLOUT_TYPE_CHOICES = ((TYPE_PREF, "Pref Rollout"), (TYPE_ADDON, "Add-On Rollout"))

    ROLLOUT_PLAYBOOK_LOW_RISK = "low_risk"
    ROLLOUT_PLAYBOOK_HIGH_RISK = "high_risk"
    ROLLOUT_PLAYBOOK_MARKETING = "marketing"
    ROLLOUT_PLAYBOOK_CUSTOM = "custom"
    ROLLOUT_PLAYBOOK_CHOICES = (
        (None, "Rollout Playbook"),
        (ROLLOUT_PLAYBOOK_LOW_RISK, "Low Risk Schedule"),
        (ROLLOUT_PLAYBOOK_HIGH_RISK, "High Risk Schedule"),
        (ROLLOUT_PLAYBOOK_MARKETING, "Marketing Launch Schedule"),
        (ROLLOUT_PLAYBOOK_CUSTOM, "Custom Schedule"),
    )

    # date range stuff
    EXPERIMENT_STARTS = "starting"
    EXPERIMENT_PAUSES = "pausing"
    EXPERIMENT_ENDS = "ending"
    EXPERIMENT_COMMENT = "new comment"

    # extra email-type stuff
    INTENT_TO_SHIP_EMAIL_LABEL = "intent to ship"

    # Status stuff
    STATUS_DRAFT = "Draft"
    STATUS_REVIEW = "Review"
    STATUS_SHIP = "Ship"
    STATUS_ACCEPTED = "Accepted"
    STATUS_LIVE = "Live"
    STATUS_COMPLETE = "Complete"
    STATUS_REJECTED = "Rejected"

    STATUS_DRAFT_LABEL = "Draft"
    STATUS_REVIEW_LABEL = "Ready for Sign-Off"
    STATUS_SHIP_LABEL = "Ready to Ship"
    STATUS_ACCEPTED_LABEL = "Accepted by Normandy"
    STATUS_LIVE_LABEL = "Live"
    STATUS_COMPLETE_LABEL = "Complete"
    STATUS_REJECTED_LABEL = "Rejected"

    STATUS_CHOICES = (
        (STATUS_DRAFT, STATUS_DRAFT_LABEL),
        (STATUS_REVIEW, STATUS_REVIEW_LABEL),
        (STATUS_SHIP, STATUS_SHIP_LABEL),
        (STATUS_ACCEPTED, STATUS_ACCEPTED_LABEL),
        (STATUS_LIVE, STATUS_LIVE_LABEL),
        (STATUS_COMPLETE, STATUS_COMPLETE_LABEL),
        (STATUS_REJECTED, STATUS_REJECTED_LABEL),
    )

    STATUS_TRANSITIONS = {
        STATUS_DRAFT: [STATUS_REVIEW],
        STATUS_REVIEW: [STATUS_DRAFT, STATUS_SHIP],
        STATUS_SHIP: [STATUS_REVIEW, STATUS_ACCEPTED],
        STATUS_ACCEPTED: [STATUS_LIVE],
        STATUS_LIVE: [STATUS_COMPLETE],
        STATUS_COMPLETE: [],
    }

    RAPID_STATUS_TRANSITIONS = {
        STATUS_DRAFT: [STATUS_REVIEW],
        STATUS_ACCEPTED: [STATUS_REJECTED],
        STATUS_REJECTED: [STATUS_DRAFT],
    }

    STATUS_PROCEED_REVIEW = "Begin Sign-Offs"
    STATUS_PROCEED_SHIP = "Confirm Ready to Ship"

    EMAIL_CHOICES = (
        (EXPERIMENT_STARTS, EXPERIMENT_STARTS),
        (EXPERIMENT_PAUSES, EXPERIMENT_PAUSES),
        (EXPERIMENT_ENDS, EXPERIMENT_ENDS),
        (EXPERIMENT_COMMENT, EXPERIMENT_COMMENT),
        (INTENT_TO_SHIP_EMAIL_LABEL, INTENT_TO_SHIP_EMAIL_LABEL),
    )

    # Version stuff
    VERSION_CHOICES = (
        ("55.0", "Firefox 55.0"),
        ("56.0", "Firefox 56.0"),
        ("57.0", "Firefox 57.0"),
        ("58.0", "Firefox 58.0"),
        ("59.0", "Firefox 59.0"),
        ("60.0", "Firefox 60.0"),
        ("61.0", "Firefox 61.0"),
        ("62.0", "Firefox 62.0"),
        ("63.0", "Firefox 63.0"),
        ("64.0", "Firefox 64.0"),
        ("65.0", "Firefox 65.0"),
        ("66.0", "Firefox 66.0"),
        ("67.0", "Firefox 67.0"),
        ("68.0", "Firefox 68.0"),
        ("69.0", "Firefox 69.0"),
        ("70.0", "Firefox 70.0"),
        ("71.0", "Firefox 71.0"),
        ("72.0", "Firefox 72.0"),
        ("73.0", "Firefox 73.0"),
        ("74.0", "Firefox 74.0"),
        ("75.0", "Firefox 75.0"),
        ("76.0", "Firefox 76.0"),
        ("77.0", "Firefox 77.0"),
        ("78.0", "Firefox 78.0"),
        ("79.0", "Firefox 79.0"),
        ("80.0", "Firefox 80.0"),
        ("81.0", "Firefox 81.0"),
        ("82.0", "Firefox 82.0"),
        ("83.0", "Firefox 83.0"),
        ("84.0", "Firefox 84.0"),
        ("85.0", "Firefox 85.0"),
        ("86.0", "Firefox 86.0"),
        ("87.0", "Firefox 87.0"),
        ("88.0", "Firefox 88.0"),
        ("89.0", "Firefox 89.0"),
        ("90.0", "Firefox 90.0"),
        ("91.0", "Firefox 91.0"),
        ("92.0", "Firefox 92.0"),
        ("93.0", "Firefox 93.0"),
        ("94.0", "Firefox 94.0"),
        ("95.0", "Firefox 95.0"),
        ("96.0", "Firefox 96.0"),
        ("97.0", "Firefox 97.0"),
        ("98.0", "Firefox 98.0"),
        ("99.0", "Firefox 99.0"),
        ("100.0", "Firefox 100.0"),
    )

    VERSION_REGEX = re.compile(r"[\d]+")

    # Channel stuff
    CHANNEL_NIGHTLY = "Nightly"
    CHANNEL_BETA = "Beta"
    CHANNEL_RELEASE = "Release"

    CHANNEL_CHOICES = (
        (None, "Firefox Channel"),
        (CHANNEL_NIGHTLY, CHANNEL_NIGHTLY),
        (CHANNEL_BETA, CHANNEL_BETA),
        (CHANNEL_RELEASE, CHANNEL_RELEASE),
    )

    # Ordering given in https://github.com/mozilla/experimenter/issues/1042
    CHANNEL_NIGHTLY_ORDER = 1
    CHANNEL_BETA_ORDER = 2
    CHANNEL_RELEASE_ORDER = 3
    CHANNEL_UNSET_ORDER = 0

    # Platform stuff
    PLATFORM_ALL = "All Platforms"
    PLATFORM_WINDOWS = "All Windows"
    PLATFORM_MAC = "All Mac"
    PLATFORM_LINUX = "All Linux"

    PLATFORM_CHOICES = (
        (PLATFORM_ALL, PLATFORM_ALL),
        (PLATFORM_WINDOWS, PLATFORM_WINDOWS),
        (PLATFORM_MAC, PLATFORM_MAC),
        (PLATFORM_LINUX, PLATFORM_LINUX),
    )

    PLATFORMS_LIST = [PLATFORM_WINDOWS, PLATFORM_MAC, PLATFORM_LINUX]

    VERSION_WINDOWS_7 = "Windows 7"
    VERSION_WINDOWS_8 = "Windows 8"
    VERSION_WINDOWS_8_1 = "Windows 8.1"
    VERSION_WINDOWS_10_PLUS = "Windows 10+"

    WINDOWS_VERSION_LIST = [
        VERSION_WINDOWS_7,
        VERSION_WINDOWS_8,
        VERSION_WINDOWS_8_1,
        VERSION_WINDOWS_10_PLUS,
    ]

    PROFILES_NEW = "New Profiles Only"
    PROFILES_EXISTING = "Existing Profiles Only"
    PROFILES_ALL = "All Profiles"

    PROFILE_AGE_CHOICES = (
        (PROFILES_ALL, PROFILES_ALL),
        (PROFILES_NEW, PROFILES_NEW),
        (PROFILES_EXISTING, PROFILES_EXISTING),
    )
    # Pref stuff
    PREF_TYPE_BOOL = "boolean"
    PREF_TYPE_INT = "integer"
    PREF_TYPE_STR = "string"
    PREF_TYPE_JSON_STR = "json string"

    PREF_TYPE_CHOICES = (
        (None, "Firefox Pref Type"),
        (PREF_TYPE_BOOL, PREF_TYPE_BOOL),
        (PREF_TYPE_INT, PREF_TYPE_INT),
        (PREF_TYPE_STR, PREF_TYPE_STR),
        (PREF_TYPE_JSON_STR, PREF_TYPE_JSON_STR),
    )

    PREF_BRANCH_USER = "user"
    PREF_BRANCH_DEFAULT = "default"
    PREF_BRANCH_CHOICES = (
        (None, "Firefox Pref Branch"),
        (PREF_BRANCH_DEFAULT, PREF_BRANCH_DEFAULT),
        (PREF_BRANCH_USER, PREF_BRANCH_USER),
    )

    SECTION_TIMELINE = "timeline"
    SECTION_OVERVIEW = "overview"
    SECTION_NORMANDY = "normandy"
    SECTION_POPULATION = "population"
    SECTION_DESIGN = "design"
    SECTION_ADDON = "addon"
    SECTION_ROLLOUT = "rollout"
    SECTION_BRANCHES = "branches"
    SECTION_OBJECTIVES = "objectives"
    SECTION_ANALYSIS = "analysis"
    SECTION_RISKS = "risks"
    SECTION_TESTING = "testing"
    SECTION_RESULTS = "results"

    # Detail Sections
    SECTION_CHOICES = (
        (SECTION_TIMELINE, "Timeline"),
        (SECTION_OVERVIEW, "Overview"),
        (SECTION_NORMANDY, "Normandy"),
        (SECTION_POPULATION, "Population"),
        (SECTION_DESIGN, "Design"),
        (SECTION_ADDON, "Add-On"),
        (SECTION_ROLLOUT, "Rollout"),
        (SECTION_BRANCHES, "Branches"),
        (SECTION_OBJECTIVES, "Objectives"),
        (SECTION_ANALYSIS, "Analysis"),
        (SECTION_RISKS, "Risks"),
        (SECTION_TESTING, "Testing"),
        (SECTION_RESULTS, "Results"),
    )

    # Branched Addon Stuff
    FX_MIN_MULTI_BRANCHED_VERSION = 68

    # Bucket stuff
    BUCKET_TOTAL = 10000
    BUCKET_AA_COUNT = 100
    BUCKET_RANDOMIZATION_UNIT = "normandy_id"

    # Labels
    RISK_PARTNER_RELATED_LABEL = "Is this delivery partner related?"
    RISK_BRAND_LABEL = "Does this have a high risk to the brand?"
    RISK_FAST_SHIPPED_LABEL = """Does this delivery require uplifting code
         or a rushed delivery schedule?"""
    RISK_CONFIDENTIAL_LABEL = (
        "Is this delivery confidential to Mozilla, sensitive, or internal only?"
    )
    RISK_RELEASE_POPULATION_LABEL = "Does this delivery affect 1 million Release users?"
    RISK_REVENUE_LABEL = """Does this delivery have possible negative impact on revenue
         (ex: search, pocket revenue, New Tab page experience)?"""

    RISK_DATA_CATEGORY_LABEL = "Are you using Category 3 or 4 data?"
    RISK_EXTERNAL_TEAM_IMPACT_LABEL = (
        "Does your project impact code in other module areas or teams outside your own?"
    )
    RISK_TELEMETRY_DATA_LABEL = (
        "Do you need data that doesn’t exist in telemetry already?"
    )
    RISK_UX_LABEL = "Is UX a significant part of this delivery?"
    RISK_SECURITY_LABEL = (
        "Does this need security review, consulting, or security testing?"
    )
    RISK_REVISION_LABEL = "Is this delivery a revision of a previous delivery?"
    RISK_TECHNICAL_LABEL = "Is this delivery Complex / Technically Risky?"
    RISK_HIGHER_RISK_LABEL = """I have been advised that this delivery design creates a
        higher risk of errors due to complexity or timing requirements."""

    RISK_EXCLUSIONS = {
        TYPE_ROLLOUT: ["risk_release_population"],
        TYPE_MESSAGE: [
            "risk_brand",
            "risk_fast_shipped",
            "risk_confidential",
            "risk_release_population",
            "risk_revenue",
            "risk_data_category",
            "risk_external_team_impact",
            "risk_telemetry_data",
            "risk_ux",
            "risk_security",
            "risk_revision",
            "risk_technical",
            "risk_higher_risk",
        ],
    }

    SIGNOFF_DEFAULTS = (
        "review_science",
        "review_advisory",
        "review_engineering",
        "review_qa_requested",
        "review_intent_to_ship",
        "review_bugzilla",
        "review_qa",
        "review_relman",
    )

    SIGNOFF_TYPE_DEFAULTS = {
        TYPE_ROLLOUT: (
            "review_advisory",
            "review_qa_requested",
            "review_intent_to_ship",
            "review_qa",
            "review_relman",
        ),
        TYPE_MESSAGE: (
            "review_science",
            "review_intent_to_ship",
            "review_qa_requested",
            "review_ux",
            "review_qa",
        ),
    }

    RISK_LABELS = {
        "risk_partner_related": RISK_PARTNER_RELATED_LABEL,
        "risk_brand": RISK_BRAND_LABEL,
        "risk_fast_shipped": RISK_FAST_SHIPPED_LABEL,
        "risk_confidential": RISK_CONFIDENTIAL_LABEL,
        "risk_release_population": RISK_RELEASE_POPULATION_LABEL,
        "risk_revenue": RISK_REVENUE_LABEL,
        "risk_data_category": RISK_DATA_CATEGORY_LABEL,
        "risk_external_team_impact": RISK_EXTERNAL_TEAM_IMPACT_LABEL,
        "risk_telemetry_data": RISK_TELEMETRY_DATA_LABEL,
        "risk_ux": RISK_UX_LABEL,
        "risk_security": RISK_SECURITY_LABEL,
        "risk_revision": RISK_REVISION_LABEL,
        "risk_technical": RISK_TECHNICAL_LABEL,
        "risk_higher_risk": RISK_HIGHER_RISK_LABEL,
    }

    SURVEY_REQUIRED_LABEL = "Is a Survey Required?"
    SURVEY_INSTRUCTIONS_LABEL = "Survey Launch Instructions"

    # Help texts
    TYPE_HELP_TEXT = """
      <p>
        The delivery type will determine how the delivery feature is
        sent to Firefox users.
      </p>
      <p>
        A <strong>{[1]}</strong> uses prefs to enable code which
        has already been merged into Firefox and deployed with a standard
        Firefox release in a disabled state, and will be selectively enabled
        for users that enroll into the experiment.
      </p>
      <p>
        An <strong>{[1]}</strong> sends a Firefox Add-On which
        contains the code for the experimental feature to the users that
        enroll in the experiment.  After the experiment is complete, that
        add-on is automatically removed.
      </p>
      <p>
        A <strong>{[1]}</strong> captures any change which is delivered
        through something other than the previous types.
      </p>
      <p>
        A <strong>{[1]}</strong> slowly deploys a pref or addon change
        to increasing numbers of users.
      </p>
    """.format(
        *TYPE_CHOICES
    )

    OWNER_HELP_TEXT = """
      <p>
        The owner of the delivery is the person responsible for ensuring
        that it is run in its entirety and is the primary stake holder in
        its analysis.
      </p>
    """

    NAME_HELP_TEXT = """
      <p>
        Choose a name for your delivery that describes
        what it is trying to accomplish, such as the effect of
        a new feature, a performance improvement, a UI change, a bug fix, etc.
      <p>
      <p><strong>Example:</strong> Larger Sign In Button
    """

    SHORT_DESCRIPTION_HELP_TEXT = """
      <p>Describe the purpose of your delivery in 1-2 sentences.</p>
      <p><strong>Example:</strong> We believe increasing the size of
      the sign in button will increase its click through rate.</p>
    """

    PROPOSED_START_DATE_HELP_TEXT = """
      <p>
        Choose the date you expect the delivery to be launched to users.
        This date is for planning purposes only, the actual start date
        is subject to the sign off and review processes.  Please refer to the
        <a target="_blank" rel="noreferrer noopener"
        href="https://wiki.mozilla.org/RapidRelease/Calendar">
        Firefox Release Calendar</a>
        to coordinate the timing of your delivery with the
        Firefox Version it will be deployed to.
      </p>
    """

    PROPOSED_DURATION_HELP_TEXT = """
      <p>
        Specify the duration of the delivery in days.  This determines
        the maximum amount of time a user may be enrolled in the delivery.
        Once the delivery is live, users will begin to enroll.  They will
        remain enrolled until the entire delivery duration has
        transpired.  Once the delivery duration has elapsed,
        users will be unenrolled.
      </p>
      <p>
        <strong>Example:</strong> 30
      </p>
    """

    PROPOSED_ENROLLMENT_HELP_TEXT = """
      <p>
        Some deliveries may only wish to enroll users for a limited amount
        of time.  This period must be shorter than the entire delivery
        duration.  If you specify a limited enrollment period, then after
        that period has expired, no additional users will be enrolled into the
        delivery.  Users that have been enrolled will remain enrolled until
        the delivery ends.
      </p>
      <p>
        <strong>Example:</strong> 10
      </p>
    """

    ROLLOUT_PLAYBOOK_HELP_TEXT = """
      <p>
        <a
          target="_blank"
          rel="noopener noreferrer"
          href="https://mana.mozilla.org/wiki/pages/viewpage.action?pageId=90737068#StagedRollouts/GradualRollouts-Playbooks"
        >
          Playbook Help
        </a>
      </p>
    """

    DATA_SCIENCE_ISSUE_HELP_TEXT = """
      <p>
        Provide a link to the ticket that was filed with the Data
        Science team that tracks this delivery.  If you have not already
        filed a ticket with Data Science, you can do that <a
        target="_blank" rel="noreferrer noopener"
        href="{url}">here</a>.
      </p>
      <p>
        <strong>Example:</strong>
        {ds_issue_host}DO-352
      </p>
    """.format(
        url=("https://mana.mozilla.org/wiki/display/PM/Data+Science+Jira+documentation"),
        ds_issue_host=settings.DS_ISSUE_HOST,
    )

    FEATURE_BUGZILLA_HELP_TEXT = """
      <p>
        (Optional) Provide a link to the Bugzilla ticket that tracks the
        feature(s) or change(s) being tested in this delivery.
      </p>
      <p>
        <strong>Example:</strong>
        {}show_bug.cgi?id=12345
      </p>
    """.format(
        settings.BUGZILLA_HOST
    )

    RELATED_WORK_HELP_TEXT = """
      <p>
        Please add any bugs and/or issues related to this delivery work.
        Link to any PRDs, Invision, or related documents. Please include a
        description of for each link. This assists Relman and will help
        ensure your delivery is not held up.
      </p>
      <p><strong>Example:</strong></p>
      <p>Designs: http://www.invision.com/myprojectdesign/</p>
      <p>Feature description: https://docs.google.com/myprojectdescription/</p>
    """

    POPULATION_PERCENT_HELP_TEXT = """
      <p>Describe the Firefox population that will receive this delivery.<p>
      <p><strong>Example:</strong> 10 percent of Nightly Firefox 60.0<p>
    """

    CHANNEL_HELP_TEXT = """
        https://wiki.mozilla.org/Release_Management/Release_Process#Channels.2FRepositories
    """

    VERSION_HELP_TEXT = """
        https://wiki.mozilla.org/Release_Management/Calendar
    """

    PLATFORM_HELP_TEXT = """
        <p>
          Select the target platform for this delivery.
        </p>
    """

    CLIENT_MATCHING_HELP_TEXT = """
      <p>
        Describe the criteria a client must meet to participate in the
        delivery in addition to the version and channel filtering specified
        above. Explain in natural language how you would like clients to be
        filtered and the Shield team will implement the filtering for you,
        you do not need to express the filter in code.
        Each filter may be inclusive or exclusive, ie "Please include
        users from locales A, B, C and exclude those from X, Y, Z".
      </p>
      <ul>
        <li>
          <p><strong>Prefs</strong> Pref and value pairs to match against.</p>
          <p><strong>Example:</strong> browser.search.region=CA</p>
        </li>
        <li>
          <p><strong>Experiments</strong>
          Other Shield Experiments to match against.</p>
          <p><strong>Example:</strong>
          Exclude clients in pref-flip-other-experiment</p>
        </li>
      </ul>
    """

    PUBLIC_NAME_HELP_TEXT = """
      <p>
        Name that will be shown to Firefox users enrolled in the delivery.
      </p>
    """

    PUBLIC_DESCRIPTION_HELP_TEXT = """
      <p>
        Description that will be shown to Firefox users enrolled in the
        delivery.
      </p>
    """

    DESIGN_HELP_TEXT = """
      <p>
        Specify the design of the experiment.
      </p>
    """

    PREF_NAME_HELP_TEXT = """
      <p>
        Enter the full name of the Firefox pref key that this experiment
        will control.  A pref experiment can control exactly one pref,
        and each branch will receive a different value for that pref.
        You can find all Firefox prefs in about:config and any pref
        that appears there can be the target of an experiment.
      </p>
      <p><strong>Example:</strong>
      browser.example.component.enable_large_sign_in_button</p>
    """

    PREF_TYPE_HELP_TEXT = """
      <p>
        Select the type of the pref entered above.  The pref type
        will be shown in the third column in about:config.
      </p>
      <p><strong>Example:</strong> boolean</p>
    """

    PREF_BRANCH_HELP_TEXT = """
      <p>
        Select the pref branch the experiment will write its pref value to.
        If you're not sure what this means, you should stick to the 'default'
        pref branch.
        Pref branches are a little more complicated than can be written here,
        but you can <a target="_blank" rel="noreferrer noopener" href="{url}">
        find more information here.</a>
      </p>
      <p><strong>Example:</strong> default</p>
    """.format(
        url=(
            "https://developer.mozilla.org/en-US/docs/Archive/"
            "Add-ons/Code_snippets/Preferences#Default_preferences"
        )
    )

    ADDON_NAME_HELP_TEXT = """
      <p>
        Enter the name of your add-on.
        <a target="_blank" rel="noreferrer noopener" href="{url}">
        See here for more info.</a>
      </p>
    """.format(
        url=(
            "https://mana.mozilla.org/wiki/display/FIREFOX/"
            "Pref-Flip+and+Add-On+Experiments"
            "#Pref-FlipandAdd-OnExperiments-Add-ons"
        )
    )

    ADDON_EXPERIMENT_ID_HELP_TEXT = """
      <p>
        Enter the <code>activeExperimentName</code> as it appears in the
        add-on.  It may appear in <code>manifest.json</code> as
        <code>applications.gecko.id</code>
        <a target="_blank" rel="noreferrer noopener" href="{url}">
        See here for more info.</a>
      </p>
    """.format(
        url=(
            "https://mana.mozilla.org/wiki/display/FIREFOX/"
            "Pref-Flip+and+Add-On+Experiments"
            "#Pref-FlipandAdd-OnExperiments-Add-ons"
        )
    )

    ADDON_RELEASE_URL_HELP_TEXT = """
      <p>
        Enter the URL where the release build of your add-on can be found.
        This is often attached to a bugzilla ticket.
        This MUST BE the release signed add-on (not the test add-on)
        that you want deployed.
        <a target="_blank" rel="noreferrer noopener" href="{url}">
        See here for more info.</a>
      </p>
    """.format(
        url=(
            "https://mana.mozilla.org/wiki/display/FIREFOX/"
            "Pref-Flip+and+Add-On+Experiments"
            "#Pref-FlipandAdd-OnExperiments-Add-ons"
        )
    )

    CONTROL_NAME_HELP_TEXT = """
      <p>
        The control group should represent the users receiving the existing,
        unchanged version of what you're testing.  For example,
        if you're testing making a button larger to see
        if users click on it more often, the control group would receive
        the existing button size.  You should name your control branch
        based on the experience or functionality
        that group of users will be receiving.  Don't name it 'Control Group',
        we already know it's the control group!
      </p>
      <p><strong>Example:</strong> Normal Button Size</p>
    """

    CONTROL_DESCRIPTION_HELP_TEXT = """
      <p>
        Describe the experience or functionality the control group
        will receive in more detail.
      </p>
      <p><strong>Example:</strong> The control group will receive the
      existing 80px sign in button located at the top right of the screen.</p>
    """

    CONTROL_RATIO_HELP_TEXT = """
      <p>
        Choose the size of this branch represented as a whole number.
        The size of all branches together must be equal to 100.
        It does not have to be exact, so these sizes are simply a
        recommendation of the relative distribution of the branches.
      </p>
      <p><strong>Example</strong> 50</p>
    """

    CONTROL_VALUE_HELP_TEXT = """
      <p>
        Choose the value of the pref for the control group.
        This value must be valid JSON in order to be sent to Shield.
        This should be the right type (boolean, string, number),
        and should be the value that represents the control
        or default state to compare to.
      </p>
      <p><strong>Boolean Example:</strong> false</p>
      <p><strong>String Example:</strong> some text</p>
      <p><strong>Integer Example:</strong> 13</p>
    """

    VARIANT_NAME_HELP_TEXT = """
      <p>
        The experimental group should represent the users receiving the
        new or changed version of what you're testing.  For example,
        if you're testing making a button larger to see
        if users click on it more often, the experimental group would
        receive the larger button size.  You should name your
        experimental group based on the experience or functionality
        that group of users will be receiving.  Don't name it
        'Experimental Group', we already know it's the experimental group!
      </p>
      <p><strong>Example:</strong> Larger Button Size</p>
    """

    VARIANT_DESCRIPTION_HELP_TEXT = """
      <p>
        Describe the experience or functionality the
        experimental group will receive in more detail.
      </p>
      <p><strong>Example:</strong> The experimental group will
      receive the larger 120px sign in button located at the
      top right of the screen.</p>
    """

    VARIANT_VALUE_HELP_TEXT = """
      <p>
        Choose the value of the pref for the experimental group.
        This value must be valid JSON in order to be sent to Shield.
        This should be the right type (boolean, string, number),
        and should be the value that represents the new
        experimental state the experiment will be measuring.
      </p>
      <p><strong>Boolean Example:</strong> true</p>
      <p><strong>String Example:</strong> "some other text"</p>
      <p><strong>Integer Example:</strong> 14</p>
    """

    OBJECTIVES_HELP_TEXT = """
      <p>
        Describe the details / purpose of your delivery in for internal consumers.
         This assists supporting teams to understand what you are doing and helps
         avoid delays. It is also a useful reference to understand the experiments
         that have been run.
      </p>
      <p>
        Please add any bugs and/or issues related to this delivery work.
        Link to any PRDs, Invision, or related documents.
        Please include a description of for each link.
      </p>
    """

    TOTAL_ENROLLED_CLIENTS_HELP_TEXT = """
        https://mana.mozilla.org/wiki/pages/viewpage.action?spaceKey=FIREFOX&title=Pref-Flip+and+Add-On+Experiments#PrefFlipandAddOnExperiments-PopulationSize
    """

    TELEMETRY_EVENT_HELP_TEXT = """
      <p>
        The conversion event describes the outcome that you are attempting to drive with
        the experiment. For example, if the experiment attempts to drive users to import
        their bookmarks from a different browser, the bookmark import feature should
        send a Firefox event telemetry event when the bookmarks are imported. This event
        must be sent from clients in both the control and all treatment branches of the
        experiment. This allows us to measure the success of the experiment at driving
        the targeted interaction. An empty box will match any value for that event
        parameter.
      </p>
    """

    ENGINEERING_OWNER_HELP_TEXT = """
      <p>
        The Engineering Owner is the person responsible for the engineering
        that implements the feature or change being tested by the delivery,
        and is the primary point of contact for any inquiries related to it.
      </p>
    """

    ANALYSIS_OWNER_HELP_TEXT = """
      <p>
        The Data Science Owner is the person responsible for designing and
        implementing the delivery and its associated data analysis.
      </p>
    """

    ANALYSIS_HELP_TEXT = """
      <p>
       The analysis plan is clear leading indicator statement(s)
        of what is being observed. These reflect how you are
        impacting the hypothesis outcome(s), specifically
        what you are observing, and how much of a difference you anticipate.
      </p>
    """

    SURVEY_HELP_TEXT = """
          https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-SurveyChecklist
    """

    SURVEY_LAUNCH_INSTRUCTIONS_HELP_TEXT = """
        <p>
            <strong>If this is a Pref-flip Experiment: </strong>
            The survey needs to launch before the study ends, to allow survey
            delivery targeting based on the experiment tag.  Since the launch
            date may change (impacting study end and survey launch), please
            share the logic for how many days before the experiment ends to
            launch the survey.   We keep surveys open 7 days to allow response
            time.
        </p>
        <p>
            <strong>If this is an Add-on Experiment: </strong>
            The most common survey trigger is upon add-on expiration
            (built into the add-on).  Add-on experiments don't leave
            breadcrumbs behind on the user systems, so there is no way
            to target those users for surveying after the Normandy recipe
            is ended.  The Normandy end date needs to be scheduled AFTER
            the add-on has expired (for the last enrolled users), plus a 7
            day survey response window.
        </p>


    """

    RISKS_HELP_TEXT = """
      <p>
        The "Risk" section helps identify which additional or dependent checklist
        items need to happen. Dependent items needed vary based on the delivery.
        Please review this <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Risks&Testing">more complete Risk question list</a> and the needed actions (for "yes" answers). This list be integrated into Experimenter soon.
      </p>
    """  # noqa

    RISK_TECHNICAL_HELP_TEXT = """
    """

    TESTING_HELP_TEXT = """
      <p>
        Your code should be QA’d to ensure that changing the
        preference values has the intended effect you are looking for
        and does not cause obvious regressions to Firefox.
      </p>
      <p>
        All deliveries must pass QA. Depending on the
        channel/population size a dev QA may be accepted.
      </p>
      <p>
        If this delivery requires additional QA, please provide a
        detailed description of how each branch can be
        tested and the expected behaviours.
      </p>
    """

    TEST_BUILDS_HELP_TEXT = """
    """

    QA_STATUS_HELP_TEXT = """
    """

    # Results
    RESULTS_URL_HELP_TEXT = """
        This is the link to analysis report.
    """
    RESULTS_INITIAL_HELP_TEXT = """
        This is the place for links to any early findings or preliminary
        results, while the final results are being developed.  If there
        are not results for this specific delivery, because they are
        associated with a related delivery - this is the place to leave
        a trail to find those closely related deliveries and/or results.
    """

    RESULTS_LESSONS_HELP_TEXT = """
        What went well or did not go well with any part of the
        delivery process. This is completely optional.
        If you have feedback on any issues you experienced and
        some details - that is beneficial for us to know.
        We are always trying to identify the most common issues
        in order to continuously improve.
    """

    RESULTS_FAIL_TO_LAUNCH_LABEL = (
        "Did this delivery fail to launch at the expected time?"
    )

    RESULTS_RECIPE_ERRORS_LABEL = "Did this experiment encounter any issues or errors?"

    RESULTS_RESTARTS_LABEL = "Did this delivery require any restarts after it launched?"

    RESULTS_LOW_ENROLLMENT_LABEL = "Did this delivery have low user enrollment issues?"

    RESULTS_EARLY_END_LABEL = "Did this delivery end before it was expected to?"

    RESULTS_NO_USABLE_DATA_LABEL = "Did this delivery fail to generate usable data?"

    RESULTS_NOTES_LABEL = "Error Notes"

    RESULTS_CHANGES_TO_FIREFOX_LABEL = """
        Did changes (features, performance, UX, etc.) enter Firefox because
        of this delivery?
    """

    RESULTS_DATA_FOR_HYPOTHESIS_LABEL = """Was the data required to prove or disprove your
        hypothesis (which may include a null result) obtained?"""

    RESULTS_CONFIDENCE_LABEL = "Did this delivery move the primary metric?"

    RESULTS_MEASURE_IMPACT_LABEL = (
        "Did this delivery help understand/measure the impact of this feature?"
    )

    RESULTS_QUESTIONS_HELP = """
        https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-ResultsandFeedback
    """

    # Sign-Offs
    REVIEW_BUGZILLA_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Bugzillaupdated">Help</a>
    """  # noqa

    REVIEW_ENGINEERING_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Engineeringallocated">Help</a>
    """  # noqa

    REVIEW_SCIENCE_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-DataSciencePeerReview">Help</a>
    """  # noqa

    REVIEW_RELMAN_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-ReleaseManagementSign-off">Help</a>
    """  # noqa

    REVIEW_QA_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-QAsign-off">Help</a>
    """  # noqa

    REVIEW_QA_REQUESTED_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-QArequested.">Help</a>
    """  # noqa

    REVIEW_INTENT_TO_SHIP_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-IntenttoShipemailsent">Help</a>
    """  # noqa

    REVIEW_LIGHTNING_ADVISING_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-LightningAdvising">Help</a>
    """  # noqa

    REVIEW_GENERAL_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-DependentSign-offs">Help</a>
    """  # noqa

    # Risks

    RISK_PARTNER_RELATED_HELP_TEXT = """
      https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Risk
    """  # noqa

    RISK_BRAND_HELP_TEXT = """
      https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Risk
    """  # noqa

    RISK_FAST_SHIPPED_HELP_TEXT = """
      https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Risk
    """  # noqa

    RISK_CONFIDENTIAL_HELP_TEXT = """
      https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Risk
    """  # noqa

    RISK_RELEASE_POPULATION_HELP_TEXT = """
      https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Risk
    """  # noqa

    RISK_REVENUE_HELP_TEXT = """
      https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Risk
    """  # noqa

    RISK_DATA_CATEGORY_HELP_TEXT = """
      https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Risk
    """  # noqa

    RISK_EXTERNAL_TEAM_IMPACT_HELP_TEXT = """
      https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-ReviewfromaFirefoxModulePeer
    """  # noqa

    RISK_TELEMETRY_DATA_HELP_TEXT = """
      https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Risk
    """  # noqa

    RISK_UX_HELP_TEXT = """
      https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Risk
    """  # noqa

    RISK_SECURITY_HELP_TEXT = """
      https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Risk
    """  # noqa

    RISK_REVISION_HELP_TEXT = """
       https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Risk
    """  # noqa

    RISK_TECHNICAL_HELP_TEXT = """
      https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Risk
    """  # noqa

    RISK_HIGHER_RISK_HELP_TEXT = """
      https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Risk
    """

    # Text defaults
    CLIENT_MATCHING_DEFAULT = """Prefs:

Experiments:

Any additional filters:
    """

    DESIGN_DEFAULT = "What is the design of this delivery? Explain in detail."

    OBJECTIVES_DEFAULT = """If we <do this/build this/create this change in the experiment> for <these users>, then we will see <this outcome>.
We believe this because we have observed <this> via <data source, UR, survey>.

Optional - We believe this outcome will <describe impact> on <core metric>
    """  # noqa

    ANALYSIS_DEFAULT = """We will measure <outcome> by an <increase/decrease/neutral> of <size> in <feature telemetry>.
There may be multiple leading indicator statements.

Optional: We hypothesize the desired change will <increase/decrease/neutral> to the <core metric>.
    """  # noqa

    RISKS_DEFAULT = """
If you answered "Yes" to any of the question above - this box is the area to
capture the details.

Please include why you think the risk is worth it or needed for this
delivery. Please also include any known mitigating factors for each risk.

This information makes it easier to collaborate with supporting teams (ex: for
sign-offs). Good details avoid assumptions or delays, while people locate the
information necessary to make an informed decision.
    """.strip()

    RISK_TECHNICAL_DEFAULT = """
If you answered “yes”, your delivery is considered Complex. QA and Release
Management will need details. Please outline the technical risk factors
or complexity factors that have been identified and any mitigations.
This information will automatically be put in emails to QA.
    """.strip()

    TESTING_DEFAULT = """
If additional QA is required, provide a plan (or links to them) for testing
each branch of this delivery.
    """.strip()

    TEST_BUILDS_DEFAULT = """
If applicable, link to any relevant test builds / staging information
    """.strip()

    QA_STATUS_DEFAULT = "What is the QA status: Not started, Green, Yellow, Red"

    ATTENTION_MESSAGE = (
        "This delivery requires special attention " "and should be reviewed ASAP"
    )

    INTENT_TO_SHIP_EMAIL_SUBJECT = "Delivery Intent to ship: {name} {version} {channel}"

    LAUNCH_EMAIL_SUBJECT = "Delivery launched: {name} {version} {channel}"

    ENDING_EMAIL_SUBJECT = "Delivery ending soon: {name} {version} {channel}"

    PAUSE_EMAIL_SUBJECT = (
        "Experimenter enrollment ending verification " "for: {name} {version} {channel}"
    )

    COMMENT_EMAIL_SUBJECT = "[Experimenter]: {email} commented on {name}"

    NORMANDY_CHANGE_WINDOW = """
        https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-NormandyChangeWindow
    """

    BUGZILLA_OVERVIEW_TEMPLATE = """
{experiment.name}

{experiment.public_description}

Experimenter is the source of truth for details and delivery. Changes to Bugzilla are not reflected in Experimenter and will not change delivery configuration.

Data Science Issue: {experiment.data_science_issue_url}
More information: {experiment.experiment_url}
        """  # noqa

    BUGZILLA_VARIANT_PREF_TEMPLATE = """- {variant.type} {variant.name} {variant.ratio}%:

Value: {variant.value}

{variant.description}
        """

    BUGZILLA_PREF_TEMPLATE = """
    Delivery Type: Pref Flip Experiment

    What is the preference we will be changing

{experiment.pref_name}

    What are the branches of the experiment and what values should
    each branch be set to?

{variants}

    What version and channel do you intend to ship to?

{experiment.population}

    Are there specific criteria for participants?

{experiment.client_matching}
Countries: {countries}

Locales: {locales}

    What is your intended go live date and how long will the experiment run?

{experiment.dates}

    What is the main effect you are looking for and what data will you use to
    make these decisions?

{experiment.analysis}

    Who is the owner of the data analysis for this experiment?

{experiment.analysis_owner}

    Will this experiment require uplift?

{experiment.risk_fast_shipped}

    QA Status of your code:

{experiment.qa_status}

    Link to more information about this experiment:

{experiment.experiment_url}
        """

    BUGZILLA_VARIANT_ADDON_TEMPLATE = """- {variant.type} {variant.name} {variant.ratio}%:

{variant.description}
        """

    BUGZILLA_ADDON_TEMPLATE = """
    Delivery Type: Add-on experiment

    What are the branches of the experiment:

{variants}

    What version and channel do you intend to ship to?

{experiment.population}

    Are there specific criteria for participants?


{experiment.client_matching}

Countries: {countries}

Locales: {locales}

    What is your intended go live date and how long will the experiment run?

{experiment.dates}

    What is the main effect you are looking for and what data will you use to
    make these decisions?

{experiment.analysis}

    Who is the owner of the data analysis for this experiment?

{experiment.analysis_owner}

    Will this experiment require uplift?

{experiment.risk_fast_shipped}

    QA Status of your code:

{experiment.qa_status}

    Link to more information about this experiment:

{experiment.experiment_url}
        """
    BUGZILLA_RAPID_EXPERIMENT_TEMPLATE = """ This is an empty CFR A/A experiment. The A/A experiment is being run to test the automation, effectiveness, and accuracy of the rapid experiments platform.
    The experiment is an internal test, and Firefox users will not see any noticeable change and there will be no user impact."""  # noqa
