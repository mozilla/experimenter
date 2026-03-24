import re
from subprocess import CalledProcessError
from unittest import TestCase

from parameterized import parameterized

from manifesttool.exception_utils import format_exception


class BogusError(Exception):
    pass


class ExceptionUtilsTests(TestCase):
    maxDiff = None

    def test_format_exception(self):
        self.assertEqual(
            format_exception(Exception("exceptional")), "Exception: exceptional\n"
        )

    @parameterized.expand(
        [
            (
                CalledProcessError(1, ["/bin/bogus"]),
                "subprocess.CalledProcessError: Command '['/bin/bogus']' returned non-zero exit status 1.\n",  # noqa: E501
            ),
            (
                CalledProcessError(1, ["/bin/bogus"], output=b"stdout"),
                """\
subprocess.CalledProcessError: Command '['/bin/bogus']' returned non-zero exit status 1.

stdout:
-----
stdout
-----
""",
            ),
            (
                CalledProcessError(1, ["/bin/bogus"], stderr=b"stderr"),
                """\
subprocess.CalledProcessError: Command '['/bin/bogus']' returned non-zero exit status 1.

stderr:
-----
stderr
-----
""",
            ),
            (
                CalledProcessError(
                    1,
                    ["/bin/bogus"],
                    output=b"multi-line\nstdout\n",
                    stderr=b"multi-line\nstderr\n",
                ),
                """\
subprocess.CalledProcessError: Command '['/bin/bogus']' returned non-zero exit status 1.

stdout:
-----
multi-line
stdout
-----

stderr:
-----
multi-line
stderr
-----
""",
            ),
            (
                CalledProcessError(1, ["/bin/bogus"], output=b"\xff", stderr=b"stderr"),
                """\
subprocess.CalledProcessError: Command '['/bin/bogus']' returned non-zero exit status 1.

stdout:
-----
b'\\xff'
-----

stderr:
-----
stderr
-----
""",
            ),
            (
                CalledProcessError(2, ["/bin/bogus"], output=b"stdout", stderr=b"\xff"),
                """\
subprocess.CalledProcessError: Command '['/bin/bogus']' returned non-zero exit status 2.

stdout:
-----
stdout
-----

stderr:
-----
b'\\xff'
-----
""",
            ),
        ],
    )
    def test_format_exception_cpe(self, exc, expected):
        """Testing format_exception with a subprocess.CalledProcessError."""
        self.assertEqual(format_exception(exc), expected)

    def test_format_exception_tb(self):
        """Testing format_exception with a raised exception includes a traceback."""

        # Raise an exception so we can get a real traceback to compare against.
        try:
            raise CalledProcessError(
                1, ["/bin/bogus"], output=b"this is stdout", stderr=b"this\nis\nstderr\n"
            )
        except Exception as e:
            exc = e

        # Replace the line number in the test so that we don't have to update
        # this test if line numbers change.
        formatted = re.sub(
            r"""File "/experimenter/manifesttool/tests/test_exception_utils.py", line \d+, in test_format_exception_tb""",  # noqa: E501
            """File "/experimenter/manifesttool/tests/test_exception_utils.py", line 0000, in test_format_exception_tb""",  # noqa: E501
            format_exception(exc),
        )

        expected = """\
Traceback (most recent call last):
  File "/experimenter/manifesttool/tests/test_exception_utils.py", line 0000, in test_format_exception_tb
    raise CalledProcessError(
        1, ["/bin/bogus"], output=b"this is stdout", stderr=b"this\\nis\\nstderr\\n"
    )
subprocess.CalledProcessError: Command '['/bin/bogus']' returned non-zero exit status 1.

stdout:
-----
this is stdout
-----

stderr:
-----
this
is
stderr
-----
"""  # noqa: E501

        self.assertEqual(formatted, expected)
