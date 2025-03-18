# analysis_tool/statistics.py

import pandas as pd
import numpy as np
from collections import defaultdict
from django.db.models import Sum
from analysis_tool.models import StudentAGCategoryAnalysis, StudentOverallAnalysis
from main_app.models import AGKategorie  # falls benötigt
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules

def get_student_category_dataframe():
    """
    Baut einen DataFrame, in dem jede Zeile einen Schüler repräsentiert und
    jede Spalte die in einer bestimmten AGKategorie verbrachte Zeit (time_spent) angibt.
    """
    qs = StudentAGCategoryAnalysis.objects.all()
    # data: {student_id: {kategorie_name: total_time_spent, ...}, ...}
    data = defaultdict(lambda: defaultdict(float))
    for entry in qs:
        student_id = entry.student.id
        # Verwende den Namen der Kategorie oder 'Uncategorized', falls nicht vorhanden.
        cat = entry.ag_kategorie.name if entry.ag_kategorie else "Uncategorized"
        data[student_id][cat] += entry.time_spent
    df = pd.DataFrame.from_dict(data, orient='index').fillna(0)
    return df

def compute_correlation_matrix():
    """
    Berechnet eine Korrelationsmatrix zwischen der in den einzelnen AGKategorien verbrachten Zeit.
    """
    df = get_student_category_dataframe()
    corr = df.corr()
    return corr

def compute_relative_time_ratios(category_of_interest_name="Sport"):
    """
    Berechnet, für alle Schüler, die in der angegebenen AGKategorie (z. B. Sport)
    Zeit verbringen, das Verhältnis der in anderen Kategorien verbrachten Zeit zur Zeit in der
    Kategorie of interest. Gibt ein Dict zurück, z. B.:
      {"Ernährung": 0.33, "Natur": 0.17, "Basteln": 0.08}
    was bedeutet, dass pro 1 Std. Sport durchschnittlich 20 min in Ernährung, 10 min in Natur und 5 min in Basteln verbracht werden.
    """
    df = get_student_category_dataframe()
    if category_of_interest_name not in df.columns:
        return {}
    ratios = {}
    # Nur Schüler berücksichtigen, die in der Basiskategorie Zeit haben.
    df_filtered = df[df[category_of_interest_name] > 0]
    for col in df.columns:
        if col == category_of_interest_name:
            continue
        # Berechne das Verhältnis
        ratio_series = df_filtered[col] / df_filtered[category_of_interest_name]
        ratios[col] = ratio_series.mean()
    return ratios

def perform_regression_analysis(baseline_category="Sport", target_category="Ernährung"):
    """
    Führt eine lineare Regression durch, bei der die unabhängige Variable die Zeit in der Basiskategorie
    und die abhängige Variable die Zeit in der Zielkategorie ist.
    Liefert ein Dict mit Regressionskoeffizient, Intercept und Bestimmtheitsmaß (R^2).
    """
    df = get_student_category_dataframe()
    if baseline_category not in df.columns or target_category not in df.columns:
        return None
    # Nur Schüler mit positiver Zeit in der Basiskategorie
    df_filtered = df[df[baseline_category] > 0]
    X = df_filtered[[baseline_category]].values
    y = df_filtered[target_category].values
    reg = LinearRegression().fit(X, y)
    return {
        "coefficient": reg.coef_[0],
        "intercept": reg.intercept_,
        "score": reg.score(X, y)
    }

def perform_cluster_analysis(n_clusters=3):
    df = get_student_category_dataframe()
    n_samples = df.shape[0]
    if n_samples < n_clusters:
        # Option 1: Anzahl der Cluster anpassen, sodass n_clusters = n_samples
        print(f"Warnung: n_samples ({n_samples}) < n_clusters ({n_clusters}). Setze n_clusters auf {n_samples}.")
        n_clusters = n_samples
        # Option 2 (Alternativ): Du könntest stattdessen auch eine leere DataFrame oder einen speziellen Hinweis zurückgeben.
        # return pd.DataFrame(), f"Nicht genügend Daten: n_samples={n_samples} < n_clusters={n_clusters}."
    kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(df)
    df['cluster'] = kmeans.labels_
    return df


def compute_association_rules(min_support=0.1, min_confidence=0.5):
    
    from mlxtend.preprocessing import TransactionEncoder
    from mlxtend.frequent_patterns import apriori, association_rules
    
    transactions = []
    df = get_student_category_dataframe()
    for index, row in df.iterrows():
        attended = list(row[row > 0].index)
        transactions.append(attended)
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    df_trans = pd.DataFrame(te_ary, columns=te.columns_)
    frequent_itemsets = apriori(df_trans, min_support=min_support, use_colnames=True)
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
    return rules
    

# Beispiel, wie man die Funktionen verwenden kann:
if __name__ == "__main__":
    # Korrelationsmatrix anzeigen:
    corr = compute_correlation_matrix()
    print("Korrelationsmatrix der Zeit in den AG-Kategorien:")
    print(corr)
    
    # Relative Zeitverhältnisse (zum Beispiel für Sport)
    ratios = compute_relative_time_ratios("Sport")
    print("\nRelative Zeitverhältnisse (pro Stunde Sport):")
    for cat, ratio in ratios.items():
        print(f"{cat}: {ratio * 60:.1f} Minuten")
    
    # Regression: Wie verändert sich die Zeit in 'Ernährung' pro zusätzlicher Stunde Sport?
    reg_results = perform_regression_analysis("Sport", "Ernährung")
    if reg_results:
        print("\nRegressionsanalyse (Ernährung als Funktion von Sport):")
        print(f"Koeffizient: {reg_results['coefficient']:.2f}")
        print(f"Intercept: {reg_results['intercept']:.2f}")
        print(f"R^2: {reg_results['score']:.2f}")
    
    # Clusteranalyse
    clustered_df = perform_cluster_analysis(n_clusters=3)
    print("\nClusteranalyse (erste 5 Zeilen):")
    print(clustered_df.head())
    
    # Assoziationsregeln (Platzhalter)
    assoc_rules = compute_association_rules()
    print("\nAssoziationsregeln:")
    print(assoc_rules)
