from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum, Count, F, Q, Max, Min
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from main_app.models import (
    AGKategorie, Raum, Schueler, Aufenthalt, AG, 
    Raum_Belegung, Zeitraum, Nutzer, Gruppe
)
from analysis_tool.models import (
    ExtendedAGKategorie, AGHistorie, StudentAGCategoryAnalysis,
    StudentSessionBuffer, StudentOverallAnalysis
)

# Import utility functions
from analysis_tool.utils.compute_ag_category_metrics import (
    compute_correlation_matrix,
    compute_relative_time_ratios,
    perform_cluster_analysis
)
from analysis_tool.utils.compute_room_metrics import (
    get_room_utilization,
    compute_room_spitzenzeiten,
    compute_room_historical_trend,
    compute_room_capacity_analysis,
    compute_room_capacity_time_analysis,
    compute_room_nutzer_profile
)
from analysis_tool.utils.advanced_analytics import (
    compute_transition_probabilities,
    compute_student_diversity,
    compute_temporal_trends
)


@login_required(redirect_field_name="login")
def ogs_optimization_view(request):
    """
    View to display comprehensive OGS optimization analytics with:
    1. Current room planning optimization recommendations
    2. Historical analysis of OGS utilization
    3. Predictive analytics for varying student numbers
    """
    # Get current date for context
    current_date = datetime.now().date()
    
    # Get historic analytics
    historical_data = get_historical_analytics()
    
    # Get current room planning optimization
    room_optimization = get_room_optimization()
    
    # Get predictive analytics
    predictive_data = get_predictive_analytics()
    
    # Get capacity optimization recommendations
    capacity_recommendations = get_capacity_recommendations()
    
    # Get AG category recommendations
    category_recommendations = get_category_recommendations()
    
    # Compile all data for the template
    context = {
        'current_date': current_date,
        'historical_data': historical_data,
        'room_optimization': room_optimization,
        'predictive_data': predictive_data,
        'capacity_recommendations': capacity_recommendations,
        'category_recommendations': category_recommendations,
    }
    
    return render(request, 'analysis/ogs_optimization.html', context)


def get_historical_analytics():
    """
    Analyzes historical data to identify patterns, trends, and inefficiencies.
    Returns structured historical analytics data.
    """
    # Initialize results dictionary
    results = {
        'utilization_trend': {
            'dates': [],
            'values': [],
            'trend': 0
        },
        'peak_hours': {},
        'category_popularity': [],
        'underutilized_rooms': [],
        'overutilized_rooms': [],
        'has_data': False
    }
    
    try:
        # Get historical utilization trend from AGHistorie
        histories = AGHistorie.objects.all().order_by('zeitraum_start')
        
        if not histories.exists():
            return results
            
        # Group by date and calculate overall utilization
        date_utilization = {}
        for history in histories:
            date = history.zeitraum_start.date()
            if date not in date_utilization:
                date_utilization[date] = {
                    'total_available': 0,
                    'actual_usage': 0
                }
            
            date_utilization[date]['total_available'] += history.total_available_time
            date_utilization[date]['actual_usage'] += history.actual_usage_time
        
        # Calculate daily utilization percentages
        dates = []
        values = []
        
        for date, data in sorted(date_utilization.items()):
            utilization = 0
            if data['total_available'] > 0:
                utilization = (data['actual_usage'] / data['total_available']) * 100
                
            dates.append(date.strftime('%Y-%m-%d'))
            values.append(round(utilization, 1))
        
        results['utilization_trend']['dates'] = dates
        results['utilization_trend']['values'] = values
        
        # Calculate trend if we have sufficient data
        if len(values) >= 2:
            first_value = values[0]
            last_value = values[-1]
            days = len(dates)
            
            # Monthly trend (assuming 30 days in a month)
            monthly_trend = (last_value - first_value) * (30 / days) if days > 0 else 0
            results['utilization_trend']['trend'] = round(monthly_trend, 1)
        
        # Get peak hours from all room usage data
        all_rooms = Raum.objects.all()
        hour_counts = [0] * 24
        
        for room in all_rooms:
            try:
                room_spitzenzeiten = compute_room_spitzenzeiten(room.id)
                for hour, count in enumerate(room_spitzenzeiten):
                    if isinstance(count, (int, float)):
                        hour_counts[hour] += count
            except Exception as e:
                print(f"Error computing peak hours for room {room.id}: {e}")
                continue
                
        # Find the peak hours (top 3)
        peak_hour_data = [(hour, count) for hour, count in enumerate(hour_counts)]
        peak_hour_data.sort(key=lambda x: x[1], reverse=True)
        
        peak_hours = peak_hour_data[:3]
        results['peak_hours'] = {
            'hours': [h for h, _ in peak_hours],
            'counts': [c for _, c in peak_hours],
        }
        
        # Get category popularity from StudentAGCategoryAnalysis
        category_data = {}
        for analysis in StudentAGCategoryAnalysis.objects.all():
            if analysis.ag_kategorie:
                cat_id = analysis.ag_kategorie.id
                if cat_id not in category_data:
                    category_data[cat_id] = {
                        'name': analysis.ag_kategorie.name,
                        'time_spent': 0,
                        'students': set()
                    }
                category_data[cat_id]['time_spent'] += analysis.time_spent
                category_data[cat_id]['students'].add(analysis.student.id)
        
        # Convert to list and add student count
        category_popularity = []
        for cat_id, data in category_data.items():
            category_popularity.append({
                'name': data['name'],
                'time_spent': round(data['time_spent'], 1),
                'student_count': len(data['students'])
            })
        
        # Sort by time spent
        category_popularity.sort(key=lambda x: x['time_spent'], reverse=True)
        results['category_popularity'] = category_popularity[:5]  # Top 5
        
        # Identify under and over utilized rooms
        room_usage = []
        for room in all_rooms:
            utilization = get_room_utilization(room.id)
            capacity_analysis = compute_room_capacity_analysis(room.id)
            capacity_time = compute_room_capacity_time_analysis(room.id)
            
            room_usage.append({
                'id': room.id,
                'number': room.raum_nr,
                'capacity': room.kapazitaet,
                'utilization': utilization.get('avg_utilization_percentage', 0),
                'full_capacity_percentage': capacity_time.get('full_percentage', 0)
            })
        
        # Sort and identify outliers
        room_usage.sort(key=lambda x: x['utilization'])
        
        # Under-utilized rooms (bottom 20%)
        underutilized_count = max(1, len(room_usage) // 5)
        results['underutilized_rooms'] = room_usage[:underutilized_count]
        
        # Over-utilized rooms (top 20%)
        results['overutilized_rooms'] = room_usage[-underutilized_count:]
        
        results['has_data'] = True
        
    except Exception as e:
        print(f"Error getting historical analytics: {e}")
    
    return results


def get_room_optimization():
    """
    Analyzes current room assignments and provides optimization recommendations.
    Focuses on current room utilization, capacity planning, and scheduling.
    """
    results = {
        'current_room_usage': [],
        'scheduling_conflicts': [],
        'room_recommendations': [],
        'capacity_alerts': [],
        'has_data': False
    }
    
    try:
        # Get all rooms
        rooms = Raum.objects.all()
        
        # Initialize room usage data
        room_usage = {}
        
        for room in rooms:
            # Current students in the room based on active Aufenthalt objects
            current_students = Aufenthalt.objects.filter(
                raum_id=room,
                zeitraum__endzeit__isnull=True  # Students currently in the room
            ).count()
            
            # Current room assignments (max is 1)
            current_belegung = Raum_Belegung.objects.filter(
                raum=room,
                zeitraum__endzeit__isnull=True  # Currently active
            ).first()
            
            # Historical utilization
            historical_utilization = get_room_utilization(room.id).get('avg_utilization_percentage', 0)
            
            # Calculate current utilization percentage based on capacity
            current_utilization = (current_students / room.kapazitaet * 100) if room.kapazitaet > 0 else 0
            
            ag_name = "Keine aktuelle AG" 
            if current_belegung and hasattr(current_belegung, 'ag') and current_belegung.ag:
                ag_name = current_belegung.ag.name
                
            room_usage[room.id] = {
                'room': room,
                'current_belegung': 1 if current_belegung else 0,
                'current_utilization': current_utilization,
                'current_students': current_students,
                'historical_utilization': historical_utilization,
                'current_ag': ag_name,
                'capacity_alert': current_utilization > 85 or historical_utilization > 85
            }
            
            # Check for capacity alerts
            if room_usage[room.id]['capacity_alert']:
                results['capacity_alerts'].append({
                    'room_number': room.raum_nr,
                    'alert_type': 'overcapacity',
                    'current_utilization': round(current_utilization, 1),
                    'historical_utilization': round(historical_utilization, 1),
                    'current_ag': ag_name
                })
            
        # Get all current AG belegungen
        current_belegungen = Raum_Belegung.objects.filter(
            zeitraum__endzeit__isnull=True
        ).select_related('raum', 'ag', 'zeitraum')
        
        # Check for scheduling conflicts (overlapping times for high-demand AGs)
        scheduling_conflicts = []
        high_demand_ags = []
        
        # Identify high demand AG categories from historical data
        high_demand_categories = set()
        for category in AGKategorie.objects.all():
            # Check if this category has high historical utilization
            category_analyses = StudentAGCategoryAnalysis.objects.filter(ag_kategorie=category)
            if category_analyses.exists() and category_analyses.count() > 5:  # Only consider categories with sufficient data
                high_demand_categories.add(category.id)
        
        # Check current belegungen for conflicts between high demand categories
        belegungen_by_time = {}
        for belegung in current_belegungen:
            if not belegung.ag or not belegung.ag.ag_kategorie:
                continue
                
            if belegung.ag.ag_kategorie.id in high_demand_categories:
                key = f"{belegung.zeitraum.startzeit}"
                if key not in belegungen_by_time:
                    belegungen_by_time[key] = []
                belegungen_by_time[key].append(belegung)
        
        # Check for overlaps where multiple high-demand AGs are at the same time
        for time_key, belegungen_list in belegungen_by_time.items():
            if len(belegungen_list) > 1:
                scheduling_conflicts.append({
                    'time': time_key,
                    'ags': [b.ag.ag_kategorie.name for b in belegungen_list if b.ag and b.ag.ag_kategorie],
                    'rooms': [b.raum.raum_nr for b in belegungen_list if b.raum]
                })
                
        # Format room usage data for display
        formatted_room_usage = []
        for room_id, data in room_usage.items():
            room = data['room']
            
            usage_data = {
                'room_number': room.raum_nr,
                'capacity': room.kapazitaet,
                'current_assignment': data['current_belegung'],
                'current_ag': data['current_ag'],
                'current_students': data['current_students'],
                'current_utilization': round(data['current_utilization'], 1),
                'historical_utilization': round(data['historical_utilization'], 1),
                'capacity_alert': data['capacity_alert']
            }
            
            formatted_room_usage.append(usage_data)
        
        # Sort by current utilization (descending)
        formatted_room_usage.sort(key=lambda x: x['current_utilization'], reverse=True)
        
        # Generate room recommendations
        room_recommendations = []
        
        # 1. Identify underutilized rooms with capacity
        underutilized_rooms = [r for r in formatted_room_usage if r['historical_utilization'] < 40 and r['current_utilization'] < 30]
        
        # 2. Identify overutilized rooms
        overutilized_rooms = [r for r in formatted_room_usage if r['historical_utilization'] > 75 or r['current_utilization'] > 85]
        
        # 3. Generate recommendations
        if underutilized_rooms and overutilized_rooms:
            for over_room in overutilized_rooms:
                for under_room in underutilized_rooms:
                    if under_room['current_assignment'] == 0:  # Only suggest empty rooms
                        room_recommendations.append({
                            'type': 'reassignment',
                            'source_room': over_room['room_number'],
                            'target_room': under_room['room_number'],
                            'source_historical_utilization': over_room['historical_utilization'],
                            'source_current_utilization': over_room['current_utilization'],
                            'target_historical_utilization': under_room['historical_utilization'],
                            'target_current_utilization': under_room['current_utilization'],
                            'reason': f"Raum {over_room['room_number']} ist überbelegt, während Raum {under_room['room_number']} unterbelegt ist."
                        })
                        break
        
        # Add recommendations for scheduling conflicts - focusing only on AG categories, not specific AGs
        for conflict in scheduling_conflicts:
            room_recommendations.append({
                'type': 'scheduling',
                'conflicting_categories': conflict['ags'],  # These are already category names
                'time': conflict['time'],
                'rooms': conflict['rooms'],
                'reason': f"Die stark nachgefragten AG-Kategorien {', '.join(conflict['ags'])} finden zeitgleich statt."
            })
        
        # Populate results
        results['current_room_usage'] = formatted_room_usage
        results['scheduling_conflicts'] = scheduling_conflicts
        results['room_recommendations'] = room_recommendations
        results['has_data'] = True
        
    except Exception as e:
        print(f"Error getting room optimization data: {e}")
    
    return results


def get_predictive_analytics():
    """
    Uses clustering to predict outcomes with varying student numbers.
    """
    results = {
        'student_growth_scenarios': [],
        'interest_shift_scenarios': [],
        'has_data': False
    }
    
    try:
        # Get current student count
        current_students = Schueler.objects.count()
        
        if current_students == 0:
            return results
            
        # Get current AG distribution from StudentAGCategoryAnalysis
        category_data = {}
        total_time_spent = 0
        
        for analysis in StudentAGCategoryAnalysis.objects.all():
            if analysis.ag_kategorie:
                cat_id = analysis.ag_kategorie.id
                if cat_id not in category_data:
                    category_data[cat_id] = {
                        'name': analysis.ag_kategorie.name,
                        'time_spent': 0,
                        'students': set(),
                        'percentage': 0
                    }
                category_data[cat_id]['time_spent'] += analysis.time_spent
                category_data[cat_id]['students'].add(analysis.student.id)
                total_time_spent += analysis.time_spent
                
        # Calculate percentages
        for cat_id in category_data:
            if total_time_spent > 0:
                category_data[cat_id]['percentage'] = category_data[cat_id]['time_spent'] / total_time_spent * 100
                
        # Get all rooms and their capacities
        rooms = Raum.objects.all()
        total_capacity = sum(room.kapazitaet for room in rooms)
        
        # Calculate average time per student
        avg_ogs_time = StudentOverallAnalysis.objects.aggregate(avg=Avg('total_ogs_time'))['avg'] or 0
        
        # Calculate current utilization from AGHistorie
        current_utilization = AGHistorie.objects.aggregate(avg=Avg('utilization_percentage'))['avg'] or 0
        
        # Generate growth scenarios (10%, 20%, 30% growth)
        growth_scenarios = []
        for growth_percent in [10, 20, 30]:
            new_students = int(current_students * (1 + growth_percent/100))
            additional_students = new_students - current_students
            
            # Simple linear prediction of increased utilization
            predicted_utilization = min(100, current_utilization * (1 + (growth_percent/100) * 0.8))
            
            # Will we have capacity issues?
            capacity_status = "ausreichend"
            if predicted_utilization > 85:
                capacity_status = "kritisch"
            elif predicted_utilization > 70:
                capacity_status = "begrenzt"
                
            # Calculate needed new spaces
            additional_capacity_needed = int(additional_students * avg_ogs_time * 0.3)
            
            growth_scenarios.append({
                'growth_percent': growth_percent,
                'new_student_count': new_students,
                'predicted_utilization': round(predicted_utilization, 1),
                'capacity_status': capacity_status,
                'additional_capacity_needed': additional_capacity_needed
            })
            
        # Generate interest shift scenarios 
        # (what if more students were interested in currently popular categories?)
        interest_shift_scenarios = []
        
        # Get top 3 categories by time spent
        top_categories = sorted(category_data.values(), key=lambda x: x['time_spent'], reverse=True)[:3]
        
        for category in top_categories:
            # What if interest in this category increased by 50%?
            current_percentage = category['percentage']
            new_percentage = min(100, current_percentage * 1.5)
            percentage_increase = new_percentage - current_percentage
            
            # Calculate impact on capacity
            capacity_impact = (percentage_increase / 100) * current_students * 0.3
            
            # Calculate needed new AG offerings
            new_ags_needed = max(1, int(capacity_impact / 15))  # Assume average AG size of 15
            
            interest_shift_scenarios.append({
                'category_name': category['name'],
                'current_percentage': round(current_percentage, 1),
                'new_percentage': round(new_percentage, 1),
                'capacity_impact': round(capacity_impact, 1),
                'new_ags_needed': new_ags_needed,
                'explanation': (
                    f"Wenn das Interesse an der Kategorie '{category['name']}' um 50% steigt, "
                    f"würde der Anteil von {round(current_percentage, 1)}% auf {round(new_percentage, 1)}% wachsen. "
                    f"Dies würde zu einem Mehrbedarf von etwa {round(capacity_impact, 1)} Plätzen führen, "
                    f"was ungefähr {new_ags_needed} neue AGs in dieser Kategorie erfordern würde, "
                    f"um eine gute Auslastung beizubehalten."
                )
            })
            
        # Try clustering analysis
        cluster_results = {}
        try:
            clustered_df = perform_cluster_analysis(n_clusters=min(3, current_students // 3)) if current_students >= 3 else None
            
            if clustered_df is not None and not clustered_df.empty and 'cluster' in clustered_df.columns:
                # Get cluster distribution
                cluster_counts = clustered_df['cluster'].value_counts()
                
                # Get category preferences for each cluster
                clusters = []
                
                for cluster_id in cluster_counts.index:
                    cluster_data = clustered_df[clustered_df['cluster'] == cluster_id]
                    
                    # Get average values for each category in this cluster
                    avg_values = cluster_data.drop('cluster', axis=1).mean()
                    
                    # Get top 3 categories for this cluster
                    top_categories = avg_values.sort_values(ascending=False).head(3)
                    
                    # Calculate percentage of students in this cluster
                    percentage = (cluster_counts[cluster_id] / clustered_df.shape[0]) * 100
                    
                    clusters.append({
                        'id': int(cluster_id),
                        'student_count': int(cluster_counts[cluster_id]),
                        'percentage': round(percentage, 1),
                        'top_categories': top_categories.index.tolist(),
                        'category_values': [round(v, 2) for v in top_categories.values]
                    })
                    
                cluster_results = {
                    'clusters': clusters,
                    'total_clusters': len(clusters)
                }
        except Exception as e:
            print(f"Error running cluster analysis: {e}")
            
        # Populate results
        results['student_growth_scenarios'] = growth_scenarios
        results['interest_shift_scenarios'] = interest_shift_scenarios
        results['cluster_results'] = cluster_results
        results['has_data'] = True
        
    except Exception as e:
        print(f"Error generating predictive analytics: {e}")
    
    return results


def get_improved_capacity_metrics():
    """
    Calculates capacity metrics based on AG offering times versus student demand.
    This provides a more accurate view of capacity than just summing room capacities.
    """
    results = {
        'available_student_hours': 0,
        'required_student_hours': 0,
        'capacity_percentage': 0,
        'capacity_status': 'unknown'
    }
    
    try:
        # Get all AG offerings with time slots (Raum_Belegung)
        from django.db.models import F, ExpressionWrapper, FloatField
        from django.db.models.functions import ExtractHour, ExtractMinute
        from main_app.models import Raum_Belegung, Schueler
        from analysis_tool.models import StudentOverallAnalysis
        import datetime
        
        # Calculate available capacity (supply side)
        # For each AG session, calculate duration × room capacity
        belegungen = Raum_Belegung.objects.filter(zeitraum__isnull=False, raum__isnull=False)
        
        # Sum up the available student-hours
        total_available_hours = 0
        daily_available_hours = 0
        
        for belegung in belegungen:
            if not belegung.zeitraum.startzeit or not belegung.zeitraum.endzeit:
                continue
                
            # Calculate duration in hours
            start_time = belegung.zeitraum.startzeit
            end_time = belegung.zeitraum.endzeit
            
            # Convert to datetime objects for calculation
            start_dt = datetime.datetime.combine(datetime.date.today(), start_time)
            end_dt = datetime.datetime.combine(datetime.date.today(), end_time)
            
            # Handle case where end time is on the next day
            if end_dt < start_dt:
                end_dt += datetime.timedelta(days=1)
                
            duration_hours = (end_dt - start_dt).total_seconds() / 3600
            
            # Multiply by room capacity
            if belegung.raum and hasattr(belegung.raum, 'kapazitaet'):
                room_capacity = belegung.raum.kapazitaet
            else:
                room_capacity = 0
                
            session_capacity = duration_hours * room_capacity
            total_available_hours += session_capacity
            
            # For daily average, consider typical weekly pattern
            # This is an approximation - ideally we'd analyze actual scheduling data
            daily_available_hours += session_capacity / 5  # Assuming 5-day week
            
        # Calculate required capacity (demand side)
        # Get number of students
        student_count = Schueler.objects.count()
        
        # Get average OGS time per student
        avg_ogs_time = StudentOverallAnalysis.objects.aggregate(
            avg_time=Avg('total_ogs_time')
        )['avg_time'] or 0
        
        # Total student-hours needed
        total_required_hours = student_count * avg_ogs_time
        daily_required_hours = total_required_hours / 5  # Assuming 5-day week
        
        # Calculate capacity percentage
        if daily_available_hours > 0:
            capacity_percentage = (daily_required_hours / daily_available_hours) * 100
        else:
            capacity_percentage = 0
            
        # Determine capacity status
        capacity_status = get_capacity_status(capacity_percentage)
        
        # Populate results
        results = {
            'available_student_hours': round(daily_available_hours, 1),
            'required_student_hours': round(daily_required_hours, 1),
            'capacity_percentage': round(capacity_percentage, 1),
            'capacity_status': capacity_status
        }
        
    except Exception as e:
        print(f"Error calculating improved capacity metrics: {e}")
        
    return results
    
# Update the capacity recommendations function to use the improved metrics
def get_capacity_recommendations():
    """
    Provides specific capacity optimization recommendations.
    Uses improved capacity calculation method.
    """
    results = {
        'capacity_summary': {},
        'room_capacity_issues': [],
        'specific_recommendations': [],
        'has_data': False
    }
    
    try:
        # Get all rooms and their capacities
        rooms = Raum.objects.all()
        
        if not rooms.exists():
            return results
            
        # Get improved capacity metrics
        improved_metrics = get_improved_capacity_metrics()
        
        # Count current students
        current_students = Schueler.objects.count()
        
        # Calculate average attendance percentage
        avg_attendance = Schueler.objects.filter(angemeldet=True).count() / current_students if current_students > 0 else 0
        avg_attendance_percentage = avg_attendance * 100
        
        # Identify rooms with capacity issues
        room_capacity_issues = []
        
        for room in rooms:
            # Get room utilization statistics
            utilization = get_room_utilization(room.id)
            capacity_analysis = compute_room_capacity_analysis(room.id)
            capacity_time = compute_room_capacity_time_analysis(room.id)
            
            # Check if room has capacity issues
            if capacity_time.get('full_percentage', 0) > 80:
                # Room is frequently at full capacity
                room_capacity_issues.append({
                    'room_number': room.raum_nr,
                    'capacity': room.kapazitaet,
                    'issue_type': 'overcapacity',
                    'percentage': round(capacity_time.get('full_percentage', 0), 1),
                    'recommendation': f"Raum {room.raum_nr} ist zu {round(capacity_time.get('full_percentage', 0), 1)}% der Zeit voll ausgelastet. Erwägen Sie, die Kapazität zu erhöhen oder Aktivitäten zu verlagern."
                })
            elif utilization.get('avg_utilization_percentage', 0) < 30:
                # Room is underutilized
                room_capacity_issues.append({
                    'room_number': room.raum_nr,
                    'capacity': room.kapazitaet,
                    'issue_type': 'undercapacity',
                    'percentage': round(utilization.get('avg_utilization_percentage', 0), 1),
                    'recommendation': f"Raum {room.raum_nr} ist mit {round(utilization.get('avg_utilization_percentage', 0), 1)}% deutlich unterbelegt. Erwägen Sie eine andere Raumzuweisung."
                })
                
        # Generate specific capacity recommendations
        specific_recommendations = []
        
        # 1. Overall capacity recommendation based on improved metrics
        capacity_percentage = improved_metrics['capacity_percentage']
        if capacity_percentage > 80:
            specific_recommendations.append({
                'type': 'overall',
                'severity': 'high',
                'title': 'Gesamtkapazität erhöhen',
                'recommendation': f"Die Gesamtkapazität ist zu {round(capacity_percentage, 1)}% ausgelastet. Mehr AGs oder erweiterte Zeitslots könnten nötig sein."
            })
        elif capacity_percentage < 40:
            specific_recommendations.append({
                'type': 'overall',
                'severity': 'medium',
                'title': 'Gesamtkapazität optimieren',
                'recommendation': f"Die Gesamtkapazität ist nur zu {round(capacity_percentage, 1)}% ausgelastet. Prüfen Sie, ob das AG-Angebot reduziert werden kann."
            })
            
        # Rest of the function remains the same...
        
        # 2. Recommendations for overcapacity rooms
        overcapacity_rooms = [r for r in room_capacity_issues if r['issue_type'] == 'overcapacity']
        if overcapacity_rooms:
            for room_data in overcapacity_rooms:
                specific_recommendations.append({
                    'type': 'room',
                    'severity': 'high',
                    'title': f"Raum {room_data['room_number']} ist überbelegt",
                    'recommendation': room_data['recommendation']
                })
                
        # Capacity summary using improved metrics
        capacity_summary = {
            'total_rooms': rooms.count(),
            'available_student_hours': improved_metrics['available_student_hours'],
            'required_student_hours': improved_metrics['required_student_hours'],
            'current_students': current_students,
            'capacity_percentage': improved_metrics['capacity_percentage'],
            'avg_attendance_percentage': round(avg_attendance_percentage, 1),
            'capacity_status': improved_metrics['capacity_status']
        }
        
        # Populate results
        results['capacity_summary'] = capacity_summary
        results['room_capacity_issues'] = room_capacity_issues
        results['specific_recommendations'] = specific_recommendations
        results['has_data'] = True
        
    except Exception as e:
        print(f"Error generating capacity recommendations: {e}")
    
    return results


def get_capacity_status(percentage):
    """Helper to get capacity status based on percentage"""
    if percentage > 85:
        return "kritisch"
    elif percentage > 70:
        return "begrenzt"
    elif percentage > 50:
        return "ausreichend"
    else:
        return "großzügig"


def get_category_recommendations():
    """
    Provides recommendations for AG category improvements.
    Analyzes which categories are popular, which are missing, and which could be expanded.
    """
    results = {
        'category_status': [],
        'expansion_recommendations': [],
        'new_category_recommendations': [],
        'diversification_recommendations': [],
        'has_data': False
    }
    
    try:
        # Get all categories
        categories = AGKategorie.objects.all()
        
        if not categories.exists():
            return results
            
        # Get category utilization from StudentAGCategoryAnalysis
        category_data = {}
        total_time_spent = 0
        
        for analysis in StudentAGCategoryAnalysis.objects.all():
            if analysis.ag_kategorie:
                cat_id = analysis.ag_kategorie.id
                if cat_id not in category_data:
                    category_data[cat_id] = {
                        'id': cat_id,
                        'name': analysis.ag_kategorie.name,
                        'time_spent': 0,
                        'students': set(),
                        'avg_session_duration': 0,
                        'sessions': 0
                    }
                category_data[cat_id]['time_spent'] += analysis.time_spent
                category_data[cat_id]['students'].add(analysis.student.id)
                category_data[cat_id]['avg_session_duration'] += analysis.average_session_duration
                category_data[cat_id]['sessions'] += analysis.frequency
                total_time_spent += analysis.time_spent
                
        # Calculate average session duration and normalize
        for cat_id in category_data:
            if category_data[cat_id]['sessions'] > 0:
                category_data[cat_id]['avg_session_duration'] /= category_data[cat_id]['sessions']
                
            category_data[cat_id]['student_count'] = len(category_data[cat_id]['students'])
            category_data[cat_id]['percentage'] = (category_data[cat_id]['time_spent'] / total_time_spent * 100) if total_time_spent > 0 else 0
                
        # Generate category status information
        category_status = []
        
        for cat_id, data in category_data.items():
            # Get actual AGHistorie data if available
            historie_data = AGHistorie.objects.filter(ag_kategorie_id=cat_id)
            avg_utilization = historie_data.aggregate(avg=Avg('utilization_percentage'))['avg'] or 0
            
            status = {
                'name': data['name'],
                'student_count': data['student_count'],
                'time_spent': round(data['time_spent'], 1),
                'percentage': round(data['percentage'], 1),
                'avg_session_duration': round(data['avg_session_duration'] * 60, 1),  # Convert to minutes
                'utilization': round(avg_utilization, 1),
                'status': get_category_status(data['percentage'], avg_utilization)
            }
            
            category_status.append(status)
            
        # Sort by percentage (descending)
        category_status.sort(key=lambda x: x['percentage'], reverse=True)
        
        # Generate expansion recommendations for popular categories
        # Only recommend expansion for categories with utilization above 50%
        popular_categories = [c for c in category_status if c['utilization'] > 50]
        
        expansion_recommendations = []
        for category in popular_categories:
            expansion_recommendations.append({
                'category': category['name'],
                'reason': "Hohe Nachfrage",
                'utilization': category['utilization'],
                'recommendation': f"Erweitern Sie das Angebot in der Kategorie {category['name']} aufgrund der hohen Nachfrage (Auslastung: {category['utilization']}%)."
            })
            
        # Check for potentially missing or underrepresented categories
        # Compare with common categories found in other OGS
        common_categories = list(AGKategorie.objects.values_list('name', flat=True))
        
        existing_categories = {c['name'].lower() for c in category_status}
        missing_categories = []
        
        for common_cat in common_categories:
            if not any(common_cat.lower() in cat_name for cat_name in existing_categories):
                missing_categories.append(common_cat)
                
        new_category_recommendations = []
        for missing_cat in missing_categories:
            new_category_recommendations.append({
                'category': missing_cat,
                'reason': "Fehlt im Angebot",
                'recommendation': f"Erwägen Sie die Einführung der Kategorie {missing_cat}, die häufig in OGS-Angeboten vertreten ist."
            })
            
        # Generate diversification recommendations
        # If too much time is spent in a few categories, suggest diversification
        if len(category_status) >= 2:
            top_two_percentage = category_status[0]['percentage'] + category_status[1]['percentage']
            
            if top_two_percentage > 60:
                diversification_recommendations = [{
                    'categories': [category_status[0]['name'], category_status[1]['name']],
                    'percentage': round(top_two_percentage, 1),
                    'recommendation': f"Das Angebot konzentriert sich stark auf {category_status[0]['name']} und {category_status[1]['name']} ({round(top_two_percentage, 1)}% der Zeit). Eine größere Vielfalt könnte die Schülerinteressen besser abdecken."
                }]
            else:
                # Check for very low diversity categories
                low_diversity = [c for c in category_status if c['percentage'] < 5 and c['status'] == 'unterrepräsentiert']
                
                if low_diversity:
                    cat_names = [c['name'] for c in low_diversity[:3]]  # Top 3
                    diversification_recommendations = [{
                        'categories': cat_names,
                        'percentage': sum(c['percentage'] for c in low_diversity[:3]),
                        'recommendation': f"Die Kategorien {', '.join(cat_names)} sind stark unterrepräsentiert. Überlegen Sie, deren Angebot zu erweitern oder zu verbessern."
                    }]
                else:
                    diversification_recommendations = []
        else:
            diversification_recommendations = []
            
        # Populate results
        results['category_status'] = category_status
        results['expansion_recommendations'] = expansion_recommendations
        results['new_category_recommendations'] = new_category_recommendations
        results['diversification_recommendations'] = diversification_recommendations
        results['has_data'] = True
        
    except Exception as e:
        print(f"Error generating category recommendations: {e}")
    
    return results


def get_category_status(percentage, utilization):
    """Helper to determine category status based on metrics"""
    if percentage > 25 and utilization > 75:
        return "überlastet"
    elif percentage > 25:
        return "beliebt"
    elif percentage > 10:
        return "gut genutzt"
    elif percentage > 5:
        return "untergenutzt"
    else:
        return "unterrepräsentiert"