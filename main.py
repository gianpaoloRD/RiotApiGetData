from datetime import datetime
import json
import time
from collections.abc import Iterable
import pandas as pd
from riotwatcher import LolWatcher, ApiError


def flatten_json(json_data, parent_key='', separator='_'):
    items = {}
    for key, value in json_data.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(flatten_json(value, new_key, separator=separator))
        elif isinstance(value, Iterable) and not isinstance(value, str):
            for i, item in enumerate(value, start=1):
                items.update(flatten_json({str(i): item}, new_key, separator=separator))
        else:
            items[new_key] = value
    return items


def make_api_request(matchId,region):
    try:
        response = lol_watcher.match.timeline_by_match(region, matchId)
        return response
    except ApiError as err:
        if err.response.status_code == 429:
            print('We should retry in {} seconds.'.format(err.headers['Retry-After']))
            print('this retry-after is handled by default by the RiotWatcher library')
            print('future requests wait until the retry-after time passes')
            return None
        elif err.response.status_code == 404:
            print('Summoner with that ridiculous name not found.')
            return None


def convertToCsv(matchId,region):
    my_ranked_stats = make_api_request(matchId,region)
    if my_ranked_stats is not None:
        # Convert and write JSON object to file


        with open("sample.json", "w") as outfile:
            json.dump(my_ranked_stats, outfile, indent=4)

        with open("sample.json", "r") as outfile:
            json_data = json.load(outfile)

        # print(json_data)

        matches = json_data["info"]["frames"]
        list_of_dicts = []
        for i in range(len(matches) - 1):
            list_of_dicts.append(flatten_json(matches[i]["participantFrames"]))

        # item = flatten_json(matches[1]["participantFrames"])

        df = pd.DataFrame([list_of_dicts[0]])

        for d in range(1, len(list_of_dicts)):
            df = pd.concat([df, pd.DataFrame([list_of_dicts[d]])])

        df["matchId"] = [json_data["metadata"]["matchId"]] * len(df)

        timestamp_ms = json_data["info"]["frames"][0]["events"][0]["realTimestamp"]
        timestamp_seconds = timestamp_ms / 1000  # Convert milliseconds to seconds
        formatted_time = datetime.utcfromtimestamp(timestamp_seconds).strftime('%Y_%m_%d-%H_%M_%S')
        print(formatted_time)
        df.to_csv(output_path + "MatchTimeline_" + formatted_time + ".csv")





lol_watcher = LolWatcher('developer key here from riot developer') # you ned you own developer key

my_region = 'NA1' # region from the data is from

#me = lol_watcher.summoner.by_name("na1", 'jamoon')
#print(me)

# all objects are returned (by default) as a dict
# lets see if i got diamond yet (i probably didn`t)

input_path = "data/Input/"
output_path = "data/Output/"
dfMatch = pd.read_csv(input_path + "matchId.csv")

# First we get the latest version of the game from data dragon
# versions = lol_watcher.data_dragon.versions_all()
# champions_version = versions[1]

# Lets get some champions
# current_champ_list = lol_watcher.data_dragon.champions(champions_version)
# print(current_champ_list)

# For Riot's API, the 404 status code indicates that the requested data wasn't found and
# should be expected to occur in normal operation, as in the case of a an
# invalid summoner name, match ID, etc.
#
# The 429 status code indicates that the user has sent too many requests
# in a given amount of time ("rate limiting").

try:

    for i in dfMatch["match_ids"]:
        print(i)
        convertToCsv(i,region)
        time.sleep(2)

    # response = lol_watcher.match.timeline_by_match("la1", "LA1_1474062571")
    # response = lol_watcher.summoner.by_name(my_region, 'jamoon')
except ApiError as err:
    if err.response.status_code == 429:
        print('We should retry in {} seconds.'.format(err.headers['Retry-After']))
        print('this retry-after is handled by default by the RiotWatcher library')
        print('future requests wait until the retry-after time passes')
    elif err.response.status_code == 404:
        print('Summoner with that ridiculous name not found.')
    else:
        raise
except IndexError as e:
        print(f"An IndexError occurred: {e}")
