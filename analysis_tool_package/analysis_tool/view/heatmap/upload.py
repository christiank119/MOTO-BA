import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from analysis_tool.models import RaumPolygon, RaumPlan, Raum
from analysis_tool.forms import RaumPlanForm

def upload_raumplan(request):
    """
    View zum Hochladen eines neuen Raumplans.
    """
    if request.method == "POST":
        form = RaumPlanForm(request.POST, request.FILES)
        if form.is_valid():
            raumplan = form.save()
            # Nach erfolgreichem Upload leitet er direkt in den Bearbeitungsmodus weiter.
            return redirect('heatmap_edit', raumplan_id=raumplan.id)
    else:
        form = RaumPlanForm()
    return render(request, 'heatmap/upload.html', {'form': form})
