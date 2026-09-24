"""
src/visualize.py
Generates presentation-ready charts from SQL query results and saves them to outputs/charts/.
"""

import os
import matplotlib.pyplot as plt
import seaborn as sns
from queries import (
    run_query,
    Q_TOP_RUN_SCORERS,
    Q_TEAM_WIN_RATES,
    Q_TOSS_IMPACT,
    Q_VENUE_FIRST_INNINGS,
    Q_OVER_PHASE_RUN_RATES
)

# Apply modern aesthetic theme
sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.sans-serif': 'Arial', 'font.family': 'sans-serif'})

def ensure_output_dir():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(base_dir, "outputs", "charts")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir

def chart_top_run_scorers(out_dir):
    print("Generating Chart 1: Top Run Scorers...")
    df = run_query(Q_TOP_RUN_SCORERS)
    
    plt.figure(figsize=(10, 5.5))
    bars = sns.barplot(
        data=df, 
        x="total_runs", 
        y="batsman", 
        palette="Blues_r"
    )
    plt.title("IPL All-Time Leading Run Scorers (2008–2020)", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Total Runs Scored", fontsize=11)
    plt.ylabel("Batsman", fontsize=11)
    
    # Add values on bars
    for p in bars.patches:
        width = p.get_width()
        plt.text(width + 40, p.get_y() + p.get_height()/2., f"{int(width):,}", 
                 va="center", fontsize=9.5, fontweight="semibold", color="#1e293b")

    plt.tight_layout()
    path = os.path.join(out_dir, "top_run_scorers.png")
    plt.savefig(path, dpi=200)
    plt.close()
    print(f"Saved: {path}")

def chart_team_win_rates(out_dir):
    print("Generating Chart 2: Franchise Win Percentage...")
    df = run_query(Q_TEAM_WIN_RATES)
    
    plt.figure(figsize=(10, 6))
    bars = sns.barplot(
        data=df, 
        x="win_percentage", 
        y="team", 
        palette="crest"
    )
    plt.title("IPL Franchise Win Rates (Min 20 Matches)", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Win Percentage (%)", fontsize=11)
    plt.ylabel("Team", fontsize=11)
    plt.xlim(0, 70)
    
    for p in bars.patches:
        width = p.get_width()
        plt.text(width + 0.8, p.get_y() + p.get_height()/2., f"{width:.1f}%", 
                 va="center", fontsize=9.5, fontweight="semibold", color="#1e293b")

    plt.tight_layout()
    path = os.path.join(out_dir, "franchise_win_rates.png")
    plt.savefig(path, dpi=200)
    plt.close()
    print(f"Saved: {path}")

def chart_toss_impact(out_dir):
    print("Generating Chart 3: Toss Impact Analysis...")
    df = run_query(Q_TOSS_IMPACT)
    
    plt.figure(figsize=(7, 5))
    bars = sns.barplot(
        data=df, 
        x="toss_decision", 
        y="toss_win_match_win_pct", 
        palette=["#3b82f6", "#10b981"]
    )
    plt.title("Toss Decision vs Match Victory Rate", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Toss Decision (Choice)", fontsize=11)
    plt.ylabel("Toss Winner Match Win Rate (%)", fontsize=11)
    plt.ylim(0, 65)
    
    for p in bars.patches:
        height = p.get_height()
        plt.text(p.get_x() + p.get_width()/2., height + 1.2, f"{height:.1f}%", 
                 ha="center", fontsize=11, fontweight="bold", color="#1e293b")

    plt.axhline(50, color='gray', linestyle='--', alpha=0.7, label='50% Neutral Baseline')
    plt.legend(loc='lower right')
    plt.tight_layout()
    path = os.path.join(out_dir, "toss_decision_impact.png")
    plt.savefig(path, dpi=200)
    plt.close()
    print(f"Saved: {path}")

def chart_match_phase_run_rates(out_dir):
    print("Generating Chart 4: Phase-by-Phase Run Rates...")
    df = run_query(Q_OVER_PHASE_RUN_RATES)
    
    plt.figure(figsize=(8, 5))
    bars = sns.barplot(
        data=df, 
        x="match_phase", 
        y="avg_run_rate_per_over", 
        palette="viridis"
    )
    plt.title("Average Run Rate Progression by Match Phase", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Phase of Innings", fontsize=11)
    plt.ylabel("Scoring Rate (Runs Per Over)", fontsize=11)
    plt.ylim(0, 12)
    
    for p in bars.patches:
        height = p.get_height()
        plt.text(p.get_x() + p.get_width()/2., height + 0.25, f"{height:.2f} rpo", 
                 ha="center", fontsize=10.5, fontweight="bold", color="#1e293b")

    plt.tight_layout()
    path = os.path.join(out_dir, "phase_run_rates.png")
    plt.savefig(path, dpi=200)
    plt.close()
    print(f"Saved: {path}")

def generate_all_charts():
    out_dir = ensure_output_dir()
    chart_top_run_scorers(out_dir)
    chart_team_win_rates(out_dir)
    chart_toss_impact(out_dir)
    chart_match_phase_run_rates(out_dir)
    print("All charts generated and saved successfully!")

if __name__ == "__main__":
    generate_all_charts()
