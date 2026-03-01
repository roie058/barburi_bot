import difflib
from utils import _clean_team_name

w_team1 = "Celta de Vigo"
w_team2 = "Valencia"

u_team1 = "Valencia"
u_team2 = "Elche"

w1 = _clean_team_name(w_team1)
w2 = _clean_team_name(w_team2)
u1 = _clean_team_name(u_team1)
u2 = _clean_team_name(u_team2)

print(f"Cleaned Names: W='{w1}'-'{w2}' vs U='{u1}'-'{u2}'")

# Straight
s1 = difflib.SequenceMatcher(None, w1, u1).ratio()
s2 = difflib.SequenceMatcher(None, w2, u2).ratio()
avg_straight = (s1 + s2) / 2
print(f"Straight: {s1:.2f} + {s2:.2f} -> Avg: {avg_straight:.2f}")

# Swapped
s3 = difflib.SequenceMatcher(None, w1, u2).ratio()
s4 = difflib.SequenceMatcher(None, w2, u1).ratio()
avg_swapped = (s3 + s4) / 2
print(f"Swapped: {s3:.2f} (Celta-Elche) + {s4:.2f} (Val-Val) -> Avg: {avg_swapped:.2f}")

threshold = 0.65
if avg_swapped > threshold:
    print(f"FAIL: Match > {threshold} triggered!")
else:
    print(f"PASS: Match <= {threshold}")
