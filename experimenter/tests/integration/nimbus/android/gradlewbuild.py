import logging
import os
import subprocess
import time

from .adbrun import ADBrun

here = os.path.dirname(__file__)
logging.getLogger(__name__).addHandler(logging.NullHandler())


class GradlewBuild:
    binary = "./gradlew"
    logger = logging.getLogger()
    adbrun = ADBrun()

    def __init__(self, log):
        self.log = log

    def test(self, identifier, smoke=None):
        test_type = "ui" if smoke else "experimentintegration"
        cmd = f"adb shell am instrument -w -e class org.mozilla.fenix.{test_type}.{identifier} -e EXP_NAME '{os.getenv('EXP_NAME', '').replace('(', '').replace(')', '')}' org.mozilla.fenix.debug.test/androidx.test.runner.AndroidJUnitRunner"

        self.logger.info(f"Running cmd: {cmd}")

        out = ""
        try:
            out = subprocess.check_output(
                cmd, encoding="utf8", shell=True, stderr=subprocess.STDOUT
            )
            logging.debug(out)
            if "FAILURES" in out:
                raise (AssertionError(out))
        except subprocess.CalledProcessError as e:
            out = e.output
            raise
        finally:
            with open(self.log, "w") as f:
                f.write(str(out))
            time.sleep(10)
