from fastapi import FastAPI, status

from cirrus.experiment_recipes import RemoteSetting
from cirrus.fml import FML
from cirrus.manifest_loader import ManifestLoader
from cirrus.sdk import SDK

app = FastAPI()
rs = RemoteSetting()
sdk = SDK()
manifest_loader = ManifestLoader()
fml = FML()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/enrollment_status", status_code=status.HTTP_200_OK)
async def compute_enrollment_status():
    recipes = rs.get_recipes()
    # will recieve as part of incoming request
    targeting_context = {"client_id": "testid"}
    enrolled_partial_configuration = sdk.compute_enrollments(recipes, targeting_context)
    feature_configurations = manifest_loader.get_latest_feature_manifest()
    client_feature_configuration = fml.compute_feature_configurations(
        enrolled_partial_configuration, feature_configurations
    )

    return client_feature_configuration
