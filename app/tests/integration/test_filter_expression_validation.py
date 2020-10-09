def test_validating_filter_expressions(base_url, selenium):
    selenium.get("about:blank")
    with open("utils/filter_expression.js") as js:
        with selenium.context(selenium.CONTEXT_CHROME):
            script = selenium.execute_script(js.read(), "filter", 80, "userID")
    print(script)
    assert False
