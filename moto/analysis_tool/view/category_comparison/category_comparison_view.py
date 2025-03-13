from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import pandas as pd
import numpy as np
import json
from main_app.models import AGKategorie
from analysis_tool.models import StudentAGCategoryAnalysis, StudentSessionBuffer, StudentOverallAnalysis

# Import utility functions
from analysis_tool.utils.compute_ag_category_metrics import (
    compute_correlation_matrix,
    compute_association_rules,
    perform_cluster_analysis,
    compute_relative_time_ratios
)
from analysis_tool.utils.advanced_analytics import (
    compute_transition_probabilities,
    compute_cooccurrence_network,
    compute_temporal_trends
)

# Expose the function for import in views.py
__all__ = ['category_comparison_view']

@login_required(redirect_field_name="login")
def category_comparison_view(request):
    """
    View to analyze and visualize relationships between different AG categories.
    Focuses on correlations, transitions, clusters, and associations.
    """
    # Get all categories
    categories = AGKategorie.objects.all()
    
    # Compute correlation matrix
    correlation_data = get_correlation_data()
    
    # Compute transition probabilities
    transition_data = get_transition_data()
    
    # Compute co-occurrence network
    cooccurrence_data = get_cooccurrence_data()
    
    # Compute association rules
    association_data = get_association_data()
    
    # Compute cluster analysis
    cluster_data = get_cluster_data()
    
    # Compute temporal patterns across categories
    temporal_data = get_temporal_data()
    
    # Generate key insights for overview page
    key_insights = generate_key_insights(
        correlation_data, 
        transition_data, 
        cooccurrence_data, 
        temporal_data, 
        association_data
    )
    
    # Prepare context for template
    context = {
        'categories': categories,
        'correlation_data': correlation_data,
        'transition_data': transition_data,
        'cooccurrence_data': cooccurrence_data,
        'association_data': association_data,
        'cluster_data': cluster_data,
        'temporal_data': temporal_data,
        'key_insights': key_insights
    }
    
    return render(request, 'analysis/category_comparison.html', context)

def generate_key_insights(correlation_data, transition_data, cooccurrence_data, temporal_data, association_data):
    """
    Generates key insights from all the analysis data for the overview tab.
    Returns a dict with prioritized insights across all analysis types.
    """
    insights = {
        'highlights': [],
        'recommendations': [],
        'warnings': [],
        'has_data': False
    }
    
    # Count how many data sources we have
    data_sources = 0
    
    # Process correlation insights
    if correlation_data.get('has_data') and correlation_data.get('strongest_correlations'):
        data_sources += 1
        # Get top correlation
        top_correlation = correlation_data['strongest_correlations'][0] if correlation_data['strongest_correlations'] else None
        if top_correlation and top_correlation[2] > 0.7:  # Strong correlation
            insights['highlights'].append({
                'type': 'correlation',
                'title': 'Starke Kategoriekorrelation',
                'description': f'"{top_correlation[0]}" und "{top_correlation[1]}" werden sehr häufig von denselben Schülern besucht (Korrelation: {top_correlation[2]:.2f}).',
                'importance': top_correlation[2],
                'actionable': f'Erwägen Sie, diese Kategorien zeitlich oder räumlich näher zusammen anzubieten.'
            })
            
        # Look for negative correlations (they might be important too)
        negative_cors = []
        for i, row in enumerate(correlation_data['matrix']):
            for j, val in enumerate(row):
                if i < j and val < -0.5:  # Only check upper triangle and significant negative correlations
                    negative_cors.append((
                        correlation_data['categories'][i],
                        correlation_data['categories'][j],
                        val
                    ))
        
        if negative_cors:
            # Sort by strongest negative correlation
            negative_cors.sort(key=lambda x: x[2])
            top_negative = negative_cors[0]
            insights['warnings'].append({
                'type': 'correlation',
                'title': 'Konkurrierende Kategorien',
                'description': f'"{top_negative[0]}" und "{top_negative[1]}" werden selten von denselben Schülern besucht (Korrelation: {top_negative[2]:.2f}).',
                'importance': abs(top_negative[2]),
                'actionable': f'Diese Kategorien könnten konkurrierende Interessen ansprechen oder zeitlich überlappen.'
            })
    
    # Process transition insights
    if transition_data.get('has_data') and transition_data.get('top_transitions'):
        data_sources += 1
        top_transition = transition_data['top_transitions'][0] if transition_data['top_transitions'] else None
        if top_transition and top_transition[2] > 20:  # Significant transition probability
            insights['highlights'].append({
                'type': 'transition',
                'title': 'Häufiger Kategorienwechsel',
                'description': f'Schüler wechseln besonders häufig von "{top_transition[0]}" zu "{top_transition[1]}" (Wahrscheinlichkeit: {top_transition[2]:.1f}%).',
                'importance': top_transition[2] / 100,
                'actionable': f'Diese Kategorien könnten zeitlich nacheinander angeboten werden.'
            })
    
    # Process co-occurrence insights
    if cooccurrence_data.get('has_data') and cooccurrence_data.get('top_cooccurrences'):
        data_sources += 1
        top_cooc = cooccurrence_data['top_cooccurrences'][0] if cooccurrence_data['top_cooccurrences'] else None
        if top_cooc and top_cooc[2] > 10:  # Significant co-occurrence
            insights['highlights'].append({
                'type': 'cooccurrence',
                'title': 'Beliebte Kategorienkombination',
                'description': f'"{top_cooc[0]}" und "{top_cooc[1]}" werden häufig am selben Tag besucht ({top_cooc[2]:.0f} mal).',
                'importance': min(1.0, top_cooc[2] / 50),  # Normalize importance
                'actionable': f'Diese Kategorien könnten an denselben Tagen angeboten werden.'
            })
    
    # Process temporal insights
    if temporal_data.get('has_data') and temporal_data.get('distinctive_patterns'):
        data_sources += 1
        # Find categories with very distinctive time patterns
        distinctive = temporal_data['distinctive_patterns'][0] if temporal_data['distinctive_patterns'] else None
        if distinctive and distinctive.get('peak_value', 0) > 25:  # Very peaked distribution
            peak_hour = distinctive.get('peak_hour', 12)
            peak_time = f"{peak_hour}:00"
            insights['recommendations'].append({
                'type': 'temporal',
                'title': 'Zeitliche Präferenz',
                'description': f'"{distinctive.get("category", "")}" wird besonders stark um {peak_time} Uhr genutzt ({distinctive.get("peak_value", 0):.1f}% der Aktivität).',
                'importance': distinctive.get('peak_value', 0) / 100,
                'actionable': f'Stellen Sie sicher, dass zu dieser Zeit ausreichend Kapazitäten vorhanden sind.'
            })
    
    # Process association rule insights
    if association_data.get('has_data') and association_data.get('rules'):
        data_sources += 1
        # Find high lift rules (strong associations)
        high_lift_rules = [rule for rule in association_data['rules'] if rule.get('lift', 0) > 1.5]
        if high_lift_rules:
            top_rule = high_lift_rules[0]
            insights['recommendations'].append({
                'type': 'association',
                'title': 'Starke Kategorienverknüpfung',
                'description': f'Wenn Schüler "{top_rule.get("antecedents", "")}" besuchen, nehmen sie mit {top_rule.get("confidence", 0)*100:.1f}% Wahrscheinlichkeit auch an "{top_rule.get("consequents", "")}" teil.',
                'importance': top_rule.get('lift', 0) / 3,  # Normalize importance
                'actionable': f'Diese Verbindung könnte für Empfehlungen oder Stundenplangestaltung genutzt werden.'
            })
    
    # Get overall category popularity data
    popular_categories = get_popular_categories()
    if popular_categories:
        insights['highlights'].append({
            'type': 'popularity',
            'title': 'Beliebteste AG-Kategorie',
            'description': f'"{popular_categories[0]["name"]}" ist die am häufigsten besuchte Kategorie mit {popular_categories[0]["students_count"]} Schülern.',
            'importance': 0.8,
            'actionable': f'Erwägen Sie, das Angebot in dieser Kategorie zu erweitern oder ähnliche Angebote zu schaffen.'
        })
    
    # Sort all insights by importance
    insights['highlights'].sort(key=lambda x: x['importance'], reverse=True)
    insights['recommendations'].sort(key=lambda x: x['importance'], reverse=True)
    insights['warnings'].sort(key=lambda x: x['importance'], reverse=True)
    
    # Limit to top 3 in each category for better overview
    insights['highlights'] = insights['highlights'][:3]
    insights['recommendations'] = insights['recommendations'][:3]
    insights['warnings'] = insights['warnings'][:2]
    
    insights['has_data'] = data_sources >= 2  # We have enough data for meaningful insights
    
    return insights

def get_popular_categories():
    """
    Gets the most popular AG categories based on StudentAGCategoryAnalysis data.
    """
    try:
        # Count unique students per category
        category_counts = {}
        
        # Get all category analyses
        analyses = StudentAGCategoryAnalysis.objects.all()
        
        for analysis in analyses:
            if analysis.ag_kategorie:
                category_id = analysis.ag_kategorie.id
                category_name = analysis.ag_kategorie.name
                
                if category_id not in category_counts:
                    category_counts[category_id] = {
                        'name': category_name,
                        'students_count': 0,
                        'total_time': 0
                    }
                
                category_counts[category_id]['students_count'] += 1
                category_counts[category_id]['total_time'] += analysis.time_spent
        
        # Convert to list and sort by popularity
        popular_categories = [v for k, v in category_counts.items()]
        popular_categories.sort(key=lambda x: x['students_count'], reverse=True)
        
        return popular_categories[:5]  # Return top 5
    except Exception as e:
        print(f"Error getting popular categories: {e}")
        return []

def get_correlation_data():
    """
    Gets correlation data between categories using compute_correlation_matrix.
    Returns data formatted for a heatmap visualization.
    """
    try:
        corr_matrix = compute_correlation_matrix()
        
        if corr_matrix.empty:
            return {
                'categories': [],
                'matrix': [],
                'has_data': False
            }
            
        # Format data for visualization
        categories = corr_matrix.columns.tolist()
        matrix = []
        
        for i, category in enumerate(categories):
            row = []
            for j, other_category in enumerate(categories):
                value = corr_matrix.iloc[i, j]
                # Convert NaN to 0 and ensure Python native float
                row.append(0.0 if pd.isna(value) else float(value))
            matrix.append(row)
            
        # Find strongest positive correlations for insights
        strongest_correlations = []
        for i in range(len(categories)):
            for j in range(i+1, len(categories)):  # Only look at upper triangle to avoid duplicates
                value = matrix[i][j]
                if value > 0.3:  # Include moderately positive correlations
                    strongest_correlations.append((categories[i], categories[j], value))
        
        # Sort by correlation strength
        strongest_correlations.sort(key=lambda x: x[2], reverse=True)
        
        # Generate color-coded insights
        correlation_insights = []
        for cat1, cat2, value in strongest_correlations[:5]:  # Top 5 correlations
            # Determine the significance level
            if value > 0.8:
                significance = "sehr stark"
                color = "#1b5e20"  # Dark green
            elif value > 0.6:
                significance = "stark"
                color = "#2e7d32"  # Medium green
            elif value > 0.4:
                significance = "moderat"
                color = "#388e3c"  # Light green
            else:
                significance = "leicht"
                color = "#66bb6a"  # Very light green
                
            correlation_insights.append({
                'category1': cat1,
                'category2': cat2,
                'value': value,
                'significance': significance,
                'color': color,
                'interpretation': f'Schüler, die viel Zeit in "{cat1}" verbringen, verbringen meist auch viel Zeit in "{cat2}".'
            })
        
        return {
            'categories': categories,
            'matrix': matrix,
            'strongest_correlations': strongest_correlations[:5],  # Top 5 correlations
            'correlation_insights': correlation_insights,
            'has_data': True
        }
    except Exception as e:
        print(f"Error computing correlation matrix: {e}")
        return {
            'categories': [],
            'matrix': [],
            'has_data': False,
            'error': str(e)
        }

def get_transition_data():
    """
    Gets transition probability data between categories using compute_transition_probabilities.
    Returns data formatted for visualization.
    """
    try:
        transitions = compute_transition_probabilities()
        
        if not transitions:
            return {
                'nodes': [],
                'links': [],
                'has_data': False
            }
            
        # Format data for visualization
        # First, collect all unique categories
        all_categories = set()
        for from_cat, to_cat in transitions.keys():
            all_categories.add(from_cat)
            all_categories.add(to_cat)
        
        all_categories = list(all_categories)
            
        # Create a map from category names to indices
        cat_to_idx = {cat: i for i, cat in enumerate(all_categories)}
        
        links = []
        for (from_cat, to_cat), prob in transitions.items():
            if from_cat != to_cat:  # Skip self-transitions for clarity
                links.append({
                    "source": cat_to_idx[from_cat],
                    "target": cat_to_idx[to_cat],
                    "value": prob * 100  # Scale for better visualization
                })
        
        # Find top transitions
        sorted_links = sorted(links, key=lambda x: x['value'], reverse=True)
        top_transitions = []
        for link in sorted_links[:5]:  # Top 5 transitions
            from_cat = all_categories[link['source']]
            to_cat = all_categories[link['target']]
            prob_value = link['value']
            
            # Determine significance and color coding
            if prob_value > 30:
                significance = "sehr häufig"
                color = "#1b5e20"  # Dark green
            elif prob_value > 20:
                significance = "häufig"
                color = "#2e7d32"  # Medium green
            elif prob_value > 10:
                significance = "gelegentlich"
                color = "#388e3c"  # Light green
            else:
                significance = "selten"
                color = "#66bb6a"  # Very light green
                
            top_transitions.append((
                from_cat, 
                to_cat, 
                prob_value,
                significance,
                color
            ))
        
        return {
            'nodes': all_categories,
            'links': links,
            'top_transitions': top_transitions,
            'has_data': True
        }
    except Exception as e:
        print(f"Error computing transition probabilities: {e}")
        return {
            'nodes': [],
            'links': [],
            'has_data': False,
            'error': str(e)
        }

def get_cooccurrence_data():
    """
    Gets co-occurrence network data using compute_cooccurrence_network.
    Returns data formatted for a network graph visualization.
    """
    try:
        cooccurrence_df = compute_cooccurrence_network()
        
        if cooccurrence_df.empty:
            return {
                'nodes': [],
                'links': [],
                'has_data': False
            }
            
        # Format data for visualization (network graph)
        categories = cooccurrence_df.columns.tolist()
        
        # Create nodes list
        nodes = [{"id": cat, "group": 1} for cat in categories]
        
        # Create links list (only include significant connections)
        links = []
        top_cooccurrences = []
        
        for i, from_cat in enumerate(categories):
            for j, to_cat in enumerate(categories):
                if i < j:  # Avoid duplicates and self-links
                    weight = float(cooccurrence_df.iloc[i, j])
                    if weight > 0:  # Only include non-zero weights
                        links.append({
                            "source": from_cat,
                            "target": to_cat,
                            "value": weight
                        })
                        
                        # Determine significance level
                        if weight > 30:
                            significance = "sehr häufig"
                            color = "#1b5e20"  # Dark green
                        elif weight > 20:
                            significance = "häufig"
                            color = "#2e7d32"  # Medium green
                        elif weight > 10:
                            significance = "gelegentlich"
                            color = "#388e3c"  # Light green
                        else:
                            significance = "selten"
                            color = "#66bb6a"  # Very light green
                            
                        top_cooccurrences.append((
                            from_cat, 
                            to_cat, 
                            weight, 
                            significance, 
                            color
                        ))
        
        # Sort by weight and get top co-occurrences
        top_cooccurrences.sort(key=lambda x: x[2], reverse=True)
        
        return {
            'nodes': nodes,
            'links': links,
            'top_cooccurrences': top_cooccurrences[:5],  # Top 5 co-occurrences
            'has_data': True
        }
    except Exception as e:
        print(f"Error computing cooccurrence network: {e}")
        return {
            'nodes': [],
            'links': [],
            'has_data': False,
            'error': str(e)
        }

def get_association_data():
    """
    Gets association rules data using compute_association_rules.
    Returns data formatted for a table or visualization.
    """
    try:
        rules = compute_association_rules(min_support=0.05, min_confidence=0.3)
        
        if rules.empty:
            return {
                'rules': [],
                'has_data': False
            }
            
        # Format data for visualization (table)
        formatted_rules = []
        
        for _, rule in rules.iterrows():
            antecedents = list(rule['antecedents'])
            consequents = list(rule['consequents'])
            
            # Convert frozensets to lists for JSON serialization
            
            # Determine significance level based on lift
            lift_value = float(rule['lift'])
            if lift_value > 3:
                significance = "sehr stark"
                color = "#1b5e20"  # Dark green
            elif lift_value > 2:
                significance = "stark"
                color = "#2e7d32"  # Medium green
            elif lift_value > 1.5:
                significance = "moderat"
                color = "#388e3c"  # Light green
            else:
                significance = "leicht"
                color = "#66bb6a"  # Very light green
                
            formatted_rules.append({
                "antecedents": ", ".join(antecedents),
                "consequents": ", ".join(consequents),
                "support": float(rule['support']),
                "confidence": float(rule['confidence']),
                "lift": lift_value,
                "significance": significance,
                "color": color
            })
            
        # Sort by lift (indicating strength of the association)
        formatted_rules.sort(key=lambda x: x['lift'], reverse=True)
        
        return {
            'rules': formatted_rules[:10],  # Top 10 rules
            'has_data': True
        }
    except Exception as e:
        print(f"Error computing association rules: {e}")
        return {
            'rules': [],
            'has_data': False,
            'error': str(e)
        }

def get_cluster_data():
    """
    Gets cluster analysis data using perform_cluster_analysis.
    Returns data formatted for visualization.
    """
    try:
        clustered_df = perform_cluster_analysis(n_clusters=3)
        
        if clustered_df.empty:
            return {
                'clusters': [],
                'has_data': False
            }
            
        # Format data for visualization
        cluster_profiles = []
        
        # Check if 'cluster' column exists
        if 'cluster' in clustered_df.columns:
            for cluster_id in clustered_df['cluster'].unique():
                cluster_data = clustered_df[clustered_df['cluster'] == cluster_id]
                
                # Get average values for each category in this cluster
                avg_values = cluster_data.drop('cluster', axis=1).mean()
                
                # Get top categories for this cluster
                top_categories = avg_values.sort_values(ascending=False).head(5)
                
                # Create a descriptive name for this cluster
                if len(top_categories) > 0:
                    top_cat = top_categories.index[0]
                    if len(top_categories) > 1:
                        second_cat = top_categories.index[1]
                        cluster_name = f"Gruppe '{top_cat} & {second_cat}'"
                    else:
                        cluster_name = f"Gruppe '{top_cat}'"
                else:
                    cluster_name = f"Gruppe {cluster_id+1}"
                
                cluster_profiles.append({
                    "cluster_id": int(cluster_id),
                    "cluster_name": cluster_name,
                    "size": len(cluster_data),
                    "top_categories": top_categories.index.tolist(),
                    "category_values": top_categories.values.tolist()
                })
        
        return {
            'clusters': cluster_profiles,
            'has_data': True if cluster_profiles else False
        }
    except Exception as e:
        print(f"Error performing cluster analysis: {e}")
        return {
            'clusters': [],
            'has_data': False,
            'error': str(e)
        }

def get_temporal_data():
    """
    Gets temporal distribution data for all categories.
    Shows when different categories are used throughout the day.
    """
    try:
        temporal_trends = compute_temporal_trends()
        
        if not temporal_trends:
            return {
                'categories': [],
                'hourly_data': [],
                'has_data': False
            }
        
        # Format data for visualization
        categories = list(temporal_trends.keys())
        hourly_data = []
        
        for cat in categories:
            cat_data = temporal_trends[cat]
            
            # If it's a pandas Series, convert to list
            if hasattr(cat_data, 'tolist'):
                hour_values = cat_data.tolist()
            else:
                # Try to convert dict to list
                hour_values = [cat_data.get(h, 0) for h in range(24)]
            
            # Normalize to percentages
            total = sum(hour_values)
            if total > 0:
                normalized = [v / total * 100 for v in hour_values]
            else:
                normalized = [0] * 24
            
            hourly_data.append({
                'category': cat,
                'values': normalized
            })
        
        # Find categories with distinctive patterns
        distinctive_patterns = []
        for cat_data in hourly_data:
            # Find peak hour
            peak_hour = cat_data['values'].index(max(cat_data['values']))
            # If the peak is pronounced (more than 15% of activity in one hour)
            if cat_data['values'][peak_hour] > 15:
                # Determine significance level
                peak_value = cat_data['values'][peak_hour]
                if peak_value > 30:
                    significance = "sehr ausgeprägt"
                    color = "#1b5e20"  # Dark green
                elif peak_value > 25:
                    significance = "ausgeprägt"
                    color = "#2e7d32"  # Medium green
                elif peak_value > 20:
                    significance = "deutlich"
                    color = "#388e3c"  # Light green
                else:
                    significance = "leicht erhöht"
                    color = "#66bb6a"  # Very light green
                
                distinctive_patterns.append({
                    'category': cat_data['category'],
                    'peak_hour': peak_hour,
                    'peak_value': peak_value,
                    'significance': significance,
                    'color': color
                })
        
        # Sort by how pronounced the peak is
        distinctive_patterns.sort(key=lambda x: x['peak_value'], reverse=True)
        
        return {
            'categories': categories,
            'hourly_data': hourly_data,
            'distinctive_patterns': distinctive_patterns[:5],  # Top 5 distinctive patterns
            'has_data': True
        }
    except Exception as e:
        print(f"Error computing temporal patterns: {e}")
        return {
            'categories': [],
            'hourly_data': [],
            'has_data': False,
            'error': str(e)
        }