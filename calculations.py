import json

int_list = []
local_list = []


class Intergame:
    def __init__(self, parameters):
        self.game_time = parameters['name']
        self.team1 = parameters['team1'].split('(')[0].strip()
        self.team2 = parameters['team2'].split('(')[0].strip()
        self.odd1 = float(parameters['odd1'])
        self.odd2 = float(parameters['odd2'])


class Wingame:
    def __init__(self, parameters):
        self.game_date = parameters[2]
        self.game_time = parameters[3]
        self.team1 = parameters[4]
        self.team2 = parameters[6]
        self.odd1 = float(parameters[5])
        self.odd2 = float(parameters[7])


games = []
with open('./data/run_results.json', mode='r') as file:
    data = json.load(file)
    for leage in data["leage"]:
        if leage.get('match'):
            for event in leage['match']:
                if event.get('odd1'):
                    games.append(Intergame(event))
                else:
                    continue
        else:
            continue
    file.close()


def find_arbitrage(local: Wingame, international: Intergame, switch=False):
    """
    Identifies an arbitrage opportunity between two betting sites.
    :param switch: if teams is opposite order
    :param threshold:
    :param international: Intergame class of the world odds
    :param local: Wingame class of the winner game
    :return: A dictionary with arbitrage information or a message indicating no arbitrage.
    """
    if any(odds <= 1 for odds in [local.odd1, international.odd1, local.odd2, international.odd2]):
        raise ValueError("All odds must be greater than 1.")

    win_int, win_odd_int = (international.team1, international.odd1) if float(international.odd1) < float(
        international.odd2) else (international.team2, international.odd2)

    win_local, win_odd_local = (local.team1, local.odd1) if float(local.odd1) < float(local.odd2) else (
    local.team2, local.odd2)
    int_team1, int_team2, int_odd1, int_odd2 = (international.team1, international.team2, international.odd1,
                                                international.odd2) if not switch else (international.team2,
                                                                                        international.team1,
                                                                                        international.odd2,
                                                                                        international.odd1)

    if win_int != win_local and abs(local.odd1 - local.odd2) >= 1:

        arb = {
            "arbitrage": True,
            "bet_type": "Sure",
            "game_date": local.game_date,
            "team1": local.team1,
            "team2": local.team2,
            "bet_on_team": win_int,
            "bet_at_site": 'Winner',
            "int_team1": int_team1,
            "int_team2": int_team2,
            "int_odd1": int_odd1,
            "int_odd2": int_odd2

        }
        return arb
    elif abs(win_odd_local - win_odd_int) >= 2 and (win_odd_local/win_odd_int) >= 1.2:

        arb = {
                    "arbitrage": True,
                    "bet_type": "Great",
                    "game_date": local.game_date,
                    "team1": local.team1,
                    "team2": local.team2,
                    "bet_on_team": win_int,
                    "bet_at_site": 'Winner',
                    "int_team1": int_team1,
                    "int_team2": int_team2,
                    "int_odd1": int_odd1,
                    "int_odd2": int_odd2,
                    "local_odd1": local.odd1,
                    "local_odd2": local.odd2
        }
        return arb

    return {
        "arbitrage": False,
        "message": "No arbitrage opportunity with the given odds"
    }


def compare_games(win_lst):
    match_list = []
    global games
    for game in win_lst:
        g = Wingame(game)
        for match in games:
            teams = [match.team1, match.team2]
            if g.team1 in teams and g.team2 in teams:
                if g.team1 == match.team1:
                    res = find_arbitrage(local=g, international=match)
                    if res["arbitrage"]:
                        match_list.append(res)
                else:
                    res = find_arbitrage(local=g, international=match, switch=True)
                    if res["arbitrage"]:
                        match_list.append(res)
    return match_list
