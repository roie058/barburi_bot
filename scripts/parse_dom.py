from bs4 import BeautifulSoup

def extract_matches(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    # Find all divs that might be a match row (they usually have a combination of classes containing 'row')
    # Or find all 'gameInfo' divs and go up to the row containing buttons.
    
    matches = []
    
    # We found that team names are inside elements with class containing 'gameInfoLabel'
    info_labels = soup.find_all(class_=lambda c: c and 'gameInfoLabel' in c)
    
    processed_rows = set()
    
    for label in info_labels:
        # Go up to find the row container that has buttons
        curr = label
        row = None
        for _ in range(10):
            curr = curr.parent
            if curr is None or curr.name == 'body':
                break
            buttons = curr.find_all('button')
            # A standard 3-way match row has at least 3 buttons (1, X, 2)
            if len(buttons) >= 3:
                row = curr
                break
                
        if row and id(row) not in processed_rows:
            processed_rows.add(id(row))
            
            # Extract team names from this row
            team_labels = row.find_all(class_=lambda c: c and 'gameInfoLabel' in c)
            team_texts = [t.text.replace('(Match)', '').strip() for t in team_labels if t.text.strip()]
            
            if len(team_texts) >= 2: # Sometimes draw isn't listed as a team label
                if "Real Madrid" in team_texts[0]:
                    print("DEBUG TEAM TEXTS:", team_texts)
                team1 = team_texts[0]
                # team2 might be at a different index if there are other labels
                # Let's just take the first two unique ones that aren't 'Draw'
                unique_teams = []
                for t in team_texts:
                    if t not in unique_teams and t.lower() != 'draw':
                        unique_teams.append(t)
                
                if len(unique_teams) >= 2:
                    team1 = unique_teams[0]
                    team2 = unique_teams[1]
                else:
                    team1 = team_texts[0]
                    team2 = team_texts[1]
                
                # Extract odds buttons (first 3 buttons are usually 1, X, 2 if available)
                buttons = row.find_all('button')
                odds = []
                for b in buttons[:3]:
                    # Extract the odds value (ignoring other spans inside)
                    # For moneyline, it's usually just the text
                    odds.append(b.text.strip())
                    
                if len(odds) == 3:
                    matches.append({
                        'team1': team1,
                        'team2': team2,
                        'num_1': odds[0],
                        'num_X': odds[1],
                        'num_2': odds[2]
                    })
    
    return matches

if __name__ == "__main__":
    with open("pinnacle_dom.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    matches = extract_matches(html)
    print(f"Extracted {len(matches)} matches")
    for m in matches[:10]:
        print(m)
