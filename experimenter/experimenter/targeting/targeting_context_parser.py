import re

from django.conf import settings

from experimenter.experiments.constants import NimbusConstants


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

            if stripped_line == "val obj = JSONObject(":
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
