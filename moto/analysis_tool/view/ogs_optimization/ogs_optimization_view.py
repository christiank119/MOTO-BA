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
    perform_regression_analysis,
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
    1. Historical analysis of OGS utilization
    2. Current room planning optimization recommendations
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
        # Get current room usage from active Raum_Belegung
        current_belegungen = Raum_Belegung.objects.filter(
            zeitraum__endzeit__isnull=True  # Currently active
        ).select_related('raum', 'ag', 'zeitraum')
        
        if not current_belegungen.exists():
            # Fallback to all Raum_Belegung if no active ones
            current_belegungen = Raum_Belegung.objects.all().select_related('raum', 'ag', 'zeitraum')
            
        # Initialize room usage data
        rooms = Raum.objects.all()
        room_usage = {}
        
        for room in rooms:
            room_usage[room.id] = {
                'room': room,
                'current_belegungen': [],
                'historical_utilization': 0,
                'capacity_alert': False,
                'recommendation': None
            }
            
        # Add current belegungen to room data
        for belegung in current_belegungen:
            if belegung.raum_id in room_usage:
                room_usage[belegung.raum_id]['current_belegungen'].append(belegung)
        
        # Get historical utilization for each room
        for room_id, data in room_usage.items():
            try:
                utilization = get_room_utilization(room_id)
                data['historical_utilization'] = utilization.get('avg_utilization_percentage', 0)
                
                # Get capacity analysis
                capacity_time = compute_room_capacity_time_analysis(room_id)
                data['full_time_percentage'] = capacity_time.get('full_percentage', 0)
                
                # Check for capacity alerts
                if data['full_time_percentage'] > 80 and data['current_belegungen']:
                    data['capacity_alert'] = True
                    results['capacity_alerts'].append({
                        'room_number': data['room'].raum_nr,
                        'alert_type': 'overcapacity',
                        'utilization': round(data['historical_utilization'], 1),
                        'full_percentage': round(data['full_time_percentage'], 1),
                        'current_ags': [b.ag.name if hasattr(b, 'ag') and b.ag else "Unbekannt" for b in data['current_belegungen']]
                    })
            except Exception as e:
                print(f"Error analyzing room {room_id}: {e}")
        
        # Check for scheduling conflicts (overlapping times for high-demand AGs)
        scheduling_conflicts = []
        high_demand_ags = []
        
        # Identify high demand AGs from historical data
        for ag_historie in AGHistorie.objects.filter(fully_utilized_percentage__gt=80):
            if ag_historie.ag_name not in high_demand_ags:
                high_demand_ags.append(ag_historie.ag_name)
        
        # Check current belegungen for conflicts between high demand AGs
        belegungen_by_time = {}
        for belegung in current_belegungen:
            if not belegung.ag:
                continue
                
            if belegung.ag.name in high_demand_ags:
                key = f"{belegung.zeitraum.startzeit}-{belegung.zeitraum.endzeit}"
                if key not in belegungen_by_time:
                    belegungen_by_time[key] = []
                belegungen_by_time[key].append(belegung)
        
        # Check for overlaps where multiple high-demand AGs are at the same time
        for time_key, belegungen_list in belegungen_by_time.items():
            if len(belegungen_list) > 1:
                scheduling_conflicts.append({
                    'time': time_key,
                    'ags': [b.ag.name for b in belegungen_list if b.ag],
                    'rooms': [b.raum.raum_nr for b in belegungen_list if b.raum]
                })
                
        # Format room usage data for display
        formatted_room_usage = []
        for room_id, data in room_usage.items():
            room = data['room']
            belegungen = data['current_belegungen']
            
            usage_data = {
                'room_number': room.raum_nr,
                'capacity': room.kapazitaet,
                'current_assignment': len(belegungen),
                'current_ags': [b.ag.name if hasattr(b, 'ag') and b.ag else "Unbekannt" for b in belegungen],
                'historical_utilization': round(data['historical_utilization'], 1),
                'capacity_alert': data['capacity_alert']
            }
            
            formatted_room_usage.append(usage_data)
        
        # Sort by current assignment (descending)
        formatted_room_usage.sort(key=lambda x: (x['current_assignment'], x['historical_utilization']), reverse=True)
        
        # Generate room recommendations
        room_recommendations = []
        
        # 1. Identify underutilized rooms with capacity
        underutilized_rooms = [r for r in formatted_room_usage if r['historical_utilization'] < 50 and r['current_assignment'] < 2]
        
        # 2. Identify overutilized rooms
        overutilized_rooms = [r for r in formatted_room_usage if r['historical_utilization'] > 80 or r['capacity_alert']]
        
        # 3. Generate recommendations
        if underutilized_rooms and overutilized_rooms:
            for over_room in overutilized_rooms:
                for under_room in underutilized_rooms:
                    if not under_room['current_ags'] or len(under_room['current_ags']) < 2:
                        room_recommendations.append({
                            'type': 'reassignment',
                            'source_room': over_room['room_number'],
                            'target_room': under_room['room_number'],
                            'source_utilization': over_room['historical_utilization'],
                            'target_utilization': under_room['historical_utilization'],
                            'reason': f"Raum {over_room['room_number']} ist überbelegt, während Raum {under_room['room_number']} unterbelegt ist."
                        })
                        break
        
        # Add recommendations for scheduling conflicts
        for conflict in scheduling_conflicts:
            room_recommendations.append({
                'type': 'scheduling',
                'conflicting_ags': conflict['ags'],
                'time': conflict['time'],
                'rooms': conflict['rooms'],
                'reason': f"Die stark nachgefragten AGs {', '.join(conflict['ags'])} finden zeitgleich statt."
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
    Uses regression and clustering to predict outcomes with varying student numbers.
    """
    results = {
        'student_growth_scenarios': [],
        'interest_shift_scenarios': [],
        'capacity_predictions': {},
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
                'new_ags_needed': new_ags_needed
            })
            
        # Calculate capacity predictions using regression when available
        capacity_predictions = {}
        try:
            # Try to run regression for the most popular category
            if top_categories:
                top_category = top_categories[0]['name']
                regression_results = perform_regression_analysis(top_category, "Sport" if top_category != "Sport" else "Ernährung")
                
                if regression_results:
                    capacity_predictions = {
                        'category': top_category,
                        'coefficient': round(regression_results['coefficient'], 3),
                        'intercept': round(regression_results['intercept'], 3),
                        'score': round(regression_results['score'], 3),
                        'interpretation': get_regression_interpretation(regression_results)
                    }
        except Exception as e:
            print(f"Error running regression analysis: {e}")
            
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
        results['capacity_predictions'] = capacity_predictions
        results['cluster_results'] = cluster_results
        results['has_data'] = True
        
    except Exception as e:
        print(f"Error generating predictive analytics: {e}")
    
    return results


def get_regression_interpretation(regression_results):
    """Helper to interpret regression results in plain language"""
    coefficient = regression_results['coefficient']
    intercept = regression_results['intercept']
    score = regression_results['score']
    
    if score < 0.3:
        strength = "schwache"
    elif score < 0.6:
        strength = "mäßige"
    else:
        strength = "starke"
        
    if coefficient > 0:
        direction = "positive"
        explanation = f"Wenn die Zeit in der einen Kategorie um 1 Stunde steigt, steigt die Zeit in der anderen Kategorie um {coefficient:.2f} Stunden."
    else:
        direction = "negative"
        explanation = f"Wenn die Zeit in der einen Kategorie um 1 Stunde steigt, sinkt die Zeit in der anderen Kategorie um {abs(coefficient):.2f} Stunden."
        
    return f"Es besteht eine {strength} {direction} Korrelation. {explanation} Diese Beziehung erklärt {score*100:.1f}% der Varianz."


def get_capacity_recommendations():
    """
    Provides specific capacity optimization recommendations.
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
            
        total_capacity = sum(room.kapazitaet for room in rooms)
        average_capacity = total_capacity / rooms.count() if rooms.count() > 0 else 0
        
        # Count current students
        current_students = Schueler.objects.count()
        
        # Calculate overall capacity utilization
        capacity_ratio = current_students / total_capacity if total_capacity > 0 else 0
        capacity_percentage = capacity_ratio * 100
        
        # Get average attendance percentage
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
            elif utilization.get('avg_utilization_percentage', 0) < 30 and room.kapazitaet > average_capacity:
                # Large room is underutilized
                room_capacity_issues.append({
                    'room_number': room.raum_nr,
                    'capacity': room.kapazitaet,
                    'issue_type': 'undercapacity',
                    'percentage': round(utilization.get('avg_utilization_percentage', 0), 1),
                    'recommendation': f"Raum {room.raum_nr} ist mit {round(utilization.get('avg_utilization_percentage', 0), 1)}% deutlich unterbelegt. Erwägen Sie eine andere Raumzuweisung."
                })
                
        # Generate specific capacity recommendations
        specific_recommendations = []
        
        # 1. Overall capacity recommendation
        if capacity_percentage > 80:
            specific_recommendations.append({
                'type': 'overall',
                'severity': 'high',
                'title': 'Gesamtkapazität erhöhen',
                'recommendation': f"Die Gesamtkapazität ist zu {round(capacity_percentage, 1)}% ausgelastet. Neue Räume oder erweiterte Kapazitäten sind zu empfehlen."
            })
        elif capacity_percentage < 40:
            specific_recommendations.append({
                'type': 'overall',
                'severity': 'medium',
                'title': 'Gesamtkapazität optimieren',
                'recommendation': f"Die Gesamtkapazität ist nur zu {round(capacity_percentage, 1)}% ausgelastet. Prüfen Sie, ob einige Räume anderweitig genutzt werden können."
            })
            
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
                
        # 3. Recommendations for group balance
        # Check if there are imbalances in group sizes
        groups = Gruppe.objects.annotate(schueler_count=Count('schueler'))
        if groups.exists():
            avg_group_size = groups.aggregate(avg=Avg('schueler_count'))['avg'] or 0
            
            # Find groups that are much larger than average
            large_groups = groups.filter(schueler_count__gt=avg_group_size * 1.5)
            
            if large_groups.exists():
                group_names = [group.name for group in large_groups[:3]]  # Top 3
                specific_recommendations.append({
                    'type': 'group',
                    'severity': 'medium',
                    'title': 'Gruppengrößen ausbalancieren',
                    'recommendation': f"Die Gruppen {', '.join(group_names)} sind deutlich größer als der Durchschnitt. Erwägen Sie eine ausgewogenere Verteilung."
                })
                
        # 4. Time distribution recommendation
        # Are there AGs that could benefit from redistributed time slots?
        ag_histories = AGHistorie.objects.filter(utilization_percentage__gt=90)
        if ag_histories.exists():
            high_utilization_ags = set()
            for history in ag_histories:
                high_utilization_ags.add(history.ag_name)
                
            if high_utilization_ags:
                specific_recommendations.append({
                    'type': 'time',
                    'severity': 'medium',
                    'title': 'Zeitslots für beliebte AGs erweitern',
                    'recommendation': f"Die AGs {', '.join(list(high_utilization_ags)[:3])} sind stark ausgelastet. Zusätzliche Zeitslots könnten die Auslastung verbessern."
                })
                
        # Capacity summary
        capacity_summary = {
            'total_rooms': rooms.count(),
            'total_capacity': total_capacity,
            'current_students': current_students,
            'capacity_percentage': round(capacity_percentage, 1),
            'avg_attendance_percentage': round(avg_attendance_percentage, 1),
            'capacity_status': get_capacity_status(capacity_percentage)
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
        popular_categories = [c for c in category_status if c['status'] == 'überlastet' or c['status'] == 'beliebt']
        
        expansion_recommendations = []
        for category in popular_categories:
            expansion_recommendations.append({
                'category': category['name'],
                'reason': "Hohe Nachfrage",
                'utilization': category['utilization'],
                'recommendation': f"Erweitern Sie das Angebot in der Kategorie {category['name']} aufgrund der hohen Nachfrage."
            })
            
        # Check for potentially missing or underrepresented categories
        # Compare with common categories found in other OGS
        common_categories = ["Sport", "Ernährung", "Kunst", "Musik", "Naturwissenschaften", "Technik", "Sprachen", "Theater"]
        
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
    if percentage > 25 and utilization > 85:
        return "überlastet"
    elif percentage > 25:
        return "beliebt"
    elif percentage > 10:
        return "gut genutzt"
    elif percentage > 5:
        return "untergenutzt"
    else:
        return "unterrepräsentiert"