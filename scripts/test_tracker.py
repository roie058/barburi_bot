import sqlite3

def trigger_simulated_change():
    conn = sqlite3.connect("data/tracker.sqlite")
    cursor = conn.cursor()
    
    # Get any valid match
    cursor.execute("SELECT id, game, num_1, num_X, num_2, team1_hebrew, team2_hebrew FROM matches LIMIT 1")
    row = cursor.fetchone()
    
    if row:
        match_id, game, n1, nX, n2, he1, he2 = row
        print(f"Modifying odds for match {game} ({match_id})")
        print(f"Old odds: 1: {n1}, X: {nX}, 2: {n2}")
        
        # Simulate a big favorite flip with > 0.75 confidence difference
        # That means prob1 - prob2 > 0.75. 
        # For odds 1.05 (prob 0.95), odds 20.0 (prob 0.05). Diff = 0.90
        new_n1 = 20.0
        new_n2 = 1.05
        print(f"New odds to trigger alert: 1: {new_n1}, X: {nX}, 2: {new_n2}")
        
        cursor.execute("UPDATE matches SET num_1 = ?, num_X = ?, num_2 = ? WHERE id = ?", (new_n1, nX, new_n2, match_id))
        conn.commit()
        print("Done. Now run major_change_tracker.py. It should detect the change, revert the odds back to the LIVE Winner odds (because the db odds are 'old'), and trigger a major change alert via telegram.")
    conn.close()

if __name__ == "__main__":
    trigger_simulated_change()
