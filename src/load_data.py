"""
src/load_data.py
Loads IPL matches and deliveries CSV files into a clean SQLite database (data/ipl.db).
Performs team name standardization, creates backward-compatible column aliases,
and creates database indexes for high query performance.
"""

import os
import sqlite3
import pandas as pd

def standardize_team_names(df, cols):
    """Normalize franchise names that changed over seasons."""
    mapping = {
        'Rising Pune Supergiant': 'Rising Pune Supergiants',
        'Delhi Daredevils': 'Delhi Capitals',
        'Deccan Chargers': 'Sunrisers Hyderabad',
        'Kings XI Punjab': 'Punjab Kings'
    }
    for c in cols:
        if c in df.columns:
            df[c] = df[c].replace(mapping)
    return df

def build_database():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    db_path = os.path.join(data_dir, "ipl.db")

    matches_csv = os.path.join(data_dir, "matches.csv")
    deliveries_csv = os.path.join(data_dir, "deliveries.csv")

    if not os.path.exists(matches_csv) or not os.path.exists(deliveries_csv):
        raise FileNotFoundError(f"Missing CSV files in {data_dir}. Ensure matches.csv and deliveries.csv exist.")

    print("1. Loading CSV datasets...")
    df_matches = pd.read_csv(matches_csv)
    df_deliveries = pd.read_csv(deliveries_csv)

    print(f"   Matches loaded: {len(df_matches):,} rows")
    print(f"   Deliveries loaded: {len(df_deliveries):,} rows")

    # Clean team names
    print("2. Standardizing franchise names & creating canonical columns...")
    team_cols_matches = ['team1', 'team2', 'toss_winner', 'winner']
    df_matches = standardize_team_names(df_matches, team_cols_matches)

    team_cols_deliv = ['batting_team', 'bowling_team']
    df_deliveries = standardize_team_names(df_deliveries, team_cols_deliv)

    # Standardize deliveries batter -> batsman
    if 'batter' in df_deliveries.columns and 'batsman' not in df_deliveries.columns:
        df_deliveries['batsman'] = df_deliveries['batter']

    # Standardize win margins in matches
    if 'win_by_runs' not in df_matches.columns:
        df_matches['win_by_runs'] = df_matches.apply(
            lambda r: r['result_margin'] if str(r.get('result')).strip() == 'runs' else 0, axis=1
        )
    if 'win_by_wickets' not in df_matches.columns:
        df_matches['win_by_wickets'] = df_matches.apply(
            lambda r: r['result_margin'] if str(r.get('result')).strip() == 'wickets' else 0, axis=1
        )

    # Convert date and seasons
    if 'date' in df_matches.columns:
        df_matches['date'] = pd.to_datetime(df_matches['date'], errors='coerce')
        if 'season' not in df_matches.columns or df_matches['season'].isnull().any():
            df_matches['season'] = df_matches['date'].dt.year

    # Connect to SQLite
    print(f"3. Writing to SQLite database: {db_path}...")
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    
    df_matches.to_sql("matches", conn, if_exists="replace", index=False)
    df_deliveries.to_sql("deliveries", conn, if_exists="replace", index=False)

    print("4. Creating relational database indexes...")
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_id ON matches(id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_season ON matches(season);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deliveries_match_id ON deliveries(match_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deliveries_batsman ON deliveries(batsman);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deliveries_bowler ON deliveries(bowler);")
    conn.commit()
    conn.close()

    print("Database built successfully with indexing! Ready for SQL queries.")

if __name__ == "__main__":
    build_database()
