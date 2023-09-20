import logging
import os

import yaml

from experimenter.settings import BASE_DIR

# Todo: Connect FML https://mozilla-hub.atlassian.net/browse/EXP-3791
# from nimbus-experimenter import Fml

logger = logging.getLogger()


class NimbusFmlLoader:
    def __init__(self, application: str, channel: str):
        self.application: str = application
        self.channel: str = channel

        path = os.path.join(BASE_DIR, "features", "manifests", "apps.yaml")
        fml_local = ""
        if os.path.exists(path):
            with open(path) as application_yaml_file:
                application_data = yaml.load(
                    application_yaml_file.read(), Loader=yaml.Loader
                )
                for feature_slug in application_data:
                    if feature_slug in application:
                        fml_local = application_data[feature_slug]["fml_path"]
                        logger.info(str(fml_local))
                        break
        if fml_local != "":
            self.fml_loader = self.create(path, channel)
            logger.info("FML loader created")
        else:
            logger.error("Failed to find fml path for application: " + application)

    def create(self, path: str, channel: str):
        return "success"
        # Todo: Connect FML https://mozilla-hub.atlassian.net/browse/EXP-3791
        # return Fml.new(path, channel)
