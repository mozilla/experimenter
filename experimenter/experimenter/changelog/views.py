from django.views.generic import DetailView
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.constants import NimbusConstants
import logging

logger = logging.getLogger()
class NimbusChangeLogsView(DetailView):
    model = NimbusExperiment
    context_object_name = "experiment"
    template_name = "changelog/overview.html"

def update_qa_status(request):
    data = request.POST.get('data')

    logger.info("ELISE: are we getting data? " + str(data))
    
    # return HttpResponse(f"Received data: {data}")
    
    if request.method == "POST":
        experiment_slug = request.POST.get("experiment_slug")
        new_status = request.POST.get("qa_status")
        logger.info("ELISE: ========== " + str(experiment_slug) + str(new_status))

        experiment = get_object_or_404(NimbusExperiment, slug=experiment_slug)
        # experiment = NimbusExperiment.objects.filter(id=experiment_slug)
        experiment.qaStatus = new_status
        
        experiment.save()
        
        return render(request, 'changelog/qa_status.html', {'qa_status': new_status})
        # return JsonResponse({"message": "QA Status updated successfully"})
    
    return JsonResponse({"message": "Failed to update QAStatus"})
