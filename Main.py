import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, List, Optional, Union
from datetime import datetime

class NBAPropsAnalyzer:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def clean_team_name(self, raw_text: str) -> str:
        """Clean team name from the raw text"""
        # Dictionary of known team names
        team_names = {
            'Cleveland Cavaliers': 'Cavaliers',
            'Boston Celtics': 'Celtics',
            'New York Knicks': 'Knicks',
            'Orlando Magic': 'Magic',
            'Milwaukee Bucks': 'Bucks',
            'Atlanta Hawks': 'Hawks',
            'Miami Heat': 'Heat',
            'Indiana Pacers': 'Pacers',
            'Chicago Bulls': 'Bulls',
            'Detroit Pistons': 'Pistons',
            'Philadelphia 76ers': '76ers',
            'Brooklyn Nets': 'Nets',
            'Charlotte Hornets': 'Hornets',
            'Toronto Raptors': 'Raptors',
            'Washington Wizards': 'Wizards',
            'Oklahoma City Thunder': 'Thunder',
            'Memphis Grizzlies': 'Grizzlies',
            'Houston Rockets': 'Rockets',
            'Dallas Mavericks': 'Mavericks',
            'Los Angeles Lakers': 'Lakers',
            'LA Clippers': 'Clippers',
            'Denver Nuggets': 'Nuggets',
            'Minnesota Timberwolves': 'Timberwolves',
            'San Antonio Spurs': 'Spurs',
            'Golden State Warriors': 'Warriors',
            'Phoenix Suns': 'Suns',
            'Sacramento Kings': 'Kings',
            'Portland Trail Blazers': 'Trail Blazers',
            'Utah Jazz': 'Jazz',
            'New Orleans Pelicans': 'Pelicans'
        }
        
        # Remove any numbers at start of string
        while raw_text and raw_text[0].isdigit():
            raw_text = raw_text[1:]
            
        # Remove any single characters at start
        while raw_text and len(raw_text) > 1 and raw_text[0].isalpha() and not raw_text[1].isalpha():
            raw_text = raw_text[1:]
            
        # Clean any remaining whitespace
        raw_text = raw_text.strip()
        
        # Find the matching team name
        for full_name, short_name in team_names.items():
            if full_name in raw_text or short_name in raw_text:
                return short_name
                
        return raw_text

    def scrape_standings(self) -> Dict:
        """Scrape current NBA standings"""
        print("Fetching NBA standings...")
        url = "https://www.espn.com/nba/standings"
        
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            tables = soup.find_all('table', class_='Table')
            print(f"\nFound {len(tables)} tables")
            
            standings = {'Eastern': [], 'Western': []}
            
            # Process team names from the first and third tables
            eastern_teams = []
            western_teams = []
            
            if len(tables) >= 1:
                for row in tables[0].find_all('tr')[1:]:  # Skip header
                    cell = row.find('td')
                    if cell:
                        team_name = self.clean_team_name(cell.text.strip())
                        eastern_teams.append(team_name)
                        
            if len(tables) >= 3:
                for row in tables[2].find_all('tr')[1:]:  # Skip header
                    cell = row.find('td')
                    if cell:
                        team_name = self.clean_team_name(cell.text.strip())
                        western_teams.append(team_name)
            
            # Process stats from the second and fourth tables
            if len(tables) >= 2:
                for i, row in enumerate(tables[1].find_all('tr')[1:]):  # Skip header
                    cells = row.find_all('td')
                    if len(cells) >= 3 and i < len(eastern_teams):
                        try:
                            win_pct = float(cells[2].text.strip().replace('.', '0.'))
                        except ValueError:
                            win_pct = 0.0
                            
                        standings['Eastern'].append({
                            'team': eastern_teams[i],
                            'wins': int(cells[0].text.strip()),
                            'losses': int(cells[1].text.strip()),
                            'win_pct': win_pct,
                            'conference': 'Eastern'
                        })
                        
            if len(tables) >= 4:
                for i, row in enumerate(tables[3].find_all('tr')[1:]):  # Skip header
                    cells = row.find_all('td')
                    if len(cells) >= 3 and i < len(western_teams):
                        try:
                            win_pct = float(cells[2].text.strip().replace('.', '0.'))
                        except ValueError:
                            win_pct = 0.0
                            
                        standings['Western'].append({
                            'team': western_teams[i],
                            'wins': int(cells[0].text.strip()),
                            'losses': int(cells[1].text.strip()),
                            'win_pct': win_pct,
                            'conference': 'Western'
                        })
            
            return {"success": True, "data": standings}
            
        except Exception as e:
            print(f"\nError details: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_player_id(self, player_name: str) -> Dict:
        """Get player's ESPN ID"""
        search_url = "https://site.web.api.espn.com/apis/common/v3/search"
        params = {
            "query": player_name,
            "limit": 5,
            "type": "player",
            "sport": "basketball"
        }
        
        try:
            print(f"\nSearching for {player_name}...")
            response = requests.get(search_url, params=params)
            data = response.json()
            print(f"Debug - Search response: {data}")  # Print response data
            
            if 'items' in data and len(data['items']) > 0:
                for item in data['items']:
                    if item['displayName'].lower() == player_name.lower():
                        player_id = item['id']
                        print(f"Debug - Found player ID: {player_id}")
                        return {"success": True, "id": player_id}
                player_id = data['items'][0]['id']
                print(f"Debug - Using first result ID: {player_id}")
                return {"success": True, "id": player_id}
            return {"success": False, "error": "Player not found"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def clean_opponent_name(self, opponent: str) -> str:
        """Clean opponent name from game log"""
        print(f"\nDebug - Cleaning opponent name: {opponent}")
        
        # Remove any vs or @ prefix
        cleaned = opponent.replace('vs', '').replace('@', '').strip()
        print(f"After removing prefixes: {cleaned}")
        
        # Team abbreviation mapping
        team_map = {
            'MEM': 'Grizzlies',
            'GS': 'Warriors',
            'PHX': 'Suns',
            'SAC': 'Kings',
            'LAL': 'Lakers',
            'LAC': 'Clippers',
            'DAL': 'Mavericks',
            'HOU': 'Rockets',
            'NO': 'Pelicans',
            'SA': 'Spurs',
            'DEN': 'Nuggets',
            'MIN': 'Timberwolves',
            'POR': 'Trail Blazers',
            'OKC': 'Thunder',
            'UTAH': 'Jazz',
            'BOS': 'Celtics',
            'BKN': 'Nets',
            'NY': 'Knicks',
            'PHI': '76ers',
            'TOR': 'Raptors',
            'CHI': 'Bulls',
            'CLE': 'Cavaliers',
            'DET': 'Pistons',
            'IND': 'Pacers',
            'MIL': 'Bucks',
            'ATL': 'Hawks',
            'CHA': 'Hornets',
            'MIA': 'Heat',
            'ORL': 'Magic',
            'WSH': 'Wizards',
        }
        
        team_name = team_map.get(cleaned, cleaned)
        print(f"Final team name: {team_name}")
        return team_name

    def get_current_nba_season(self) -> str:
        """
        Determine the current NBA season.
        NBA season spans two years and officially starts in October.
        Returns the earlier year (e.g., 2024 for the 2024-25 season)
        """
        current_date = datetime.now()
        if current_date.month >= 10:  # New season starts in October
            return str(current_date.year)
        return str(current_date.year - 1)

    def get_player_games(self, player_name: str) -> Dict:
        """Get player's game logs"""
        player_id_result = self.get_player_id(player_name)
        if not player_id_result["success"]:
            return player_id_result
        
        player_id = player_id_result["id"]
        url = f"https://www.espn.com/nba/player/gamelog/_/id/{player_id}"
        
        try:
            print(f"Fetching game logs from: {url}")
            response = requests.get(url, headers=self.headers)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            game_tables = soup.find_all('table', class_='Table')
            print(f"\nDebug - Looking for game tables")
            print(f"Found {len(game_tables)} tables")
            
            all_games = []
            
            for table in game_tables:
                rows = table.find_all('tr')[1:]  # Skip header row
                
                for row in rows:
                    cells = row.find_all('td')
                    
                    if len(cells) >= 15 and any(month in cells[0].text.strip().lower() 
                        for month in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']):
                        try:
                            raw_opponent = cells[1].text.strip()
                            opponent = self.clean_opponent_name(raw_opponent)
                            
                            # Fix three pointers parsing
                            threes_str = cells[6].text.strip().split('-')[0]  # Get makes from "makes-attempts"
                            threes = int(threes_str) if threes_str.isdigit() else 0
                            
                            game_data = {
                                'date': cells[0].text.strip(),
                                'opponent': opponent,
                                'minutes': cells[3].text.strip() if len(cells) > 3 else '0',
                                'points': int(cells[16].text.strip() if len(cells) > 16 else '0'),
                                'rebounds': int(cells[10].text.strip() if len(cells) > 10 else '0'),
                                'assists': int(cells[11].text.strip() if len(cells) > 11 else '0'),
                                'blocks': int(cells[12].text.strip() if len(cells) > 12 else '0'),
                                'steals': int(cells[13].text.strip() if len(cells) > 13 else '0'),
                                'threes': threes  # Store three pointers made
                            }
                            all_games.append(game_data)
                            print(f"Found game: {game_data['date']} vs {game_data['opponent']} - " +
                                  f"{game_data['points']} pts, {game_data['threes']} threes")
                            
                        except (IndexError, ValueError) as e:
                            print(f"Error processing row: {str(e)}")
                            continue
            
            print(f"\nFound {len(all_games)} total games")
            return {"success": True, "data": all_games}
            
        except Exception as e:
            print(f"Error in get_player_games: {str(e)}")
            return {"success": False, "error": str(e)}

    def analyze_vs_team(self, games: List[Dict], team: str, prop_type: str, prop_value: float, is_over: bool) -> Dict:
        """Analyze player's performance against specific team"""
        relevant_games = []
        
        # Debug print
        print(f"\nDebug - Looking for games against {team}")
        for game in games:
            print(f"Debug - Checking game: Opponent = {game['opponent']}, Points = {game['points']}")
            if game['opponent'] == team:
                print(f"Debug - Found matching game!")
                relevant_games.append(game)
        
        if not relevant_games:
            return {
                "success": True,
                "data": {
                    "games_played": 0,
                    "average": 0,
                    "hit_rate": 0,
                    "hit_count": 0,
                    "performances": []
                }
            }
        
        # Calculate stats
        total_value = 0
        hits = 0
        performances = []
        
        for game in relevant_games:
            stat_key = prop_type.lower()
            stat_value = game.get(stat_key, 0)
            total_value += stat_value
            
            # Check if prop hit
            if is_over:
                hit = stat_value > prop_value
            else:
                hit = stat_value < prop_value
                
            if hit:
                hits += 1
                
            performances.append({
                'date': game['date'],
                'value': stat_value,
                'hit': hit
            })
        
        return {
            "success": True,
            "data": {
                "games_played": len(relevant_games),
                "average": total_value / len(relevant_games),
                "hit_rate": (hits / len(relevant_games)) * 100,
                "hit_count": hits,
                "performances": performances
            }
        }

    def analyze_performance(self, games: List[Dict], team: str, prop_type: str, prop_value: float, is_over: bool) -> Dict:
        """Analyze player's performance against specific team"""
        relevant_games = []
        
        # Map property types to game log keys
        stat_map = {
            'points': 'points',
            'rebounds': 'rebounds',
            'assists': 'assists',
            'steals': 'steals',
            'blocks': 'blocks',
            'threes': 'threes',
            'three pointers': 'threes',  # Add alternative naming
            '3pt': 'threes',             # Add alternative naming
            '3s': 'threes'               # Add alternative naming
        }
        
        stat_key = stat_map.get(prop_type.lower())
        if not stat_key:
            return {"success": False, "error": "Invalid prop type"}
        
        # Debug print
        print(f"\nDebug - Looking for games against {team}")
        for game in games:
            print(f"Debug - Checking game: Opponent = {game['opponent']}, {stat_key.title()} = {game[stat_key]}")
            if game['opponent'] == team:
                print(f"Debug - Found matching game!")
                relevant_games.append(game)
        
        if not relevant_games:
            return {
                "success": True,
                "data": {
                    "games_played": 0,
                    "average": 0,
                    "hit_rate": 0,
                    "hit_count": 0,
                    "performances": []
                }
            }
        
        # Calculate stats
        total_value = 0
        hits = 0
        performances = []
        
        for game in relevant_games:
            stat_value = game[stat_key]
            total_value += stat_value
            
            # Check if prop hit
            if is_over:
                hit = stat_value > prop_value
            else:
                hit = stat_value < prop_value
                
            if hit:
                hits += 1
                
            performances.append({
                'date': game['date'],
                'value': stat_value,
                'hit': hit
            })
        
        return {
            "success": True,
            "data": {
                "games_played": len(relevant_games),
                "average": total_value / len(relevant_games),
                "hit_rate": (hits / len(relevant_games)) * 100,
                "hit_count": hits,
                "performances": performances
            }
        }
    
    def get_surrounding_teams(self, team_name: str, standings: Dict, positions: int = 2) -> Dict:
        """Get teams above and below the given team in standings"""
        try:
            # Find which conference the team is in
            team_conf = None
            team_index = None
            
            for conf in ['Eastern', 'Western']:
                for i, team in enumerate(standings[conf]):
                    if team['team'] == team_name:
                        team_conf = conf
                        team_index = i
                        break
                if team_conf:
                    break
            
            if not team_conf:
                return {"success": False, "error": f"Team {team_name} not found in standings"}
            
            teams = {
                "above": [],
                "below": []
            }
            
            # Get teams above (in reverse order for proper standings order)
            start_above = max(0, team_index - positions)
            for i in range(team_index - 1, start_above - 1, -1):
                team = standings[team_conf][i]
                teams["above"].append(team)
            
            # Get teams below
            end_below = min(len(standings[team_conf]), team_index + positions + 1)
            for i in range(team_index + 1, end_below):
                team = standings[team_conf][i]
                teams["below"].append(team)
            
            return {"success": True, "data": teams}
            
        except Exception as e:
            print(f"Error in get_surrounding_teams: {str(e)}")
            return {"success": False, "error": str(e)}

    def analyze_surrounding_teams(self, games: List[Dict], opponent: str, standings: Dict,
                                prop_type: str, prop_value: float, is_over: bool, positions: int = 2) -> Dict:
        """Analyze performance against teams surrounding the opponent in standings"""
        # Get surrounding teams
        surr_teams = self.get_surrounding_teams(opponent, standings, positions)
        if not surr_teams["success"]:
            return surr_teams
            
        results = {
            "above": [],
            "below": []
        }
        
        # Process teams above
        if "above" in surr_teams["data"]:
            for pos, team in enumerate(surr_teams["data"]["above"], 1):
                analysis = self.analyze_vs_team(games, team['team'], prop_type, prop_value, is_over)
                if analysis["success"]:
                    results["above"].append({
                        "team": team['team'],
                        "position_diff": -pos,  # Negative for above
                        "analysis": analysis["data"]
                    })
        
        # Process teams below
        if "below" in surr_teams["data"]:
            for pos, team in enumerate(surr_teams["data"]["below"], 1):
                analysis = self.analyze_vs_team(games, team['team'], prop_type, prop_value, is_over)
                if analysis["success"]:
                    results["below"].append({
                        "team": team['team'],
                        "position_diff": pos,  # Positive for below
                        "analysis": analysis["data"]
                    })
        
        return {"success": True, "data": results}

    def find_win_pct_match(self, team_name: str, standings: Dict) -> Dict:
        """Find team in opposite conference with closest win percentage"""
        try:
            # Find team's conference and win percentage
            team_conf = None
            team_win_pct = None
            team_obj = None
            
            for conf in ['Eastern', 'Western']:
                for team in standings[conf]:
                    if team['team'] == team_name:
                        team_conf = conf
                        team_win_pct = team['win_pct']
                        team_obj = team
                        break
                if team_conf:
                    break
            
            if not team_conf:
                return {"success": False, "error": f"Team {team_name} not found in standings"}
                
            # Find closest match in opposite conference
            opp_conf = 'Western' if team_conf == 'Eastern' else 'Eastern'
            closest_team = min(
                standings[opp_conf],
                key=lambda x: abs(x['win_pct'] - team_win_pct)
            )
            
            return {
                "success": True,
                "data": closest_team
            }
            
        except Exception as e:
            print(f"Error in find_win_pct_match: {str(e)}")
            return {"success": False, "error": str(e)}

    def analyze_cross_conference(self, games: List[Dict], opponent: str, standings: Dict,
                                prop_type: str, prop_value: float, is_over: bool) -> Dict:
        """Analyze performance against similar win percentage team in opposite conference"""
        # Find matching team in opposite conference
        match_result = self.find_win_pct_match(opponent, standings)
        if not match_result["success"]:
            return match_result
            
        matched_team = match_result["data"]
        
        # Analyze performance against matched team
        direct_analysis = self.analyze_vs_team(games, matched_team['team'], prop_type, prop_value, is_over)
        
        # Analyze surrounding teams
        surr_analysis = self.analyze_surrounding_teams(
            games, matched_team['team'], standings, prop_type, prop_value, is_over
        )
        
        return {
            "success": True,
            "data": {
                "matched_team": matched_team['team'],
                "win_pct": matched_team['win_pct'],
                "direct_analysis": direct_analysis["data"],
                "surrounding_teams": surr_analysis["data"] if surr_analysis["success"] else None
            }
        }

    def calculate_overall_stats(self, games: List[Dict], prop_type: str, prop_value: float, is_over: bool) -> Dict:
        """Calculate overall season stats"""
        total_games = 0
        total_value = 0
        hits = 0
        
        stat_map = {
            'points': 'points',
            'rebounds': 'rebounds',
            'assists': 'assists',
            'steals': 'steals',
            'blocks': 'blocks',
            'threes': 'threes'
        }
        
        stat_key = stat_map.get(prop_type.lower())
        if not stat_key:
            return {"success": False, "error": "Invalid prop type"}
            
        # Calculate season stats
        for game in games:
            stat_value = game.get(stat_key, 0)
            total_value += stat_value
            total_games += 1
            
            if is_over:
                if stat_value > prop_value:
                    hits += 1
            else:
                if stat_value < prop_value:
                    hits += 1
        
        return {
            "success": True,
            "data": {
                "games_played": total_games,
                "season_average": total_value / total_games if total_games > 0 else 0,
                "season_hit_rate": (hits / total_games * 100) if total_games > 0 else 0,
                "season_hits": hits
            }
        }

    def perform_full_analysis(self, player_name: str, prop_type: str, prop_value: float,
                            opponent: str, is_over: bool, season: str = None) -> Dict:
        """Perform complete analysis using all components"""
        try:
            # Get standings
            standings_result = self.scrape_standings()
            if not standings_result["success"]:
                return standings_result
            
            # Get player's game logs for specified season
            games_result = self.get_player_games(player_name)
            if not games_result["success"]:
                return games_result
                
            # Calculate overall stats
            overall_stats = self.calculate_overall_stats(
                games_result["data"],
                prop_type,
                prop_value,
                is_over
            )
            
            # Direct matchup analysis
            direct_analysis = self.analyze_vs_team(
                games_result["data"],
                opponent,
                prop_type,
                prop_value,
                is_over
            )
            
            # Surrounding teams analysis
            surr_analysis = self.analyze_surrounding_teams(
                games_result["data"],
                opponent,
                standings_result["data"],
                prop_type,
                prop_value,
                is_over
            )
            
            # Cross-conference analysis
            cross_conf_analysis = self.analyze_cross_conference(
                games_result["data"],
                opponent,
                standings_result["data"],
                prop_type,
                prop_value,
                is_over
            )
            
            return {
                "success": True,
                "data": {
                    "overall_stats": overall_stats["data"],
                    "direct_matchup": direct_analysis["data"],
                    "surrounding_teams": surr_analysis["data"],
                    "cross_conference": cross_conf_analysis["data"]
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# Let's test the core functionality with some realistic test cases
'''
def test_analysis():
    analyzer = NBAPropsAnalyzer()
    
    # Test Case 1: LeBron James points vs Celtics
    test_lebron = analyzer.perform_full_analysis(
        player_name="Josh Hart",
        prop_type="points",
        prop_value=25.5,
        opponent="Wizards",
        is_over=True
    )
    
    if test_lebron["success"]:
        print("Test 1 - LeBron Analysis: Success")
        # Verify we're getting full season data
        total_games = test_lebron["data"]["overall_stats"]["games_played"]
        print(f"Total games found: {total_games}")
    else:
        print(f"Test 1 Failed: {test_lebron['error']}")
'''
        
def main():
    analyzer = NBAPropsAnalyzer()
    
    print("NBA Props Analyzer\n")
    
    # Get user input
    player_name = input("Enter player name: ")
    print("\nProp Types: points, rebounds, assists, steals, blocks, threes")
    prop_type = input("Enter prop type: ").lower()
    prop_value = float(input("Enter prop value: "))
    is_over = input("Over or Under? (o/u): ").lower().startswith('o')
    opponent = input("Enter opponent team: ")
    
    # Perform analysis
    result = analyzer.perform_full_analysis(player_name, prop_type, prop_value, opponent, is_over)
    
    if result["success"]:
        data = result["data"]
        prop_direction = "OVER" if is_over else "UNDER"
        
        print(f"\n=== Analysis for {player_name} {prop_direction} {prop_value} {prop_type} vs {opponent} ===\n")
        
        # Overall season stats
        overall = data["overall_stats"]
        print(f"Season Overview:")
        print(f"Season Average: {overall['season_average']:.1f}")
        print(f"Season Hit Rate: {overall['season_hit_rate']:.1f}% ({overall['season_hits']}/{overall['games_played']})\n")
        
        # Direct matchup results
        print("Direct Matchup Analysis:")
        direct = data["direct_matchup"]
        print(f"Games vs {opponent}: {direct['games_played']}")
        if direct['games_played'] > 0:
            print(f"Average: {direct['average']:.1f}")
            print(f"Hit Rate: {direct['hit_rate']:.1f}% ({direct['hit_count']}/{direct['games_played']})")
            print("\nPerformances:")
            for perf in direct['performances']:
                hit_marker = "✓" if perf['hit'] else "✗"
                print(f"{perf['date']}: {perf['value']} {hit_marker}")
        
        # Surrounding teams results
        print("\nConference Standing Analysis:")
        surr = data["surrounding_teams"]
        
        def print_team_analysis(team_data, position_text):
            print(f"\n{team_data['team']} ({position_text}):")
            analysis = team_data["analysis"]
            print(f"Games Played: {analysis['games_played']}")
            if analysis['games_played'] > 0:
                print(f"Average: {analysis['average']:.1f}")
                print(f"Hit Rate: {analysis['hit_rate']:.1f}% ({analysis['hit_count']}/{analysis['games_played']})")
                for perf in analysis['performances']:
                    hit_marker = "✓" if perf['hit'] else "✗"
                    print(f"{perf['date']}: {perf['value']} {hit_marker}")
        
        if surr["above"]:
            print("\nTeams Above:")
            for team in surr["above"]:
                print_team_analysis(team, f"{abs(team['position_diff'])} position(s) above")
        
        if surr["below"]:
            print("\nTeams Below:")
            for team in surr["below"]:
                print_team_analysis(team, f"{team['position_diff']} position(s) below")
        
        # Cross-conference analysis
        print("\nCross-Conference Analysis:")
        cross = data["cross_conference"]
        print(f"Matched Team: {cross['matched_team']} (Win%: {cross['win_pct']:.3f})")
        
        direct_cross = cross["direct_analysis"]
        print(f"\nGames vs {cross['matched_team']}: {direct_cross['games_played']}")
        if direct_cross['games_played'] > 0:
            print(f"Average: {direct_cross['average']:.1f}")
            print(f"Hit Rate: {direct_cross['hit_rate']:.1f}% ({direct_cross['hit_count']}/{direct_cross['games_played']})")
            print("\nPerformances:")
            for perf in direct_cross['performances']:
                hit_marker = "✓" if perf['hit'] else "✗"
                print(f"{perf['date']}: {perf['value']} {hit_marker}")
        
        if cross["surrounding_teams"]:
            print("\nSurrounding Teams of Matched Team:")
            surr_cross = cross["surrounding_teams"]
            
            if surr_cross["above"]:
                print("\nTeams Above Matched Team:")
                for team in surr_cross["above"]:
                    print_team_analysis(team, f"{abs(team['position_diff'])} position(s) above")
            
            if surr_cross["below"]:
                print("\nTeams Below Matched Team:")
                for team in surr_cross["below"]:
                    print_team_analysis(team, f"{team['position_diff']} position(s) below")
    
    else:
        print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()
    #test_analysis()