from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

urlpatterns = [
    url(
        r"graphql",
        csrf_exempt(GraphQLView.as_view(graphiql=True)),
        name="nimbus-api-graphql",
    ),
]
