class Browser:
    def execute_script(selenium, *args, script=None, context=None):
        if "chrome" in context:
            with selenium.context(selenium.CONTEXT_CHROME):
                return selenium.execute_script(script, *args)
        else:
            return selenium.execute_script
