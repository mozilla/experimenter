import re

from django.conf import settings
from django.core.management.base import BaseCommand

from experimenter.experiments.constants import Application
from experimenter.experiments.versions import VersionsLoader

MANIFEST_APPLICATIONS = (Application.DESKTOP, Application.FENIX, Application.IOS)
MANIFEST_VERSION_RE = re.compile(r"^v(?P<major>\d+)\.")
VALUE_MAJOR_RE = re.compile(r"^(?P<major>\d+)\.")


class Command(BaseCommand):
    help = (
        "Append upcoming Firefox majors to versions.yaml, keeping the ceiling "
        f"{settings.FIREFOX_VERSIONS_AHEAD} majors ahead of the latest feature "
        "manifest"
    )

    def handle(self, *args, **options):
        ceiling = self.highest_manifest_major() + settings.FIREFOX_VERSIONS_AHEAD
        highest_yaml_major = self.highest_yaml_major()

        new_lines = []
        for major in range(highest_yaml_major + 1, ceiling + 1):
            new_lines.extend(self.entries_for_major(major))

        if not new_lines:
            self.stdout.write("versions.yaml is already at the ceiling, nothing to add")
            return

        with settings.FIREFOX_VERSIONS_PATH.open("a") as versions_file:
            versions_file.writelines(f"{line}\n" for line in new_lines)

        VersionsLoader.clear_cache()

        self.stdout.write(
            f"Added Firefox {highest_yaml_major + 1} through {ceiling} to versions.yaml"
        )

    def highest_manifest_major(self):
        max_major = 0

        for application in MANIFEST_APPLICATIONS:
            application_dir = settings.FEATURE_MANIFESTS_PATH / application

            for child in application_dir.iterdir():
                if child.is_dir() and (match := MANIFEST_VERSION_RE.match(child.name)):
                    max_major = max(max_major, int(match.group("major")))

        assert max_major > 0, "expected versioned application manifests"

        return max_major

    def highest_yaml_major(self):
        max_major = 0

        for value in VersionsLoader.all().values():
            if match := VALUE_MAJOR_RE.match(value):
                max_major = max(max_major, int(match.group("major")))

        return max_major

    def entries_for_major(self, major):
        return [
            f'FIREFOX_{major}: "{major}.!"',
            f'FIREFOX_{major}_0_1: "{major}.0.1"',
            f'FIREFOX_{major}_0_2: "{major}.0.2"',
            f'FIREFOX_{major}_0_3: "{major}.0.3"',
            f'FIREFOX_{major}_0_4: "{major}.0.4"',
            f'FIREFOX_{major}_1_0: "{major}.1.0"',
            f'FIREFOX_{major}_2_0: "{major}.2.0"',
            f'FIREFOX_{major}_3_0: "{major}.3.0"',
            f'FIREFOX_{major}_4_0: "{major}.4.0"',
        ]
