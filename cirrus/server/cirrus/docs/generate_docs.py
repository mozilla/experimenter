from cirrus.main import app

app.openapi()


def generate_openapi_json():
    with open("openapi.json", "w") as f:
        f.write(app.openapi_json)
