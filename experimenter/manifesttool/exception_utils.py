import subprocess
import traceback


def _format_output(output: bytes) -> str:
    try:
        output = output.decode("utf-8")
    except Exception:
        return f"{output}\n"

    # If there is any output, ensure it ends with a newline for formatting
    # purposes.
    if not output.endswith("\n"):
        output += "\n"

    return output


def format_exception(exc: Exception) -> str:
    """Format an exception into a string.

    If the exception is a :ref:`subprocess.CalledProcessError`, stdout and
    stderr will be included if present.

    NB: This is similar to :ref:`traceback.format_exception`, except it returns
    a string instead of a list of strings.
    """
    parts = traceback.format_exception(exc)

    if isinstance(exc, subprocess.CalledProcessError):
        if exc.stdout is not None:
            stdout = _format_output(exc.stdout)
            if stdout:
                parts.append(f"\nstdout:\n-----\n{stdout}-----\n")

        if exc.stderr is not None:
            stderr = _format_output(exc.stderr)
            if stderr:
                parts.append(f"\nstderr:\n-----\n{stderr}-----\n")

    return "".join(parts)
