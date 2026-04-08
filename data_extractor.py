import requests
import json
import os

class DataExtractor:
    # base url for the api
    global base_url
    base_url = 'https://api.clashroyale.com/v1'

    # get query for the any requests
    def set_query():
        with open("api_key.txt", "r") as f:
            API_KEY = f.read().strip('\n')
            # From the documentation:
            # Authorization header looks like this: "Authorization: Bearer API_TOKEN"
            return {"Authorization": f"Bearer {API_KEY}"}

    def get_cards_info(query):
        endpoint = "/cards"
        response = requests.get(base_url+endpoint, params=query)

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return None
        
        filename = "data/cards_info.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            r : dict = response.json()
            p: str = json.dumps(r, indent=4)
            f.write(p)
    
    def get_locations(query):
        endpoint = "/locations"
        response = requests.get(base_url+endpoint, params=query)

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return None
        
        filename = "data/locations.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            r : dict = response.json()
            p: str = json.dumps(r, indent=4)
            f.write(p)

    def get_location(query):
        endpoint = "/locations/global/seasonsv2"
        response = requests.get(base_url+endpoint, params=query)

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return None
        
        id = response.json()[0]['id']
        print(id)
        endpoint = f"/locations/global/seasons/{id}/rankings/players"
        response = requests.get(base_url+endpoint, params=query)
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return None
        filename = "data/location.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            r : dict = response.json()
            p: str = json.dumps(r, indent=4)
            f.write(p)

    def get_locations_info(query):
        with open("data/locations.json", "r") as f:
            data = json.load(f)
            for location in data['items']:
                id = location['id']
                endpoint = f"/locations/{id}"
                response = requests.get(base_url+endpoint, params=query)
                if response.status_code != 200:
                    print(f"Error: {response.status_code}")
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

    # all of the random requests that idk
    def get_seasons_info(query):
        endpoint = "/locations/global/seasonsV2"
        response = requests.get(base_url+endpoint, params=query)

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return None

        filename = "data/random/seasonsV2.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            r : dict = response.json()
            p: str = json.dumps(r, indent=4)
            f.write(p)
    
    # season ids range from 1 (first season) to 82 (current season)

    def get_leaderboards(query):
        endpoint = "/leaderboards"
        response = requests.get(base_url+endpoint, params=query)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return None
        
        data = response.json()
        for leaderboard in data['items']:
            id = leaderboard['id']
            endpoint = f"/leaderboard/{id}"
            response = requests.get(base_url+endpoint, params=query)
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                return None
            filename = f"data/leaderboards/{leaderboard['id']}.json"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "w") as f:
                r : dict = response.json()
                p: str = json.dumps(r, indent=4)
                f.write(p)
    ''' # not as important
    /locations/{locationId}/rankings/clans
        Get clan rankings for a specific location 
    
    /locations/{locationId}/rankings/clanwars
        Get clan war rankings for a specific location
    
    /locations/global/rankings/tournaments/{tournamentTag}
        Get global tournament rankings
    '''


    '''
    important: to get global live ranking, use /locations/global/rankings/players
    /locations/{locationId}/rankings/players
        Get player rankings for a specific location
    
    /locations/global/pathoflegend/{seasonId}/rankings/players
        Get top Path of Legend players for given season.
    
    /locations/global/seasons/{seasonId}
        Get top player league season.
    
    /locations/global/seasons/{seasonId}/rankings/players
        Get top player rankings for a season.
    
    /locations/{locationId}/pathoflegend/players
        Get player rankings in Path of Legend for a specific location
    '''