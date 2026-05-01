import requests
import json
import csv
import os

class DataExtractor:
    # base url for the api
    base_url = 'https://api.clashroyale.com/v1'
    # cards dict with key as card and value as card info
    cards_info = {}

    @classmethod
    def check_status_code(cls, response):
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return True
        return False

    # get query for the any requests
    @classmethod
    def set_query(cls):
        with open("api_key.txt", "r") as f:
            API_KEY = f.read().strip('\n')
            # From the documentation:
            # Authorization header looks like this: "Authorization: Bearer API_TOKEN"
            return {"Authorization": f"Bearer {API_KEY}"}

    @classmethod
    def get_cards_info(cls, query):
        endpoint = "/cards"
        response = requests.get(cls.base_url+endpoint, params=query)
        if cls.check_status_code(response):
            return None
        ''' testing only, DELETE LATER
        filename = "data/cards_info.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            r : dict = response.json()
            p: str = json.dumps(r, indent=4)
            f.write(p)
        '''
        data = response.json()
        # just returning id but so that I can easily check if the card is a hero/champion, and also get the name of the card for easier analysis
        for card in data['items']:
            cls.cards_info[card['id']] = {
                'name':         card['name'], 
                'regular':      card['iconUrls']['medium'] if card['rarity'] != "champion" else 'N/A',
                'evo':          card['iconUrls']['evolutionMedium'] if "evolutionMedium" in card['iconUrls'].keys() else 'N/A',
                'hero_champion':card['iconUrls']['heroMedium'] if "heroMedium" in card['iconUrls'].keys() else card['iconUrls']['medium'] if card['rarity'] == "champion" else 'N/A',
                'elixir':       card['elixirCost'] if 'elixirCost' in card.keys() else 'N/A' # forgor about mirror
                }

# this is the current most important function
    # grabbing the current top 1000 players, then just grabbing their player tags
    @classmethod
    def get_top_global_players(cls, query):
        endpoint = "/locations/global/pathoflegend/players"
        response = requests.get(cls.base_url+endpoint, params=query, timeout=30)
        if cls.check_status_code(response):
            return None
        data = response.json()
        player_tags = []
        for player in data['items']:
            player_tags.append(player['tag'].replace('#', '%23'))
        ''' for testing, can use if we want to see the list
        filename = "data/top_1000_players.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            json.dump(player_tags, f)
        '''
        return player_tags

    # method to get complete battle logs for a player
    @classmethod
    def get_battle_logs(cls, query, player_tag):
        endpoint = f"/players/{player_tag}/battlelog"
        response = requests.get(cls.base_url+endpoint, params=query, timeout=30)
        if cls.check_status_code(response):
            return None
        ''' for testing, visualize the battle logs for one player
        filename = f"data/battle_logs/{player_tag}.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            r : dict = response.json()
            p: str = json.dumps(r, indent=4)
            f.write(p)
        #'''
        return response.json()

    '''
        d check (but dont keep):
            d gameMode['id']
            d isHostedMatch
        keep:
            d battleTime
            d team["crowns"] --> compare to opps crowns to determine win or loss
            d team["cards"]
                Important:  keep just ID of card, but also seperate first 3 cards
                                keep hero/champion in seperate from evos
                            keep in mind  that team[cards[0]] & team[cards[2]] are evos
                                while team[cards[1]] is the hero/champion
                            sort other 5 cards by id
            d team['supportCards']["id"]
            opponent["crowns"] --> compare to opps crowns to determine win or loss
            opponent["cards"]
                Important:  keep just ID of card, but also seperate first 3 cards
                                keep hero/champion in seperate from evos
                            keep in mind  that opponent[cards[0]] & opponent[cards[2]] are evos
                                while opponent[cards[1]] is the hero/champion
                                check againsts cards_info data to determine if the card is a hero/champion!
                            sort other 5 cards by id
            opponent['supportCards']["id"]
        do not store into a json file, just the dictionary, then we use the dictionary
            to make a csv file with the relevant data and ready for analysis

        72000450 - ranked
        72000006 - ladder

        Am currently 60% sure that battleTime is syncronized between players
        In that case we can also compare kingTowerHitPoints and princessTowerHitPoints as safe checks
            but I will implement if we see a lot of duplicate data
    '''
    battleLog = {} # this dict will be our main data structure to hold the relevant battle data during runtime
    @classmethod
    def get_relevant_battle_data(cls, query, player_tag):
        battle_logs = cls.get_battle_logs(query, player_tag)
        
        for battle in battle_logs:
            # skip if the battle is not ranked or ladder, or if its a hosted match, or if we have already seen this battle
            if (battle['gameMode']['id'] != 72000450 and battle['gameMode']['id'] != 72000006 or 
                battle['isHostedMatch'] or battle['battleTime'] in cls.battleLog.keys()):
                continue
            player1_win = battle['team'][0]['crowns'] > battle['opponent'][0]['crowns']
            player1 = cls.player_cards_sort(battle['team'][0]['cards'], battle['team'][0]['supportCards'][0]['id'])
            player2 = cls.player_cards_sort(battle['opponent'][0]['cards'], battle['opponent'][0]['supportCards'][0]['id'])
            cls.battleLog[battle['battleTime']] = {
                "player1 win": player1_win,
                "player1 evo": player1['evo'],
                "player1 hero/champion": player1['hero/champion'],
                "player1 normal": player1['normal'],
                "player1 tower": player1['tower'],
                "player2 win": not player1_win,
                "player2 evo": player2['evo'],
                "player2 hero/champion": player2['hero/champion'],
                "player2 normal": player2['normal'],
                "player2 tower": player2['tower']
            }

    @classmethod
    def player_cards_sort(cls, cards, tower):
        sorted_cards = {"evo": [], "hero/champion": [], "normal": [], "tower": tower}
        for card in cards:
            if "evolutionLevel" in card:
                sorted_cards['evo' if card['evolutionLevel'] == 1 else 'hero/champion'].append(card['id'])
            elif card['rarity'] == "champion":
                sorted_cards['hero/champion'].append(card['id'])
            else: # regular card
                sorted_cards['normal'].append(card['id'])
        for key in sorted_cards.keys():
            if isinstance(sorted_cards[key], list):
                sorted_cards[key].sort()
        return sorted_cards
        '''
        Important:  Deck can contain, 2 evos 1 hero/champion or 2 heroes/champions and 1 evo
                    Evo in slot 1
                    Hero/champion in slot 2
                    Evo OR hero/champion in slot 3 --> This is a big problem, for 3 cards, the Wizard, Musketeer and Knight
                                                        because those three cards have both evo and hero versions
                    SOLUTION: "evolutionLevel" contains a 1 or 2, I have yet to see a 3, or if it is not either, "evolutionLevel" is non-existant
                    so check evolutionLevel for evo/heros && rarity for champions
        '''

    @classmethod
    def create_loaded_csv(cls, query):
        tags = cls.get_top_global_players(query)
        print(f"Got player tags: {len(tags)}")
        for tag in tags:
            cls.get_relevant_battle_data(query, tag)
        print(f"Got battle data: {len(cls.battleLog)}")
        with open("data/battle_data.csv", "a", newline='') as f:
            fieldnames = ['battleTime', 'player1 win', 'player1 evo', 'player1 hero/champion', 'player1 normal', 'player1 tower', 'player2 win', 'player2 evo', 'player2 hero/champion', 'player2 normal', 'player2 tower']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for battleTime, data in cls.battleLog.items():
                row = {"battleTime": battleTime}
                row.update(data)
                writer.writerow(row)
        cls.get_cards_info(query)
        with open("data/cards_info.csv", "w", newline='') as f:
            fieldnames = ['card_id', 'name', 'regular', 'evo', 'hero/champion' , 'elixir']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for card_id, data in cls.cards_info.items():
                row = {"card_id": card_id}
                row.update(data)
                writer.writerow(row)
        print("CSV files created successfully!")

''' functions that I was messing around with, does not help us atm
    # not too important, unless we want to do loc based analysis
    @classmethod
    def get_location(cls, query):
        endpoint = "/locations/global/seasonsv2"
        response = requests.get(base_url+endpoint, params=query)
        if cls.check_status_code(response):
            return None
        data = response.json()
        for location in data['items']:
            id = location['id']
            endpoint = f"/locations/{id}"
            response = requests.get(base_url+endpoint, params=query)
            if cls.check_status_code(response):
                return None
            filename = f"data/locations_info"
            if location["isCountry"]:
                filename += "/countries"
            elif not location["name"] == "International":
                filename += "/continents"
            filename += f"/{location['name'].replace(' ', '_')}.json"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "w") as f:
                r : dict = response.json()
                p: str = json.dumps(r, indent=4)
                f.write(p)

    # gamemodes other than ladder and path of legend
    # not important right now 
    @classmethod
    def get_seasons_info(cls, query):
        endpoint = "/locations/global/seasonsV2"
        response = requests.get(base_url+endpoint, params=query)
        if cls.check_status_code(response):
            return None
        filename = "data/random/seasonsV2.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            r : dict = response.json()
            p: str = json.dumps(r, indent=4)
            f.write(p)

    # season ids range from 1 (first season) to 132 (last season)
    @classmethod
    def get_leaderboards(cls, query):
        endpoint = "/leaderboards"
        response = requests.get(base_url+endpoint, params=query)
        
        if cls.check_status_code(response):
            return None
        filename = "data/leaderboards/leaderboards.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            r : dict = response.json()
            p: str = json.dumps(r, indent=4)
            f.write(p)
        data = response.json()
        for leaderboard in data['items']:
            id = leaderboard['id']
            name = leaderboard['name']
            if not name:
                name = str(id)
            endpoint = f"/leaderboard/{id}"
            response = requests.get(base_url+endpoint, params=query)
            if cls.check_status_code(response):
                return None
            filename = f"data/leaderboards/{leaderboard['name'].replace(' ', '_')}.json"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "w") as f:
                r : dict = response.json()
                p: str = json.dumps(r, indent=4)
                f.write(p)

    @classmethod
    def test_seasonID(cls, query):
        endpoint = "/locations/global/pathoflegend/138/rankings/players"
        response = requests.get(base_url+endpoint, params=query)

        if cls.check_status_code(response):
            return None
        
        filename = "data/test_seasonID.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            r : dict = response.json()
            p: str = json.dumps(r, indent=4)
            f.write(p)

        # we need this to give a value to each card
#'''