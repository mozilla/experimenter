from cirrus.main import app
from fastapi.staticfiles import StaticFiles
app.openapi()

app.mount("/static", StaticFiles(directory="static"), name="static")


def generate_openapi_json():
    with open("openapi.json", "w") as f:
        f.write(app.openapi_json)
