from django.utils.text import format_lazy
from django.urls import reverse_lazy


class ExperimentConstants(object):
    # Model Constants
    MAX_DURATION = 1000

    # Type stuff
    TYPE_PREF = "pref"
    TYPE_ADDON = "addon"

    TYPE_CHOICES = (
        (TYPE_PREF, "Pref-Flip Study"),
        (TYPE_ADDON, "Add-On Study"),
    )

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
        STATUS_DRAFT: [STATUS_REVIEW, STATUS_REJECTED],
        STATUS_REVIEW: [STATUS_DRAFT, STATUS_SHIP, STATUS_REJECTED],
        STATUS_SHIP: [STATUS_REVIEW, STATUS_ACCEPTED, STATUS_REJECTED],
        STATUS_ACCEPTED: [STATUS_LIVE, STATUS_REJECTED],
        STATUS_LIVE: [STATUS_COMPLETE],
        STATUS_COMPLETE: [],
        STATUS_REJECTED: [],
    }

    # Version stuff
    VERSION_CHOICES = (
        (None, "Firefox Version"),
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
    )

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

    # Pref stuff
    PREF_TYPE_BOOL = "boolean"
    PREF_TYPE_INT = "integer"
    PREF_TYPE_STR = "string"

    PREF_TYPE_CHOICES = (
        (None, "Firefox Pref Type"),
        (PREF_TYPE_BOOL, PREF_TYPE_BOOL),
        (PREF_TYPE_INT, PREF_TYPE_INT),
        (PREF_TYPE_STR, PREF_TYPE_STR),
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
    SECTION_POPULATION = "population"
    SECTION_BRANCHES = "branches"
    SECTION_OBJECTIVES = "objectives"
    SECTION_ANALYSIS = "analysis"
    SECTION_RISKS = "risks"
    SECTION_TESTING = "testing"

    # Detail Sections
    SECTION_CHOICES = (
        (SECTION_TIMELINE, "Timeline"),
        (SECTION_OVERVIEW, "Overview"),
        (SECTION_POPULATION, "Population"),
        (SECTION_BRANCHES, "Firefox & Branches"),
        (SECTION_OBJECTIVES, "Objectives"),
        (SECTION_ANALYSIS, "Analysis"),
        (SECTION_RISKS, "Risks"),
        (SECTION_TESTING, "Testing"),
    )

    # Labels
    RISK_PARTNER_RELATED_LABEL = "Is this study partner related?"
    RISK_BRAND_LABEL = "Does this have a high risk to the brand?"
    RISK_FAST_SHIPPED_LABEL = (
        "Does this need to be shipped outside the normal release process?"
    )
    RISK_CONFIDENTIAL_LABEL = "Is this study confidential to Mozilla?"
    RISK_RELEASE_POPULATION_LABEL = (
        "Does this study affect a large number of Release users?"
    )
    RISK_TECHNICAL_LABEL = "Is this study Complex / Technically Risky?"

    # Help texts
    TYPE_HELP_TEXT = """
      <p>
        The study type will determine how the experimental feature is
        delivered to Firefox users.
      </p>
      <p>
        A <strong>{[1]}</strong> uses prefs to enable code which
        has already been merged into Firefox and deployed with a standard
        Firefox release in a disabled state, and will be selectively enabled
        for users that enroll into the experiment.
      </p>
      <p>
        An <strong>{[1]}</strong> sends a Firefox addon which
        contains the code for the experimental feature to the users that
        enroll in the study.  After the experiment is complete, that addon
        is automatically removed.
      </p>
    """.format(
        *TYPE_CHOICES
    )

    OWNER_HELP_TEXT = """
      <p>
        The owner of the experiment is the person responsible for ensuring
        that it is run in its entirety and is the primary stake holder in
        its analysis.
      </p>
    """

    PROJECT_HELP_TEXT = format_lazy(
        """
      <p>
        Choose which project this experiment belongs to.
        A project should correspond to a Firefox product or effort.
        If you do not see your project in this list, you can
        <a href="{project_create_url}">create one here</a>.
      </p>
    """,
        project_create_url=reverse_lazy("projects-create"),
    )

    NAME_HELP_TEXT = """
      <p>
        Choose a name for your experiment that describes
        what it is trying to study, such as the effect of
        a new feature, a performance improvement, a UI change, a bug fix, etc.
      <p>
      <p><strong>Example:</strong> Larger Sign In Button
    """

    SHORT_DESCRIPTION_HELP_TEXT = """
      <p>Describe the purpose of your experiment in 1-2 sentences.</p>
      <p><strong>Example:</strong> We believe increasing the size of
      the sign in button will increase its click through rate.</p>
    """

    PROPOSED_START_DATE_HELP_TEXT = """
      <p>
        Choose the date you expect the experiment to be launched to users.
        This date is for planning purposes only, the actual start date
        is subject to the sign off and review processes.  Please refer to the
        <a target="_blank" rel="noreferrer noopener"
        href="https://wiki.mozilla.org/RapidRelease/Calendar">
        Firefox Release Calendar</a>
        to coordinate the timing of your experiment with the
        Firefox Version it will be deployed to.
      </p>
    """

    PROPOSED_DURATION_HELP_TEXT = """
      <p>
        Specify the duration of the experiment in days.  This determines
        the maximum amount of time a user may be enrolled in the study.
        Once the study is live, users will begin to enroll.  They will
        remain enrolled until the entire experiment duration has
        transpired.  Once the experiment duration has elapsed,
        users will be unenrolled.
      </p>
      <p>
        <strong>Example:</strong> 30
      </p>
    """

    PROPOSED_ENROLLMENT_HELP_TEXT = """
      <p>
        Some experiments may only wish to enroll users for a limited amount
        of time.  This period must be shorter than the entire experiment
        duration.  If you specify a limited enrollment period, then after
        that period has expired, no additional users will be enrolled into the
        study.  Users that have been enrolled will remain enrolled until
        the experiment ends.
      </p>
      <p>
        <strong>Example:</strong> 10
      </p>
    """

    DATA_SCIENCE_BUGZILLA_HELP_TEXT = """
      <p>
        Provide a link to the Bugzilla ticket that was filed with the Data
        Science team that tracks this experiment.  If you have not already
        filed a ticket with Data Science, you can do that <a
        target="_blank" rel="noreferrer noopener"
        href="{url}">here</a>.
      </p>
      <p>
        <strong>Example:</strong>
        https://bugzilla.mozilla.org/show_bug.cgi?id=12345
      </p>
    """.format(
        url=(
            "https://mana.mozilla.org/wiki/display/PM/Firefox+Data+Science"
            "#FirefoxDataScience-initiatingaproject"
        )
    )

    FEATURE_BUGZILLA_HELP_TEXT = """
      <p>
        (Optional) Provide a link to the Bugzilla ticket that tracks the
        feature(s) or change(s) being tested in this experiment.
      </p>
      <p>
        <strong>Example:</strong>
        https://bugzilla.mozilla.org/show_bug.cgi?id=12345
      </p>
    """

    RELATED_WORK_HELP_TEXT = """
      <p>
        Please add any bugs and/or issues related to this experiment work.
        Link to any PRDs, Invision, or related documents. Please include a
        description of for each link. This assists Relman and will help
        ensure your experiment is not held up.
      </p>
      <p><strong>Example:</strong></p>
      <p>Designs: http://www.invision.com/myprojectdesign/</p>
      <p>Feature description: https://docs.google.com/myprojectdescription/</p>
    """

    POPULATION_PERCENT_HELP_TEXT = """
      <p>Describe the Firefox population that will receive this experiment.<p>
      <p><strong>Example:</strong> 10 percent of Nightly Firefox 60.0<p>
    """

    CLIENT_MATCHING_HELP_TEXT = """
      <p>
        Describe the criteria a client must meet to participate in the
        study in addition to the version and channel filtering specified above.
        Explain in natural language how you would like clients to be filtered
        and the Shield team will implement the filtering for you,
        you do not need to express the filter in code.
        Each filter may be inclusive or exclusive, ie "Please include
        users from locales A, B, C and exclude those from X, Y, Z".
      </p>
      <ul>
        <li>
          <p><strong>Locales</strong> A list of
          <a target="_blank" rel="noreferrer noopener"
          href="https://wiki.mozilla.org/L10n:Locale_Codes">
          Firefox Locale Codes</a></p>
          <p><strong>Example:</strong> en-US, fr-FR, de-DE</p>
        </li>
        <li>
          <p><strong>Geographic regions</strong> A list of
          <a target="_blank" rel="noreferrer noopener"
          href="http://www.geonames.org/countries/">
          Country Geo Codes</a></p>
          <p><strong>Example:</strong> US, FR, DE</p>
        </li>
        <li>
          <p><strong>Prefs</strong> Pref and value pairs to match against.</p>
          <p><strong>Example:</strong> browser.search.region=CA</p>
        </li>
        <li>
          <p><strong>Studies</strong>
          Other Shield Studies to match against.</p>
          <p><strong>Example:</strong>
          Exclude clients in pref-flip-other-study</p>
        </li>
      </ul>
    """

    PREF_KEY_HELP_TEXT = """
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
        The size of all branches together must be less than or equal to 100.
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
      <p><strong>String Example:</strong> "some text"</p>
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
        Describe the objective of the study in detail.  What changes
        will be made in each branch, what effects will those changes have,
        and how will those effects be measured and compared.
      </p>
      <p>
        Link to any relevant google docs / Drive files that
        describe the project. Links to prior art if it exists:
      </p>
      <p>
        If there is prior art (e.g. testpilot, usertesting.com,
        field research, etc.),
      </p>
      <p>
        If there are previous results (particularly if they allow
        for the removal of experimental branches), review them here.
      </p>
      <p><strong>Example:</strong> We think that by doing X
      we will improve [retention/page views/performance/satisfaction]</p>
    """

    ENGINEERING_OWNER_HELP_TEXT = """
      <p>
        The Engineering Owner is the person responsible for the engineering
        that implements the feature or change being tested by the experiment,
        and is the primary point of contact for any inquiries related to it.
      </p>
    """

    ANALYSIS_OWNER_HELP_TEXT = """
      <p>
        The Data Science Owner is the person responsible for designing and
        implementing the experiment and its associated data analysis.
      </p>
    """

    ANALYSIS_HELP_TEXT = """
      <p>
        Describe how this study will be analyzed, including
        which telemetry metrics will be considered, how those metrics will be
        analyzed to determine the outcome of the study,
        and who will be responsible for that analysis.
      </p>
      <p><strong>Example:</strong></p>
      <p>Unique page views</p>
      <p>Usage hours</p>
      <p>Attracting heavy users and influencers.</p>
      <p>Understanding the landscape of the web (research)</p>
    """

    RISKS_HELP_TEXT = """
      <p>
        The "Risk" section helps identify which additional or dependent checklist
        items need to happen. Dependent items needed vary based on the study.
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
        All experiments must pass QA. Depending on the
        channel/population size a dev QA may be accepted.
      </p>
      <p>
        If this study requires additional QA, please provide a
        detailed description of how each branch can be
        tested and the expected behaviours.
      </p>
    """

    TEST_BUILDS_HELP_TEXT = """
    """

    QA_STATUS_HELP_TEXT = """
    """

    # Sign-Offs
    REVIEW_COMMS_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Mozillapress/commsreview(optional)">Help</a>
    """  # noqa

    REVIEW_BUGZILLA_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Bugzillaupdated">Help</a>
    """  # noqa

    REVIEW_ENGINEERING_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Engineeringallocated">Help</a>
    """  # noqa

    REVIEW_ADVISORY_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-LightningAdvising">Help</a>
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

    REVIEW_LEGAL_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-LegalReview(optional)LegalBug">Help</a>
    """  # noqa

    REVIEW_UX_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-UXReview(Optional)">Help</a>
    """  # noqa

    REVIEW_SECURITY_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-SecurityReview(optional)">Help</a>
    """  # noqa

    REVIEW_VP_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-VPReview(optional)">Help</a>
    """  # noqa

    REVIEW_DATA_STEWARD_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-DataStewardReview(optional)">Help</a>
    """  # noqa

    REVIEW_IMPACTED_TEAMS_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-ImpactedTeam(s)Signed-off(optional)">Help</a>
    """  # noqa

    REVIEW_QA_REQUESTED_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-QArequested.">Help</a>
    """  # noqa

    REVIEW_INTENT_TO_SHIP_HELP_TEXT = """
      <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-IntenttoShipemailsent">Help</a>
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

    RISK_TECHNICAL_HELP_TEXT = """
      https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Risk
    """  # noqa

    # Text defaults
    CLIENT_MATCHING_DEFAULT = (
        """Locales:

Geographic regions:

Prefs:

Studies:

Any additional filters:
    """
    )

    OBJECTIVES_DEFAULT = (
        "What is the objective of this study?  Explain in detail."
    )

    ANALYSIS_DEFAULT = (
        """What is the main effect you are looking for and what data will
you use to make these decisions? What metrics are you using to measure success

Do you plan on surveying users at the end of the study? Yes/No.
Strategy and Insights can help create surveys if needed
    """
    )

    RISKS_DEFAULT = (
        """
If you answered "Yes" to any of the question above - this box is the area to
capture the details.

Please include why you think the risk is worth it or needed for this
experiment. Please also include any known mitigating factors for each risk.

This information makes it easier to collaborate with supporting teams (ex: for
sign-offs). Good details avoid assumptions or delays, while people locate the
information necessary to make an informed decision.
    """.strip()
    )

    RISK_TECHNICAL_DEFAULT = (
        """
If you answered “yes”, your study is considered Complex. QA and Release
Management will need details. Please outline the technical risk factors
or complexity factors that have been identified and any mitigations.
This information will automatically be put in emails to QA.
    """.strip()
    )

    TESTING_DEFAULT = (
        """
If additional QA is required, provide a plan (or links to them) for testing
each branch of this study.
    """.strip()
    )

    TEST_BUILDS_DEFAULT = (
        """
If applicable, link to any relevant test builds / staging information
    """.strip()
    )

    QA_STATUS_DEFAULT = (
        "What is the QA status: Not started, Green, Yellow, Red"
    )

    ATTENTION_MESSAGE = (
        "This experiment requires special attention "
        "and should be reviewed ASAP"
    )

    REVIEW_EMAIL_SUBJECT = "Experimenter Review Request: {name}"

    REVIEW_EMAIL_TEMPLATE = (
        """Please add the following experiment to the Shield review queue:

{experiment_url}

{attention}"""
    )

    BUGZILLA_OVERVIEW_TEMPLATE = (
        """
{experiment.name}

{experiment.short_description}

More information: {experiment.experiment_url}
        """
    )

    BUGZILLA_VARIANT_PREF_TEMPLATE = (
        """- {variant.type} {variant.name} {variant.ratio}%:

Value: {variant.value}

{variant.description}
        """
    )

    BUGZILLA_PREF_TEMPLATE = (
        """
    Experiment Type: Pref Flip Study

    What is the preference we will be changing

{experiment.pref_key}

    What are the branches of the study and what values should
    each branch be set to?

{variants}

    What version and channel do you intend to ship to?

{experiment.population}

    Are there specific criteria for participants?

{experiment.client_matching}

    What is your intended go live date and how long will the study run?

{experiment.dates}

    What is the main effect you are looking for and what data will you use to
    make these decisions?

{experiment.analysis}

    Who is the owner of the data analysis for this study?

{experiment.analysis_owner}

    Will this experiment require uplift?

{experiment.risk_fast_shipped}

    QA Status of your code:

{experiment.testing}

    Link to more information about this study:

{experiment.experiment_url}
        """
    )

    BUGZILLA_VARIANT_ADDON_TEMPLATE = (
        """- {variant.type} {variant.name} {variant.ratio}%:

{variant.description}
        """
    )

    BUGZILLA_ADDON_TEMPLATE = (
        """
    Experiment Type: Opt-Out Study

    What are the branches of the study:

{variants}

    What version and channel do you intend to ship to?

{experiment.population}

    Are there specific criteria for participants?

{experiment.client_matching}

    What is your intended go live date and how long will the study run?

{experiment.dates}

    What is the main effect you are looking for and what data will you use to
    make these decisions?

{experiment.analysis}

    Who is the owner of the data analysis for this study?

{experiment.analysis_owner}

    Will this experiment require uplift?

{experiment.risk_fast_shipped}

    QA Status of your code:

{experiment.testing}

    Link to more information about this study:

{experiment.experiment_url}
        """
    )
