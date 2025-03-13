from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max
from main_app.models import Schueler, Nutzer
from analysis_tool.models import StudentOverallAnalysis, StudentAGCategoryAnalysis

@login_required(redirect_field_name="login")
def student_analysis_view(request, pupil_id):
    """
    View to display analytics for a specific student with comparison to school averages.
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
    avg_duration_data = []
    
    for analysis in category_analyses:
        category_name = analysis.ag_kategorie.name if analysis.ag_kategorie else "Ohne Kategorie"
        category_labels.append(category_name)
        time_spent_data.append(analysis.time_spent)
        frequency_data.append(analysis.frequency)
        avg_duration_data.append(analysis.average_session_duration)
    
    # Calculate diversity metric - how evenly the student distributes time across categories
    total_time = sum(time_spent_data)
    time_percentages = [time / total_time * 100 if total_time > 0 else 0 for time in time_spent_data]
    
    # Find the category with the longest continuous session duration
    if category_analyses:
        longest_continuous_index = avg_duration_data.index(max(avg_duration_data)) if avg_duration_data else 0
        longest_continuous_category = category_labels[longest_continuous_index] if category_labels else "Keine"
        longest_continuous_duration = avg_duration_data[longest_continuous_index] if avg_duration_data else 0
    else:
        longest_continuous_category = "Keine"
        longest_continuous_duration = 0
    
    # Get school-wide averages for comparison
    school_avg = {}
    
    # Average AG visits per day
    avg_ag_per_day = StudentOverallAnalysis.objects.aggregate(avg=Avg('avg_ag_per_day'))
    school_avg['avg_ag_per_day'] = avg_ag_per_day['avg'] or 0
    
    # Average session duration
    avg_continuous_duration = StudentOverallAnalysis.objects.aggregate(avg=Avg('avg_continuous_ag_duration'))
    school_avg['avg_continuous_duration'] = avg_continuous_duration['avg'] or 0
    
    # Average time spent in OGS
    avg_total_ogs_time = StudentOverallAnalysis.objects.aggregate(avg=Avg('total_ogs_time'))
    school_avg['avg_total_ogs_time'] = avg_total_ogs_time['avg'] or 0
    
    # Comparison percentiles (where does this student rank compared to others)
    percentiles = {}
    
    # Visits per day percentile
    higher_ag_visits = StudentOverallAnalysis.objects.filter(avg_ag_per_day__gt=overall_analysis.avg_ag_per_day).count()
    total_students = StudentOverallAnalysis.objects.count()
    percentiles['ag_visits'] = 100 - (higher_ag_visits / total_students * 100) if total_students > 0 else 50
    
    # Session duration percentile
    higher_duration = StudentOverallAnalysis.objects.filter(avg_continuous_ag_duration__gt=overall_analysis.avg_continuous_ag_duration).count()
    percentiles['duration'] = 100 - (higher_duration / total_students * 100) if total_students > 0 else 50
    
    # Engagement percentile (based on total OGS time)
    higher_ogs_time = StudentOverallAnalysis.objects.filter(total_ogs_time__gt=overall_analysis.total_ogs_time).count()
    percentiles['ogs_time'] = 100 - (higher_ogs_time / total_students * 100) if total_students > 0 else 50
    
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
        'longest_continuous_category': longest_continuous_category,
        'longest_continuous_duration': longest_continuous_duration,
        'school_avg': school_avg,
        'percentiles': percentiles,
        'pupil': pupil_id,  # For back button
    }
    
    return render(request, 'analysis/student_analysis.html', context)