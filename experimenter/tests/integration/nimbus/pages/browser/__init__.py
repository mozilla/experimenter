"""Browser Model"""

import time

from pypom import Page


class Browser:
    def execute_async_script(self, *args, script=None, context=None):
        if "chrome" in context:
            with self.context(self.CONTEXT_CHROME):
                return self.execute_async_script(script, *args)
        else:
            return self.execute_async_script(script, *args)


class AboutConfig(Page):
    URL_TEMPLATE = "about:config"

    def __init__(self, selenium, **kwargs):
        super().__init__(selenium, timeout=80, **kwargs)

    def wait_for_pref_flip(self, pref, pref_value, action=None, pref_type=str):
        timeout = time.time() + 60 * 5
        error = None
        while time.time() < timeout:
            with self.selenium.context(self.selenium.CONTEXT_CHROME):
                try:
                    if pref_type is str:
                        result = self.selenium.execute_script(
                            """
                                return Services.prefs.getStringPref(arguments[0])
                            """,
                            pref,
                        )
                    elif pref_type is bool:
                        result = self.selenium.execute_script(
                            """
                                return Services.prefs.getBoolPref(arguments[0])
                            """,
                            pref,
                        )
                    assert result == pref_value
                except Exception as e:
                    error = e
                    time.sleep(5)
                    if action:
                        action()
                    continue
                else:
                    return
        raise (error)

    def get_pref_value(self, pref, pref_type=str):
        match pref_type:
            case _ if pref_type is bool:
                method = "getBoolPref"
            case _ if pref_type is int:
                method = "getIntPref"
            case _ if pref_type is str:
                method = "getStringPref"
            case _:
                raise TypeError(f"Unsupported pref type {pref_type}")
        with self.selenium.context(self.selenium.CONTEXT_CHROME):
            return self.selenium.execute_script(
                f"return Services.prefs.{method}(arguments[0]);", pref
            )

    def set_pref(self, pref, value):
        match value:
            case bool():
                method = "setBoolPref"
            case int():
                method = "setIntPref"
            case str():
                method = "setStringPref"
            case _:
                raise TypeError(f"Unsupported pref type {type(value)}")
        with self.selenium.context(self.selenium.CONTEXT_CHROME):
            self.selenium.execute_script(
                f"Services.prefs.{method}(arguments[0], arguments[1]);", pref, value
            )

    def flip_pref(self, pref):
        self.set_pref(pref, not self.get_pref_value(pref, pref_type=bool))
