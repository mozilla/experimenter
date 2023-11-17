from django.views.generic import DetailView
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import render, redirect

from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.constants import NimbusConstants
import logging

logger = logging.getLogger()
class NimbusChangeLogsView(DetailView):
    model = NimbusExperiment
    context_object_name = "experiment"
    template_name = "changelog/overview.html"

@require_POST
def update_qa_status(request):
    model = NimbusExperiment
    experiment_slug = request.POST.get("experiment_slug")

    queryset = NimbusExperiment.objects.filter(id=experiment_slug)
    if request.method == "POST":
        new_status = request.POST.get("qa_status")
        
        experiment = queryset
        experiment.qaStatus = new_status.value
        experiment.update(
            qaStatus=new_status
        )
        experiment.save()
        
        return render(request, 'changelog/qa_status.html', {'qa_status': new_status})
        # return JsonResponse({"message": "QA Status updated successfully"})
    
    return JsonResponse({"message": "Failed to update QAStatus"})
