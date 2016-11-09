from django.views.generic import View
from django.http import HttpResponse


class LandingView(View):

    def get(self, request):
        return HttpResponse('Let\'s Experiment!')
