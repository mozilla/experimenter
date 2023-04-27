import os
import subprocess


if __name__ == "__main__":
    tests = []
    final_string = "()"

    with open("../test_names.txt") as r:
        for item in r:
            if "test_" in item and "pytest_" not in item and ".py" not in item:
                item = item.split()[1].split("[")[0]
                item = f"{item}"
                tests.append(item)
    with open("../_test_names.txt", "+w") as _:
        for item in tests:
            _.write(f"{item} ")
    # split using circleci
    stream = os.popen("circleci tests split ../_test_names.txt")
    output = stream.read()
    
    length_of_tests = len(tests)
    final_string = f"-k '({' and '.join(output)}')"
    os.environ["PYTEST_ARGS"] = final_string
    print(final_string)
