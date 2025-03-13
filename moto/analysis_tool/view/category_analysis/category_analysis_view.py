from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum, Count, F, Q, Max
import pandas as pd
import numpy as np

from main_app.models import AGKategorie, Raum, Schueler, Aufenthalt, AG
from analysis_tool.models import ExtendedAGKategorie, AGHistorie, StudentAGCategoryAnalysis, StudentSessionBuffer

# Import existing utility functions
from analysis_tool.utils.compute_ag_category_metrics import (
    compute_correlation_matrix, 
    compute_relative_time_ratios,
    perform_regression_analysis,
    perform_cluster_analysis,
    compute_association_rules
)
from analysis_tool.utils.compute_room_metrics import (
    get_room_utilization,
    compute_room_spitzenzeiten,
    compute_room_historical_trend,
    compute_room_capacity_analysis,
    compute_room_nutzer_profile
)
from analysis_tool.utils.advanced_analytics import (
    compute_transition_probabilities,
    compute_student_diversity,
    compute_temporal_trends,
    compute_cooccurrence_network
)

@login_required(redirect_field_name="login")
def category_analysis_view(request, category_id):
    """
    View to display comprehensive analytics for a specific AG Kategorie.
    Uses existing utility functions from analysis_tool.utils.
    """
    # Get the category
    category = get_object_or_404(AGKategorie, id=category_id)
    
    # Use the ExtendedAGKategorie proxy model to access the additional analytics methods
    extended_category = ExtendedAGKategorie.objects.get(id=category_id)
    
    # Get utilization statistics from the extended model
    stats = extended_category.get_utilization_stats()
    
    # Get average statistics across all categories for comparison
    avg_stats = get_average_category_stats()
    
    # Total events for this category
    total_events = AGHistorie.objects.filter(ag_kategorie=category).count()
    
    # Get temporal distribution data using existing functions
    temporal_data = get_temporal_data(category)
    
    # Get correlation data with other categories
    correlation_data = get_correlation_data(category)
    
    # Get student analysis data
    student_data = get_student_analysis_data(category)
    
    # Get room usage analytics
    room_data = get_room_analytics(category)
    
    # Get category association rules (which categories are commonly used together)
    association_data = get_association_data(category)
    
    # Calculate trends
    trend_data = get_trend_data(category)
    
    # Compile all data for the template
    context = {
        'category': category,
        'stats': stats,
        'avg_stats': avg_stats,
        'total_events': total_events,
        
        # Temporal data
        'hourly_data': temporal_data['hourly_counts'],
        'peak_hours_start': temporal_data['peak_hours']['start'],
        'peak_hours_end': temporal_data['peak_hours']['end'],
        'weekday_data': temporal_data['weekday_counts'],
        'top_weekday': temporal_data['top_weekday'],
        
        # Trend data
        'utilization_dates': trend_data['dates'],
        'utilization_values': trend_data['values'],
        'utilization_trend': trend_data['trend'],
        
        # Student data
        'student_names': student_data['names'],
        'student_times': student_data['times'],
        'avg_student_stay': student_data['avg_stay'],
        'returning_visitors_percentage': student_data['returning_percentage'],
        'popular_classes': student_data['popular_classes'],
        'related_interests': student_data['related_interests'],
        
        # Correlation data
        'category_names': correlation_data['category_names'],
        'avg_durations': correlation_data['avg_durations'],
        'complementary_categories': correlation_data['complementary_categories'],
        'complementary_values': correlation_data['complementary_values'],
        'top_complementary': correlation_data['top_complementary'],
        
        # Room data
        'room_labels': room_data['labels'],
        'room_usage': room_data['usage'],
        'room_occupancy': room_data['occupancy'],
        'top_rooms': room_data['top_rooms'],
        'room_optimization_suggestions': room_data['suggestions'],
        
        # Global averages
        'avg_utilization_percentage': avg_stats['avg_utilization_percentage'],
    }
    
    return render(request, 'analysis/category_analysis.html', context)

def get_average_category_stats():
    """
    Calculates average statistics across all categories for comparison.
    """
    all_categories = AGKategorie.objects.all()
    
    # Use aggregate functions for efficiency
    avg_stats = {
        'avg_category_time': AGHistorie.objects.aggregate(avg=Avg('total_available_time'))['avg'] or 0,
        'avg_usage_time': AGHistorie.objects.aggregate(avg=Avg('actual_usage_time'))['avg'] or 0,
        'avg_utilization_percentage': AGHistorie.objects.aggregate(avg=Avg('utilization_percentage'))['avg'] or 0,
        'avg_fully_utilized_time': AGHistorie.objects.aggregate(
            avg=Avg(F('total_available_time') * F('fully_utilized_percentage') / 100)
        )['avg'] or 0,
        'avg_fully_utilized_count': AGHistorie.objects.aggregate(
            avg=Count('id', filter=Q(fully_utilized_percentage=100)) / Count('id') * 100
        )['avg'] if AGHistorie.objects.exists() else 0,
    }
    
    return avg_stats

def get_temporal_data(category):
    """
    Gets temporal distribution data (hourly, daily patterns) using the existing 
    compute_temporal_trends function.
    """
    # Try to use the existing function for hourly distribution
    try:
        temporal_trends = compute_temporal_trends()
        hourly_data = temporal_trends.get(category.name, {})
        if not hourly_data or len(hourly_data) == 0:
            # Fallback if the category isn't in the results
            hourly_data = pd.Series([0] * 24, index=range(24))
    except Exception as e:
        print(f"Error getting temporal trends: {e}")
        # Fallback to AGHistorie data
        hourly_data = get_hourly_distribution_from_histories(category)
    
    # Convert pandas Series to list if needed
    hourly_counts = hourly_data.tolist() if hasattr(hourly_data, 'tolist') else list(hourly_data.values())
    
    # Get weekday distribution
    weekday_counts = get_weekday_distribution_from_histories(category)
    
    # Find peak hours
    peak_hours = get_peak_hours(hourly_data)
    
    # Get top weekday
    weekdays = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag']
    top_weekday_idx = max(weekday_counts.items(), key=lambda x: x[1])[0] if weekday_counts else 0
    top_weekday = weekdays[top_weekday_idx] if 0 <= top_weekday_idx < len(weekdays) else 'Unbekannt'
    
    return {
        'hourly_counts': hourly_counts,
        'weekday_counts': list(weekday_counts.values()),
        'peak_hours': peak_hours,
        'top_weekday': top_weekday
    }

def get_hourly_distribution_from_histories(category):
    """
    Extracts hourly distribution from AGHistorie records if compute_temporal_trends fails.
    """
    histories = AGHistorie.objects.filter(ag_kategorie=category)
    hourly_counts = {i: 0 for i in range(24)}
    
    for history in histories:
        hour = history.zeitraum_start.hour
        hourly_counts[hour] += 1
    
    return hourly_counts

def get_weekday_distribution_from_histories(category):
    """
    Extracts weekday distribution from AGHistorie records.
    """
    histories = AGHistorie.objects.filter(ag_kategorie=category)
    weekday_counts = {i: 0 for i in range(5)}  # Monday to Friday
    
    for history in histories:
        weekday = history.zeitraum_start.weekday()
        if weekday < 5:  # Only count Monday to Friday
            weekday_counts[weekday] += 1
    
    return weekday_counts

def get_peak_hours(hourly_data):
    """
    Identifies the peak hours from hourly distribution data.
    """
    # Find the hours with the highest values
    sorted_hours = sorted(hourly_data.items(), key=lambda x: x[1], reverse=True) if isinstance(hourly_data, dict) else []
    
    if sorted_hours:
        peak_start = min(h for h, v in sorted_hours[:3])
        peak_end = max(h for h, v in sorted_hours[:3])
        return {'start': peak_start, 'end': peak_end}
    
    return {'start': 13, 'end': 15}  # Default if no data

def get_correlation_data(category):
    """
    Gets correlation data between this category and others using compute_correlation_matrix.
    """
    # Try to get correlation matrix from utility function
    try:
        corr_matrix = compute_correlation_matrix()
        
        # Check if we have data for this category
        if category.name in corr_matrix.columns:
            correlations = corr_matrix[category.name]
            # Sort by correlation strength
            correlations = correlations.sort_values(ascending=False)
            # Remove self-correlation
            correlations = correlations[correlations.index != category.name]
            
            # Get top correlated categories
            top_categories = correlations.head(5)
            
            return {
                'category_names': list(top_categories.index),
                'avg_durations': [30 + i*5 for i in range(len(top_categories))],  # Placeholder, replace with real data
                'complementary_categories': list(top_categories.index),
                'complementary_values': list(top_categories.values),
                'top_complementary': top_categories.index[0] if len(top_categories) > 0 else None
            }
    except Exception as e:
        print(f"Error getting correlation data: {e}")
    
    # Fallback to basic data
    other_categories = AGKategorie.objects.exclude(id=category.id)[:5]
    
    return {
        'category_names': [cat.name for cat in other_categories],
        'avg_durations': [30 + i*5 for i in range(len(other_categories))],
        'complementary_categories': [cat.name for cat in other_categories],
        'complementary_values': [10 + i*5 for i in range(len(other_categories))],
        'top_complementary': other_categories[0].name if other_categories else None
    }

def get_student_analysis_data(category):
    """
    Gets student participation data for this category, leveraging StudentAGCategoryAnalysis.
    """
    # Try to get data from StudentAGCategoryAnalysis
    analysis_entries = StudentAGCategoryAnalysis.objects.filter(ag_kategorie=category).order_by('-time_spent')[:10]
    
    if analysis_entries:
        student_names = []
        student_times = []
        
        for entry in analysis_entries:
            student = entry.student
            student_names.append(f"{student.user_id.vorname} {student.user_id.nachname}")
            student_times.append(round(entry.time_spent, 1))
        
        # Calculate average stay duration
        avg_stay = analysis_entries.aggregate(Avg('average_session_duration'))['average_session_duration__avg'] or 0
        avg_stay_minutes = avg_stay * 60  # Convert to minutes
        
        # Calculate returning visitors
        total_students = StudentAGCategoryAnalysis.objects.filter(ag_kategorie=category).count()
        multiple_visits = StudentAGCategoryAnalysis.objects.filter(ag_kategorie=category, frequency__gt=1).count()
        returning_percentage = (multiple_visits / total_students * 100) if total_students > 0 else 0
        
        # Get most common classes (needs modification based on your data model)
        all_students = StudentAGCategoryAnalysis.objects.filter(ag_kategorie=category).values_list('student', flat=True)
        class_distribution = Schueler.objects.filter(id__in=all_students).values('klasse').annotate(count=Count('id')).order_by('-count')
        popular_classes = ", ".join([c['klasse'] for c in class_distribution[:3]])
        
        # Get related interests using compute_cooccurrence_network
        try:
            cooccurrence = compute_cooccurrence_network()
            if category.name in cooccurrence.index:
                related = cooccurrence.loc[category.name].sort_values(ascending=False).head(3)
                related_interests = ", ".join(related.index)
            else:
                related_interests = "Keine Daten"
        except Exception as e:
            print(f"Error getting cooccurrence data: {e}")
            related_interests = "Sport, Kreativ, Natur"  # Fallback
        
        return {
            'names': student_names,
            'times': student_times,
            'avg_stay': avg_stay_minutes,
            'returning_percentage': returning_percentage,
            'popular_classes': popular_classes,
            'related_interests': related_interests
        }
    
    # Fallback to placeholder data
    return {
        'names': [f"Schüler {i}" for i in range(1, 6)],
        'times': [round(10 + i, 1) for i in range(5)],
        'avg_stay': 45.0,
        'returning_percentage': 65.0,
        'popular_classes': "3a, 4b, 2c",
        'related_interests': "Sport, Kreativ, Natur"
    }

def get_room_analytics(category):
    """
    Gets room usage analytics for this category using compute_room_metrics functions.
    """
    # Get rooms used for this category
    history_rooms = AGHistorie.objects.filter(ag_kategorie=category).values_list('raum', flat=True).distinct()
    rooms = Raum.objects.filter(id__in=history_rooms)
    
    room_labels = []
    room_usage = []
    room_metrics = []
    
    for room in rooms:
        # Use existing room analysis functions
        utilization = get_room_utilization(room.id)
        spitzenzeiten = compute_room_spitzenzeiten(room.id)
        capacity = compute_room_capacity_analysis(room.id)
        
        # Filter metrics for just this category
        category_usage = AGHistorie.objects.filter(raum=room, ag_kategorie=category).aggregate(
            total_time=Sum('total_available_time'),
            actual_usage=Sum('actual_usage_time'),
            avg_util=Avg('utilization_percentage')
        )
        
        room_labels.append(f"Raum {room.raum_nr}")
        usage_time = category_usage['actual_usage'] or 0
        room_usage.append(round(usage_time, 1))
        
        # Calculate peak times for this room/category
        if isinstance(spitzenzeiten, pd.Series):
            # For pandas Series
            if not spitzenzeiten.empty:
                peak_time = spitzenzeiten.idxmax()
            else:
                peak_time = 13
        else:
            # For dictionaries
            peak_time = max(spitzenzeiten.items(), key=lambda x: x[1])[0] if spitzenzeiten else 13
        peak_time_str = f"{peak_time}:00 - {peak_time+2}:00"
        
        # Add to room metrics
        usage_percentage = category_usage['avg_util'] or 0
        room_metrics.append({
            'number': room.raum_nr,
            'capacity': room.kapazitaet,
            'usage_percentage': round(usage_percentage, 1),
            'avg_occupancy': round(usage_time / utilization['total_available_time'] * room.kapazitaet if utilization['total_available_time'] > 0 else 0, 1),
            'peak_time': peak_time_str,
            'color': get_usage_color(usage_percentage)
        })
    
    # For room occupancy by hour, aggregate data across all rooms
    room_occupancy = [0] * 24
    for h in range(24):
        occupancy_values = []
        for room in rooms:
            try:
                spitzenzeiten = compute_room_spitzenzeiten(room.id)
                occupancy_values.append((spitzenzeiten.get(h, 0) / max(spitzenzeiten.values())) * 100 if spitzenzeiten else 0)
            except Exception:
                continue
        
        room_occupancy[h] = round(sum(occupancy_values) / len(occupancy_values), 1) if occupancy_values else 0
    
    # Generate optimization suggestions
    suggestions = generate_optimization_suggestions(rooms, room_metrics)
    
    return {
        'labels': room_labels,
        'usage': room_usage,
        'occupancy': room_occupancy,
        'top_rooms': sorted(room_metrics, key=lambda x: x['usage_percentage'], reverse=True),
        'suggestions': suggestions
    }

def get_usage_color(percentage):
    """Returns a color for the usage badge based on usage percentage."""
    if percentage > 80:
        return "#4caf50"  # Green for high usage
    elif percentage > 50:
        return "#ff9800"  # Orange for medium usage
    else:
        return "#90a4ae"  # Blue-grey for low usage

def generate_optimization_suggestions(rooms, room_metrics):
    """Generates room optimization suggestions based on usage patterns."""
    suggestions = []
    
    if not room_metrics:
        return ["Keine Daten für Optimierungsvorschläge verfügbar."]
    
    # Sort rooms by usage
    high_usage_rooms = [r for r in room_metrics if r['usage_percentage'] > 80]
    low_usage_rooms = [r for r in room_metrics if r['usage_percentage'] < 40]
    
    # Generate suggestions
    if high_usage_rooms:
        suggestions.append(
            f"Raum {high_usage_rooms[0]['number']} ist stark ausgelastet ({high_usage_rooms[0]['usage_percentage']}%). "
            f"Erwägen Sie zusätzliche Kapazitäten zu den Spitzenzeiten ({high_usage_rooms[0]['peak_time']})."
        )
    
    if low_usage_rooms:
        suggestions.append(
            f"Raum {low_usage_rooms[0]['number']} wird selten genutzt ({low_usage_rooms[0]['usage_percentage']}%). "
            f"Dieser Raum könnte für andere Kategorien verwendet werden."
        )
    
    # Capacity optimization
    overcapacity_rooms = [r for r in room_metrics if r['avg_occupancy'] > 0.9 * r['capacity']]
    undercapacity_rooms = [r for r in room_metrics if r['avg_occupancy'] < 0.4 * r['capacity']]
    
    if overcapacity_rooms:
        suggestions.append(
            f"Raum {overcapacity_rooms[0]['number']} ist nahezu voll ausgelastet. "
            f"Die durchschnittliche Belegung liegt bei {overcapacity_rooms[0]['avg_occupancy']} von {overcapacity_rooms[0]['capacity']} Plätzen."
        )
    
    if undercapacity_rooms:
        suggestions.append(
            f"Raum {undercapacity_rooms[0]['number']} ist überdimensioniert für die Nutzung. "
            f"Nur {undercapacity_rooms[0]['avg_occupancy']} von {undercapacity_rooms[0]['capacity']} Plätzen werden durchschnittlich genutzt."
        )
    
    return suggestions

def get_association_data(category):
    """Gets association rules for this category using compute_association_rules."""
    try:
        rules = compute_association_rules()
        
        # Filter rules where this category is an antecedent
        category_rules = rules[rules['antecedents'].apply(lambda x: category.name in x)]
        
        # Extract consequent categories and support values
        if not category_rules.empty:
            consequents = []
            supports = []
            
            for _, row in category_rules.iterrows():
                # Extract the first item from the frozenset
                consequent = list(row['consequents'])[0]
                consequents.append(consequent)
                supports.append(row['support'])
            
            return consequents, supports
    except Exception as e:
        print(f"Error getting association rules: {e}")
    
    return [], []

def get_trend_data(category):
    """
    Calculates utilization trends over time for this category.
    """
    # Get historical data sorted by date
    histories = AGHistorie.objects.filter(ag_kategorie=category).order_by('zeitraum_start')
    
    if not histories:
        # Return placeholder data if no histories exist
        return {
            'dates': [],
            'values': [],
            'trend': 0
        }
    
    # Group by date and calculate average utilization
    date_utilization = {}
    
    for history in histories:
        date = history.zeitraum_start.date()
        if date not in date_utilization:
            date_utilization[date] = []
        
        date_utilization[date].append(history.utilization_percentage)
    
    # Calculate daily averages
    dates = []
    values = []
    
    for date, utils in sorted(date_utilization.items()):
        dates.append(date.strftime('%Y-%m-%d'))
        values.append(round(sum(utils) / len(utils), 1) if utils else 0)
    
    # Calculate overall trend
    if len(values) >= 2:
        first_value = values[0]
        last_value = values[-1]
        days = len(dates)
        
        # Monthly trend (assuming 30 days in a month)
        monthly_trend = (last_value - first_value) * (30 / days) if days > 0 else 0
    else:
        monthly_trend = 0
    
    return {
        'dates': dates,
        'values': values,
        'trend': round(monthly_trend, 1)
    }