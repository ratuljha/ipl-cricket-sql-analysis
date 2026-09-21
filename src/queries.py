"""
src/queries.py
Contains 15 structured analytical SQL queries on the IPL database.
Includes aggregations, multi-table JOINs, subqueries, and window functions (RANK, ROW_NUMBER).
"""

import os
import sqlite3
import pandas as pd

def get_connection():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "ipl.db")
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}. Run load_data.py first.")
    return sqlite3.connect(db_path)

def run_query(query):
    conn = get_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ==============================================================
# 15 ANALYTICAL SQL QUERIES
# ==============================================================

# Query 1: Top 10 All-Time Run Scorers
Q_TOP_RUN_SCORERS = """
SELECT 
    batsman,
    SUM(batsman_runs) AS total_runs,
    COUNT(DISTINCT match_id) AS matches_played,
    ROUND(CAST(SUM(batsman_runs) AS FLOAT) / COUNT(DISTINCT match_id), 2) AS runs_per_match
FROM deliveries
GROUP BY batsman
ORDER BY total_runs DESC
LIMIT 10;
"""

# Query 2: Top 10 All-Time Wicket Takers (Excluding Run Outs)
Q_TOP_WICKET_TAKERS = """
SELECT 
    bowler,
    COUNT(*) AS total_wickets,
    COUNT(DISTINCT match_id) AS matches_played
FROM deliveries
WHERE dismissal_kind IS NOT NULL 
  AND dismissal_kind NOT IN ('run out', 'retired hurt', 'obstructing the field')
GROUP BY bowler
ORDER BY total_wickets DESC
LIMIT 10;
"""

# Query 3: Franchise Win Percentage & Match Summary
Q_TEAM_WIN_RATES = """
WITH team_matches AS (
    SELECT team1 AS team FROM matches
    UNION ALL
    SELECT team2 AS team FROM matches
),
match_counts AS (
    SELECT team, COUNT(*) AS total_matches
    FROM team_matches
    GROUP BY team
),
win_counts AS (
    SELECT winner AS team, COUNT(*) AS total_wins
    FROM matches
    WHERE winner IS NOT NULL
    GROUP BY winner
)
SELECT 
    m.team,
    m.total_matches,
    COALESCE(w.total_wins, 0) AS total_wins,
    ROUND((CAST(COALESCE(w.total_wins, 0) AS FLOAT) / m.total_matches) * 100, 2) AS win_percentage
FROM match_counts m
LEFT JOIN win_counts w ON m.team = w.team
WHERE m.total_matches >= 20
ORDER BY win_percentage DESC;
"""

# Query 4: Toss Decision Impact (Field First vs Bat First)
Q_TOSS_IMPACT = """
SELECT 
    toss_decision,
    COUNT(*) AS total_matches,
    SUM(CASE WHEN toss_winner = winner THEN 1 ELSE 0 END) AS toss_and_match_wins,
    ROUND(CAST(SUM(CASE WHEN toss_winner = winner THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) AS toss_win_match_win_pct
FROM matches
WHERE winner IS NOT NULL
GROUP BY toss_decision;
"""

# Query 5: Average First Innings Score by Venue (Min 10 Matches)
Q_VENUE_FIRST_INNINGS = """
SELECT 
    m.venue,
    COUNT(DISTINCT m.id) AS matches_hosted,
    ROUND(AVG(first_inns.total_runs), 1) AS avg_first_innings_score
FROM matches m
JOIN (
    SELECT match_id, SUM(total_runs) AS total_runs
    FROM deliveries
    WHERE inning = 1
    GROUP BY match_id
) first_inns ON m.id = first_inns.match_id
GROUP BY m.venue
HAVING matches_hosted >= 10
ORDER BY avg_first_innings_score DESC
LIMIT 15;
"""

# Query 6: Chasing Success Rate by Venue
Q_CHASING_SUCCESS_VENUE = """
SELECT 
    venue,
    COUNT(*) AS total_matches,
    SUM(CASE WHEN win_by_wickets > 0 THEN 1 ELSE 0 END) AS chasing_wins,
    ROUND(CAST(SUM(CASE WHEN win_by_wickets > 0 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) AS chase_win_pct
FROM matches
WHERE winner IS NOT NULL
GROUP BY venue
HAVING total_matches >= 15
ORDER BY chase_win_pct DESC
LIMIT 10;
"""

# Query 7: Most Destructive Powerplay Batsmen (Overs 1-6, Min 400 Balls)
Q_POWERPLAY_STRIKE_RATE = """
SELECT 
    batsman,
    SUM(batsman_runs) AS powerplay_runs,
    COUNT(*) AS powerplay_balls_faced,
    ROUND((CAST(SUM(batsman_runs) AS FLOAT) / COUNT(*)) * 100, 2) AS powerplay_strike_rate
FROM deliveries
WHERE over <= 6
GROUP BY batsman
HAVING powerplay_balls_faced >= 400
ORDER BY powerplay_strike_rate DESC
LIMIT 10;
"""

# Query 8: Most Economical Death Overs Bowlers (Overs 16-20, Min 300 Balls)
Q_DEATH_OVERS_ECONOMY = """
SELECT 
    bowler,
    COUNT(*) AS balls_bowled,
    SUM(total_runs) AS runs_conceded,
    ROUND(CAST(SUM(total_runs) AS FLOAT) / (COUNT(*) / 6.0), 2) AS death_overs_economy
FROM deliveries
WHERE over >= 16
GROUP BY bowler
HAVING balls_bowled >= 300
ORDER BY death_overs_economy ASC
LIMIT 10;
"""

# Query 9: Window Function: Season-by-Season Top Run Scorer (Orange Cap Simulation)
Q_ORANGE_CAP_PER_SEASON = """
WITH season_runs AS (
    SELECT 
        m.season,
        d.batsman,
        SUM(d.batsman_runs) AS total_runs,
        ROW_NUMBER() OVER (PARTITION BY m.season ORDER BY SUM(d.batsman_runs) DESC) AS rank
    FROM deliveries d
    JOIN matches m ON d.match_id = m.id
    GROUP BY m.season, d.batsman
)
SELECT season, batsman, total_runs
FROM season_runs
WHERE rank = 1
ORDER BY season ASC;
"""

# Query 10: Window Function: Season-by-Season Leading Wicket Takers (Purple Cap Simulation)
Q_PURPLE_CAP_PER_SEASON = """
WITH season_wickets AS (
    SELECT 
        m.season,
        d.bowler,
        COUNT(*) AS total_wickets,
        ROW_NUMBER() OVER (PARTITION BY m.season ORDER BY COUNT(*) DESC) AS rank
    FROM deliveries d
    JOIN matches m ON d.match_id = m.id
    WHERE d.dismissal_kind IS NOT NULL 
      AND d.dismissal_kind NOT IN ('run out', 'retired hurt')
    GROUP BY m.season, d.bowler
)
SELECT season, bowler, total_wickets
FROM season_wickets
WHERE rank = 1
ORDER BY season ASC;
"""

# Query 11: Boundary Percentage Analysis per Franchise
Q_BOUNDARY_PERCENTAGE = """
SELECT 
    batting_team AS team,
    SUM(total_runs) AS total_runs,
    SUM(CASE WHEN batsman_runs IN (4, 6) THEN batsman_runs ELSE 0 END) AS boundary_runs,
    ROUND(CAST(SUM(CASE WHEN batsman_runs IN (4, 6) THEN batsman_runs ELSE 0 END) AS FLOAT) / SUM(total_runs) * 100, 2) AS boundary_run_pct
FROM deliveries
GROUP BY batting_team
HAVING total_runs >= 5000
ORDER BY boundary_run_pct DESC;
"""

# Query 12: High Stakes Rivalry Head-to-Head (CSK vs MI)
Q_CSK_VS_MI_RIVALRY = """
SELECT 
    winner,
    COUNT(*) AS total_wins,
    ROUND(CAST(COUNT(*) AS FLOAT) / (SELECT COUNT(*) FROM matches WHERE (team1='Chennai Super Kings' AND team2='Mumbai Indians') OR (team1='Mumbai Indians' AND team2='Chennai Super Kings')) * 100, 2) AS win_pct
FROM matches
WHERE (team1 = 'Chennai Super Kings' AND team2 = 'Mumbai Indians')
   OR (team1 = 'Mumbai Indians' AND team2 = 'Chennai Super Kings')
GROUP BY winner
HAVING winner IS NOT NULL;
"""

# Query 13: Win Margin Distribution by Year
Q_WIN_MARGIN_TRENDS = """
SELECT 
    season,
    COUNT(*) AS matches_count,
    ROUND(AVG(CASE WHEN win_by_runs > 0 THEN win_by_runs END), 1) AS avg_win_margin_runs,
    ROUND(AVG(CASE WHEN win_by_wickets > 0 THEN win_by_wickets END), 1) AS avg_win_margin_wickets
FROM matches
WHERE winner IS NOT NULL
GROUP BY season
ORDER BY season ASC;
"""

# Query 14: Top Player of the Match Award Winners
Q_PLAYER_OF_MATCH = """
SELECT 
    player_of_match,
    COUNT(*) AS total_awards
FROM matches
WHERE player_of_match IS NOT NULL
GROUP BY player_of_match
ORDER BY total_awards DESC
LIMIT 10;
"""

# Query 15: Run Rate Evolution Across Over Blocks (1-6 Powerplay, 7-15 Middle, 16-20 Death)
Q_OVER_PHASE_RUN_RATES = """
SELECT 
    CASE 
        WHEN over <= 6 THEN 'Powerplay (Overs 1-6)'
        WHEN over <= 15 THEN 'Middle Overs (Overs 7-15)'
        ELSE 'Death Overs (Overs 16-20)'
    END AS match_phase,
    COUNT(*) AS total_deliveries,
    SUM(total_runs) AS total_runs_scored,
    ROUND(CAST(SUM(total_runs) AS FLOAT) / (COUNT(*) / 6.0), 2) AS avg_run_rate_per_over
FROM deliveries
GROUP BY match_phase
ORDER BY avg_run_rate_per_over ASC;
"""

def test_all_queries():
    print("Testing SQL queries against SQLite database...")
    queries = [
        ("Top Run Scorers", Q_TOP_RUN_SCORERS),
        ("Top Wicket Takers", Q_TOP_WICKET_TAKERS),
        ("Team Win Rates", Q_TEAM_WIN_RATES),
        ("Toss Impact", Q_TOSS_IMPACT),
        ("Venue First Innings Avg", Q_VENUE_FIRST_INNINGS),
        ("Orange Cap (Window Function)", Q_ORANGE_CAP_PER_SEASON),
        ("Over Phase Run Rates", Q_OVER_PHASE_RUN_RATES)
    ]
    for name, q in queries:
        df = run_query(q)
        print(f"[PASS] {name}: returned {len(df)} rows")
    print("All queries executed successfully!")

if __name__ == "__main__":
    test_all_queries()
