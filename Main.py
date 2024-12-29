import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, List, Optional, Union

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
            
            if 'items' in data and len(data['items']) > 0:
                for item in data['items']:
                    if item['displayName'].lower() == player_name.lower():
                        return {"success": True, "id": item['id']}
                return {"success": True, "id": data['items'][0]['id']}
            return {"success": False, "error": "Player not found"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_player_games(self, player_name: str) -> Dict:
        """Get player's game logs"""
        player_id_result = self.get_player_id(player_name)
        if not player_id_result["success"]:
            return player_id_result
        
        player_id = player_id_result["id"]
        url = f"https://www.espn.com/nba/player/gamelog/_/id/{player_id}"
        
        try:
            print(f"Fetching game logs...")
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Print raw HTML for debugging
            print("\nDebug - Looking for game log table...")
            
            table = soup.find('table', class_='Table')
            if not table:
                print("No table found")
                return {"success": False, "error": "Game log table not found"}
            
            games = []
            rows = table.find_all('tr')[2:]  # Skip header rows
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 15:  # Make sure row has enough columns
                    try:
                        # Print raw data for debugging
                        print(f"\nDebug - Processing game: {cells[0].text.strip()} vs {cells[1].text.strip()}")
                        
                        game_data = {
                            'date': cells[0].text.strip(),
                            'opponent': self.clean_team_name(cells[1].text.strip()),
                            'minutes': cells[2].text.strip(),
                            'fg': cells[3].text.strip(),
                            'threes': cells[4].text.strip(),
                            'ft': cells[5].text.strip(),
                            'rebounds': cells[6].text.strip(),
                            'assists': cells[7].text.strip(),
                            'blocks': cells[8].text.strip(),
                            'steals': cells[9].text.strip(),
                            'points': cells[10].text.strip()
                        }
                        games.append(game_data)
                        print(f"Debug - Processed game: {game_data['points']} points against {game_data['opponent']}")
                    except IndexError as e:
                        print(f"Debug - Error processing row: {str(e)}")
                        continue
            
            print(f"\nFound {len(games)} games")
            return {"success": True, "data": games}
            
        except Exception as e:
            print(f"Debug - Exception: {str(e)}")
            return {"success": False, "error": str(e)}

def main():
    analyzer = NBAPropsAnalyzer()
    
    # Test player game log retrieval
    player_name = input("Enter player name: ")
    games_result = analyzer.get_player_games(player_name)
    
    if games_result["success"]:
        print(f"\nLast 5 games for {player_name}:")
        for game in games_result["data"][:5]:
            print(f"{game['date']} vs {game['opponent']}: {game['points']} points, {game['rebounds']} rebounds, {game['assists']} assists")
    else:
        print(f"Error: {games_result['error']}")

if __name__ == "__main__":
    main()