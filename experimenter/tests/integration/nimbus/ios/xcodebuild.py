import logging
import os
import subprocess
from pathlib import Path

from .xcrun import XCRun

here = Path(__file__).resolve()
logging.getLogger(__name__).addHandler(logging.NullHandler())


class XCodeBuild:
    device = os.getenv("IOS_DEVICE", "iPhone 16")
    ios_version = os.getenv("IOS_VERSION", "18.1")
    binary = "xcodebuild"
    destination = f"platform=iOS Simulator,name={device},OS={ios_version}"
    logger = logging.getLogger()
    scheme = "Fennec"
    testPlan = "SyncIntegrationTestPlan"
    xcrun = XCRun()

    def __init__(self, log, **kwargs):
        self.scheme = kwargs.get("scheme", self.scheme)
        self.testPlan = kwargs.get("test_plan", self.testPlan)
        self.log = log
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
                f"xcrun simctl install booted {self.firefox_app_path}",
                cwd=f"{here.parent}",
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                shell=True,
            )
        except subprocess.CalledProcessError as e:
            out = e.output
            raise
        finally:
            with Path.open(self.log, "w") as f:
                f.write(out)

    def test(self, identifier, build=True, erase=True):
        run_args = "test"
        if erase:
            self.xcrun.erase()
        if not build:
            run_args = "test-without-building"
        args = [
            self.binary,
            f"{run_args}",
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
                cwd=f"{here.parents[3]}",
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError as e:
            out = e.output
            raise
        finally:
            with Path.open(self.log, "w") as f:
                f.write(out)
