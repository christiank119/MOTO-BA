from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from main_app.models import Schueler, Nutzer
from analysis_tool.models import StudentOverallAnalysis, StudentAGCategoryAnalysis

@login_required(redirect_field_name="login")
def student_analysis_view(request, pupil_id):
    """
    View to display analytics for a specific student.
    Shows both overview and detailed metrics.
    """
    # Get the student
    nutzer = get_object_or_404(Nutzer, id=pupil_id)
    schueler = get_object_or_404(Schueler, user_id=nutzer)
    
    # Get analysis data
    try:
        overall_analysis = StudentOverallAnalysis.objects.get(student=schueler)
    except StudentOverallAnalysis.DoesNotExist:
        # If no analysis exists, redirect back with message
        return redirect('pupil', pupil=pupil_id)
    
    # Get category-specific analysis
    category_analyses = StudentAGCategoryAnalysis.objects.filter(student=schueler)
    
    # Prepare data for charts
    category_labels = []
    time_spent_data = []
    frequency_data = []
    
    for analysis in category_analyses:
        category_name = analysis.ag_kategorie.name if analysis.ag_kategorie else "Ohne Kategorie"
        category_labels.append(category_name)
        time_spent_data.append(analysis.time_spent)
        frequency_data.append(analysis.frequency)
    
    # Calculate diversity metric - how evenly the student distributes time across categories
    total_time = sum(time_spent_data)
    time_percentages = [time / total_time * 100 if total_time > 0 else 0 for time in time_spent_data]
    
    # Pass all data to the template
    context = {
        'nutzer': nutzer,
        'schueler': schueler,
        'overall_analysis': overall_analysis,
        'category_analyses': category_analyses,
        'category_labels': category_labels,
        'time_spent_data': time_spent_data,
        'time_percentages': time_percentages,
        'frequency_data': frequency_data,
        'pupil': pupil_id,  # For back button
    }
    
    return render(request, 'analysis/student_analysis.html', context)