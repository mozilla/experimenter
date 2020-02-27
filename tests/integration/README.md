# Experimenter Integration Tests

### Prerequisites
- Docker
- Docker-Compose
- make
- [geckodriver]
- Python 3
- [tox]

### Setup using docker and make

To run the tests via docker-compose use the following make commands.

- Start and run the tests
```
make integration_test_run
```
You can view the tests running via VNC and port 5900. The password to connect to the container is `secret`.
To trigger the tests within the container:
```
docker-compose -p experimenter_integration -f docker-compose.yml -f docker-compose.integration-test.yml exec firefox sh -c "tox -c tests/integration"
```
With the VNC window open, you should see Firefox open and Selenium executing commands.

### Setup using local Firefox

Install [geckodriver] in your path. You should be able to do `geckodriver --version` from your terminal if your path is correct. Firefox must also be available from
your path. To verify this use the following command: `firefox --version`. If there is no output check your configuration.

Now navigate to the directory that you have cloned experimenter into and follow these steps:

1. Within the experimenter root directory:
```
mkdir python_env
python3 -m venv python_env
source python_env/bin/activate
```
If successful your shell should have an `(python_env)` prefix.
2. Install Tox
```
pip install tox
```
3. Start the tests
```
tox -c tests/integration/tox.ini
```
Firefox should open and the tests should execute.

### Extras

- To run a single test with tox you must pass the arguments through tox using `--` and then use the _keyword_ argument within pytest.
Ex: `tox -c tests/integration -- -k name_of_test`
- To deactivate the virtual env: `source deactivate`
- Setup and start containers but do not run tests: `make integration_up_detached`
- Setup and start containers but do not run tests and show all container messages: `make integration_up`
- Kill all containers: `make kill`


[geckodriver]: https://github.com/mozilla/geckodriver/releases
[tox]: https://tox.readthedocs.io/en/latest/