import logging
import os
import subprocess
from pathlib import Path

from .xcrun import XCRun

HERE = Path(__file__).resolve()
LOGGER = logging.getLogger(__name__).addHandler(logging.NullHandler())


class XCodeBuild:
    def __init__(self, log, **kwargs):
        self.device = os.getenv("SIMULATOR_DEVICE", "iPhone 16")
        self.ios_version = os.getenv("IOS_VERSION", "18.1")
        self.binary = "xcodebuild"
        self.destination = (
            f"platform=iOS Simulator,name={self.device},OS={self.ios_version}"
        )
        self.scheme = "Fennec"
        self.testPlan = "ExperimentIntegrationTests"
        self.xcrun = XCRun()
        self.scheme = kwargs.get("scheme", self.scheme)
        self.test_plan = kwargs.get("test_plan", self.testPlan)
        self.log = log
        self.logger = logging.getLogger()
        self.firefox_app_path = next(
            Path("/Users").glob(
                "**/Library/Developer/Xcode/DerivedData/Client-*/Build/Products/Fennec_Testing-*/Client.app"
            )
        )

    def install(self, boot=True):
        if boot:
            self.xcrun.boot()
        try:
            out = subprocess.check_output(
                ["xcrun", "simctl", "install", "booted", self.firefox_app_path],
                cwd=f"{HERE.parent}",
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError as e:
            out = e.output
            raise
        finally:
            with self.log.open("w") as f:
                f.write(out)

    def test(self, identifier, build=True, erase=True):
        run_args = "test" if build else "test-without-building"
        args = [
            self.binary,
            run_args,
            "-scheme",
            self.scheme,
            "-destination",
            self.destination,
            f"-only-testing:{identifier}",
            "-testPlan",
            self.testPlan,
        ]
        self.logger.info("Running: {}".format(" ".join(args)))
        try:
            out = subprocess.check_output(
                args,
                cwd=f"{HERE.parents[3]}",
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError as e:
            out = e.output
            raise
        finally:
            with self.log.open("w") as f:
                f.write(out)
