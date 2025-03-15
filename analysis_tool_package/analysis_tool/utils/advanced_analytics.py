import pandas as pd
import numpy as np
import math
from collections import defaultdict
from django.db.models import Sum
from analysis_tool.models import StudentSessionBuffer, StudentAGCategoryAnalysis
from main_app.models import Schueler, AGKategorie

def compute_transition_probabilities():
    """
    Berechnet Übergangswahrscheinlichkeiten zwischen AG-Kategorien basierend auf den
    StudentSessionBuffer-Einträgen. Für jeden Schüler werden die Sitzungen chronologisch
    sortiert, und die Übergänge von einer Kategorie zur nächsten werden gezählt.
    
    Rückgabe:
      dict: Schlüssel sind Tupel (from_category, to_category), Werte die relative Häufigkeit.
    """
    transitions = defaultdict(int)
    total_transitions = 0
    
    # Für jeden Schüler
    for student in Schueler.objects.all():
        sessions = StudentSessionBuffer.objects.filter(student=student).order_by('session_start')
        # Filtere nur Sitzungen, die einer AGKategorie zugeordnet sind
        categories = [s.ag_kategorie.name for s in sessions if s.ag_kategorie is not None]
        for i in range(len(categories) - 1):
            from_cat = categories[i]
            to_cat = categories[i+1]
            transitions[(from_cat, to_cat)] += 1
            total_transitions += 1
    
    if total_transitions == 0:
        return {}
    # Normiere die Übergangszahlen zu Wahrscheinlichkeiten
    transition_prob = {k: v / total_transitions for k, v in transitions.items()}
    return transition_prob

def compute_student_diversity(student_id):
    """
    Berechnet die Diversität (Entropie) der AG-Kategorie-Besuche eines Schülers,
    basierend auf der in StudentAGCategoryAnalysis gespeicherten Zeit.
    
    Die Entropie gibt an, wie gleichmäßig die Zeit über die verschiedenen Kategorien
    verteilt ist – höhere Werte deuten auf ein breiteres Interessenprofil hin.
    
    Rückgabe:
      float: Entropie in Nat (natürlicher Logarithmus)
    """
    try:
        analyses = StudentAGCategoryAnalysis.objects.filter(student__id=student_id)
        if not analyses.exists():
            return 0.0
        total_time = sum(a.time_spent for a in analyses)
        if total_time == 0:
            return 0.0
        entropy = 0.0
        for a in analyses:
            p = a.time_spent / total_time
            if p > 0:
                entropy -= p * math.log(p)
        return entropy
    except Exception as e:
        print(f"Fehler bei Diversity-Berechnung für Schüler {student_id}: {e}")
        return None

def compute_temporal_trends():
    """
    Ermittelt, zu welchen Tagesstunden (0-23) Sitzungen in den verschiedenen AG-Kategorien
    beginnen. Liefert ein Dictionary, das pro Kategorie eine pandas Series mit den Zählungen pro Stunde enthält.
    
    Rückgabe:
      dict: {category_name: pandas.Series(index=0..23, values=count)}
    """
    qs = StudentSessionBuffer.objects.filter(ag_kategorie__isnull=False)
    data = []
    for s in qs:
        hour = s.session_start.hour
        cat = s.ag_kategorie.name
        data.append({'category': cat, 'hour': hour})
    if not data:
        return {}
    df = pd.DataFrame(data)
    trends = {}
    for cat, group in df.groupby('category'):
        counts = group['hour'].value_counts().sort_index()
        counts = counts.reindex(range(24), fill_value=0)
        trends[cat] = counts
    return trends

def compute_cooccurrence_network():
    """
    Berechnet ein Netzwerk der gleichzeitigen Vorkommen von AG-Kategorien.
    Für jeden Schüler und jeden Tag werden die besuchten Kategorien gesammelt;
    dann werden für alle Paarungen innerhalb dieses Tages die Vorkommenshäufigkeiten gezählt.
    
    Rückgabe:
      pandas.DataFrame: Eine Matrix mit Kategorien als Zeilen und Spalten, die die Co-Vorkommen zählt.
    """
    cooccurrence = defaultdict(lambda: defaultdict(int))
    for student in Schueler.objects.all():
        sessions = StudentSessionBuffer.objects.filter(student=student, ag_kategorie__isnull=False)
        days = defaultdict(set)
        for s in sessions:
            days[s.session_date].add(s.ag_kategorie.name)
        for day, cats in days.items():
            cats = list(cats)
            for i in range(len(cats)):
                for j in range(i, len(cats)):
                    cat1 = cats[i]
                    cat2 = cats[j]
                    cooccurrence[cat1][cat2] += 1
                    if cat1 != cat2:
                        cooccurrence[cat2][cat1] += 1
    all_cats = sorted(cooccurrence.keys())
    matrix = pd.DataFrame(index=all_cats, columns=all_cats, data=0)
    for cat1 in all_cats:
        for cat2 in all_cats:
            matrix.loc[cat1, cat2] = cooccurrence[cat1].get(cat2, 0)
    return matrix

def compute_engagement_metric(student_id):
    """
    Berechnet einen einfachen Engagement-Index für einen Schüler. Hier wird als Engagement
    der Anteil der Tage gewertet, an denen der Schüler mindestens eine Sitzung hatte, relativ zur
    Gesamtperiode zwischen dem ersten und letzten Besuch.
    
    Rückgabe:
      tuple: (engagement_ratio, number_of_days_with_sessions)
    """
    qs = StudentSessionBuffer.objects.filter(student__id=student_id)
    if not qs.exists():
        return 0.0, 0
    dates = qs.values_list('session_date', flat=True)
    unique_days = set(dates)
    total_days = (max(unique_days) - min(unique_days)).days + 1
    engagement_ratio = len(unique_days) / total_days if total_days > 0 else 0.0
    return engagement_ratio, len(unique_days)

if __name__ == "__main__":
    # Beispielaufruf der Funktionen
    
    print("Transition Probabilities:")
    transitions = compute_transition_probabilities()
    for (from_cat, to_cat), prob in transitions.items():
        print(f"{from_cat} -> {to_cat}: {prob:.2f}")
    
    test_student_id = 1  # Passe diesen Wert an eine existierende Schüler-ID an
    diversity = compute_student_diversity(test_student_id)
    print(f"\nDiversity (Entropy) for student {test_student_id}: {diversity:.2f}")
    
    print("\nTemporal Trends (Session start hours per category):")
    trends = compute_temporal_trends()
    for cat, series in trends.items():
        print(f"{cat}:")
        print(series)
    
    print("\nCo-occurrence Network:")
    cooccurrence_df = compute_cooccurrence_network()
    print(cooccurrence_df)
    
    engagement_ratio, days_with_sessions = compute_engagement_metric(test_student_id)
    print(f"\nEngagement metric for student {test_student_id}: {engagement_ratio:.2f} (days with sessions: {days_with_sessions})")
