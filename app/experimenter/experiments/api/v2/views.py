from rest_framework.generics import (
    UpdateAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.response import Response
from rest_framework import status

from experimenter.experiments.constants import ExperimentConstants
from experimenter.experiments.models import Experiment
from experimenter.experiments import email
from experimenter.experiments.serializers.entities import ExperimentSerializer
from experimenter.experiments.api.v2.serializers import (
    ExperimentCloneSerializer,
    ExperimentDesignAddonRolloutSerializer,
    ExperimentDesignAddonSerializer,
    ExperimentDesignBranchedAddonSerializer,
    ExperimentDesignGenericSerializer,
    ExperimentDesignMessageSerializer,
    ExperimentDesignMultiPrefSerializer,
    ExperimentDesignPrefRolloutSerializer,
    ExperimentDesignPrefSerializer,
)
from experimenter.experiments.api.v2.serializers import ExperimentTimelinePopSerializer


class ExperimentSendIntentToShipEmailView(UpdateAPIView):
    lookup_field = "slug"
    queryset = Experiment.objects.filter(status=Experiment.STATUS_REVIEW)
    serializer_class = ExperimentSerializer

    def update(self, request, *args, **kwargs):
        experiment = self.get_object()

        if experiment.review_intent_to_ship:
            return Response(
                {"error": "email-already-sent"}, status=status.HTTP_409_CONFLICT
            )

        email.send_intent_to_ship_email(experiment.id)

        experiment.review_intent_to_ship = True
        experiment.save()

        return Response()


class ExperimentCloneView(UpdateAPIView):
    lookup_field = "slug"
    queryset = Experiment.objects.all()
    serializer_class = ExperimentCloneSerializer


class ExperimentDesignPrefView(RetrieveUpdateAPIView):
    lookup_field = "slug"
    queryset = Experiment.objects.filter(type=ExperimentConstants.TYPE_PREF)
    serializer_class = ExperimentDesignPrefSerializer


class ExperimentDesignMultiPrefView(RetrieveUpdateAPIView):
    lookup_field = "slug"
    queryset = Experiment.objects.filter(type=ExperimentConstants.TYPE_PREF)
    serializer_class = ExperimentDesignMultiPrefSerializer


class ExperimentDesignAddonView(RetrieveUpdateAPIView):
    lookup_field = "slug"
    queryset = Experiment.objects.filter(type=ExperimentConstants.TYPE_ADDON)
    serializer_class = ExperimentDesignAddonSerializer


class ExperimentDesignGenericView(RetrieveUpdateAPIView):
    lookup_field = "slug"
    queryset = Experiment.objects.filter(type=ExperimentConstants.TYPE_GENERIC)
    serializer_class = ExperimentDesignGenericSerializer


class ExperimentDesignBranchedAddonView(RetrieveUpdateAPIView):
    lookup_field = "slug"
    queryset = Experiment.objects.filter(type=ExperimentConstants.TYPE_ADDON)
    serializer_class = ExperimentDesignBranchedAddonSerializer


class ExperimentDesignPrefRolloutView(RetrieveUpdateAPIView):
    lookup_field = "slug"
    queryset = Experiment.objects.filter(type=ExperimentConstants.TYPE_ROLLOUT)
    serializer_class = ExperimentDesignPrefRolloutSerializer


class ExperimentDesignAddonRolloutView(RetrieveUpdateAPIView):
    lookup_field = "slug"
    queryset = Experiment.objects.filter(type=ExperimentConstants.TYPE_ROLLOUT)
    serializer_class = ExperimentDesignAddonRolloutSerializer


class ExperimentDesignMessageView(RetrieveUpdateAPIView):
    lookup_field = "slug"
    queryset = Experiment.objects.filter(type=ExperimentConstants.TYPE_MESSAGE)
    serializer_class = ExperimentDesignMessageSerializer


class ExperimentTimelinePopulationView(RetrieveUpdateAPIView):
    lookup_field = "slug"
    queryset = Experiment.objects.all()
    serializer_class = ExperimentTimelinePopSerializer
