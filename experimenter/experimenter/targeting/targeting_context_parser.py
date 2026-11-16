import re

from django.conf import settings

from experimenter.experiments.constants import NimbusConstants


class RecordedPrefs:
    """The prefs the Desktop recorder writes to nimbus_targeting_environment.pref_values.

    Targeting may reference any pref, but only these are recorded, so a reference
    to any other resolves to NULL in the sizing SQL and matches nobody.
    """

    _desktop_prefs = None

    # Keys sit at indent 2 inside the object literal. The value may wrap onto the
    # next line, so match the key alone.
    _PREF_KEY = re.compile(r'^  "([^"]+)"')

    @classmethod
    def _parse(cls, targeting_context_code):
        found_block = False
        prefs = []

        for line in targeting_context_code.splitlines():
            if line.strip() == "export const PREFS = Object.freeze({":
                found_block = True
            elif found_block and line.strip() == "});":
                break
            elif found_block:
                if match := cls._PREF_KEY.match(line):
                    prefs.append(match.group(1))

        return prefs

    @classmethod
    def clear_cache(cls):
        cls._desktop_prefs = None

    @classmethod
    def for_desktop(cls):
        """Union across every recorder version held in the repo.

        The sizing pool spans Firefox versions, so a pref dropped from the
        current recorder is still present in data from older clients. Taking
        only the current list would warn on prefs that do resolve.
        """
        if cls._desktop_prefs is None:
            app = NimbusConstants.Application.DESKTOP
            app_path = settings.FEATURE_MANIFESTS_PATH / app
            file_name = NimbusConstants.APPLICATION_CONFIGS[
                app
            ].targeting_context_file_name

            prefs = set()
            for path in app_path.glob(f"**/{file_name}"):
                prefs.update(cls._parse(path.read_text()))
            cls._desktop_prefs = sorted(prefs)
        return cls._desktop_prefs


class SettablePrefs:
    """The prefs a Nimbus feature can set, which the client reports as user-set.

    Firefox builds nimbus_targeting_environment.user_set_prefs only from the
    `setPref` entries in the feature manifests. A `preferenceIsUserSet` check on
    any other pref is false for every client.
    """

    _desktop_prefs = None

    _SET_PREF = re.compile(r"^(\s*)setPref:\s*(.*)$")
    _PREF = re.compile(r"^\s*pref:\s*(\S+)")

    @staticmethod
    def _unquote(value):
        return value.strip("'\"")

    @classmethod
    def _parse(cls, manifest_text):
        # A text scan, not a YAML load: there is one large manifest per version.
        # `setPref` is either `setPref: some.pref` or a block with a `pref:` key.
        prefs = set()
        lines = manifest_text.splitlines()
        for index, line in enumerate(lines):
            match = cls._SET_PREF.match(line)
            if not match:
                continue
            indent, inline = len(match.group(1)), match.group(2).strip()
            if inline:
                prefs.add(cls._unquote(inline))
                continue
            for following in lines[index + 1 : index + 6]:
                if (
                    following.strip()
                    and len(following) - len(following.lstrip()) <= indent
                ):
                    break
                if pref := cls._PREF.match(following):
                    prefs.add(cls._unquote(pref.group(1)))
                    break
        return prefs

    @classmethod
    def clear_cache(cls):
        cls._desktop_prefs = None

    @classmethod
    def for_desktop(cls):
        """Union across every manifest version, since the pool spans versions."""
        if cls._desktop_prefs is None:
            app_path = (
                settings.FEATURE_MANIFESTS_PATH / NimbusConstants.Application.DESKTOP
            )
            prefs = set()
            for path in app_path.glob("**/experimenter.yaml"):
                prefs |= cls._parse(path.read_text())
            cls._desktop_prefs = frozenset(prefs)
        return cls._desktop_prefs


class TargetingContextFields:
    _desktop_targeting_fields = None
    _fenix_targeting_fields = None
    _ios_targeting_fields = None

    _CACHE_FIELDS = {
        NimbusConstants.Application.DESKTOP: "_desktop_targeting_fields",
        NimbusConstants.Application.FENIX: "_fenix_targeting_fields",
        NimbusConstants.Application.IOS: "_ios_targeting_fields",
    }

    @staticmethod
    def _parse_desktop_targeting_fields(targeting_context_code):
        found_block = False
        targeting_fields = []
        # This regex is meant to only match lines on the primary level of the object
        # literal, so it looks for lines that start with two spaces followed by a letter.
        # This is to avoid matching nested lines.
        target_line_match = re.compile(r"^  [a-zA-Z]")

        for line in targeting_context_code.splitlines():
            stripped_line = line.strip()

            if stripped_line == "export const ATTRIBUTE_TRANSFORMS = Object.freeze({":
                found_block = True
            elif found_block and stripped_line == "});":
                break
            elif found_block:
                if target_line_match.match(line):
                    targeting_fields.append(stripped_line.split(":")[0].strip())

        return targeting_fields

    @staticmethod
    def _parse_fenix_targeting_fields(targeting_context_code):
        found_block = False
        targeting_fields = []
        target_line_match = re.compile(r'"([^"]+)"')

        for line in targeting_context_code.splitlines():
            stripped_line = line.strip()

            if stripped_line == "override fun toJson(): JsonObject {":
                found_block = True
            elif found_block and stripped_line == "),":
                break
            elif found_block:
                res = target_line_match.search(stripped_line)
                if res:
                    targeting_fields.append(res.group(1))

        return targeting_fields

    @staticmethod
    def _parse_ios_targeting_fields(targeting_context_code):
        found_block = False
        targeting_fields = []
        target_line_match = re.compile(r'"([^"]+)"')

        for line in targeting_context_code.splitlines():
            stripped_line = line.strip()

            if (
                stripped_line
                == "guard let data = try? JSONSerialization.data(withJSONObject: ["
            ):
                found_block = True
            elif found_block and stripped_line == "]),":
                break
            elif found_block:
                res = target_line_match.search(stripped_line)
                if res:
                    targeting_fields.append(res.group(1))

        return targeting_fields

    @classmethod
    def _load_targeting_fields(cls, app, version=None):
        app_path = (
            settings.FEATURE_MANIFESTS_PATH / app / version
            if version
            else settings.FEATURE_MANIFESTS_PATH / app
        )
        targeting_context_path = (
            app_path
            / NimbusConstants.APPLICATION_CONFIGS[app].targeting_context_file_name
        )

        targeting_context_code = targeting_context_path.read_text()

        match app:
            case NimbusConstants.Application.DESKTOP:
                return cls._parse_desktop_targeting_fields(targeting_context_code)
            case NimbusConstants.Application.FENIX:
                return cls._parse_fenix_targeting_fields(targeting_context_code)
            case NimbusConstants.Application.IOS:
                return cls._parse_ios_targeting_fields(targeting_context_code)

    @classmethod
    def clear_cache(cls, application=None):
        if application is None:
            for field_name in cls._CACHE_FIELDS.values():
                setattr(cls, field_name, None)
            return

        field_name = cls._CACHE_FIELDS.get(application)
        if field_name is not None:
            setattr(cls, field_name, None)

    @classmethod
    def for_application(cls, app, version=None):
        field_name = cls._CACHE_FIELDS.get(app)
        if field_name is None:
            raise ValueError(f"Unknown application: {app}")

        cached_fields = getattr(cls, field_name)
        if cached_fields is not None:
            return cached_fields

        targeting_fields = cls._load_targeting_fields(app, version)
        setattr(cls, field_name, targeting_fields)
        return targeting_fields
