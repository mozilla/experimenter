group "default" {
    targets = ["experimenter-dev", "experimenter-deploy", "cirrus-deploy", "nginx"]
}

group "prod" {
    targets = ["experimenter-deploy", "cirrus-deploy", "nginx"]
}

group "integration-tests" {
    targets = ["default", "rust-sdk"]
}

group "cirrus" {
    targets = ["cirrus-deploy", "cirrus-dev"]
}

group "demo" {
    targets = ["demo-app-frontend", "demo-app-backend"]
}

target "megazords" {
    context = "./application-services"

    tags = ["experimenter:megazords"]
}

target "experimenter" {
    matrix = {
        item = [
            {
                build_target = "deploy"
            },
            {
                build_target = "dev"
            },
            {
                build_target = "test"
            }
        ]
    }

    tags = ["experimenter:${item.build_target}"]
    name = "experimenter-${item.build_target}"

    context = "./experimenter"
    target = "dev"

    contexts = {
        megazords = "target:megazords"
    }
}

target "cirrus" {
    matrix = {
        item = [
            {
                build_target = "deploy"
            },
            {
                build_target = "dev"
            }
        ]
    }

    name = "cirrus-${item.build_target}"
    tags = ["cirrus:${item.build_target}"]

    context = "./cirrus/server"
    target = "deploy"
    contexts = {
        fml = "./experimenter/experimenter/features/manifests/"
        megazords = "target:megazords"
    }
}

target "nginx" {
    tags = ["experimenter:nginx"]

    context = "./nginx"
}

target "rust-sdk" {
    tags = ["experimenter:integration-tests"]

    context = "./experimenter/tests/integration"
    contexts = {
        megazords = "target:megazords"
    }
}

target "demo-app-backend" {
    tags = ["demo-app:backend"]

    context = "./demo-app/server"
}

target "demo-app-frontend" {
    tags = ["demo-app:frontend"]

    context = "./demo-app/frontend"
}
