# Author: Mitchell John Boone
# V 1.1
# Reranks college football teams for any college football season by opponent
#   rank and win/loss margin using weighting system.
# Schedules can be found at https://www.sports-reference.com/cfb/years/
# Schedules can be imported using:
# https://docs.google.com/spreadsheets/d/1eLsWt7h0MQLnylBDi_QYnqUgcKCoY78mLvXKkt7vnXM/edit?usp=sharing


# For formatting a dataframe into an array
import numpy as np
# For retrieving sheet
import pygsheets as ps
# For checking paths
import os
# For reading csv files
import pandas as pd
# To ignore intentional warnings
import warnings
# Ignore intentional warning regarding empty dataframe cells
warnings.filterwarnings("ignore", "At least one column name in the data frame is an empty string")


# A game between two teams
class Game:
    def __init__(self, winner, loser, winner_loc, winner_pts = 0, loser_pts = 0):
        self.winner = winner # Winning team
        self.loser = loser # Losing team
        self.winner_loc = winner_loc # Location of game relative to the winner
        self.winner_pts = winner_pts # Winning team's score
        self.loser_pts = loser_pts # Losing team's score

        self.margin = self.winner_pts - self.loser_pts  # Margin of victory for winner

        # Set mutual references with Team objects
        self.winner.add_game(self)
        self.loser.add_game(self)


# A team in a season
class Team:
    def __init__(self, team_name):
        self.team_name = team_name # Team name
        self.schedule = [] # Team's schedule

    # Add games participated in to the team's schedule with mutual references to Game objects
    def add_game(self, game_add):
        if game_add not in self.schedule:
            self.schedule.append(game_add)


# A weight multiplier system to be used for ranking teams
class Weights:
    def __init__(self, wu3, w3t6, w7t13, w14t20, wo21, lu3, l3t6, l7t13, l14t20, lo21):
        self.wu3 = wu3 # # win under 3
        self.w3t6 = w3t6 # win 3-6
        self.w7t13 = w7t13 # win 7-13
        self.w14t20 = w14t20 # win 14-20
        self.wo21 = wo21 # win 21+
        self.lu3 = lu3 # loss under 3
        self.l3t6 = l3t6 # loss 3-6
        self.l7t13 = l7t13 # loss 7 to 13
        self.l14t20 = l14t20 # loss 14 to 20
        self.lo21 = lo21 # loss 21+

    # Changes a weight system to new values
    def change_weights(self, wu3, w3t6, w7t13, w14t20, wo21, lu3, l3t6, l7t13, l14t20, lo21):
            self.wu3 = wu3
            self.w3t6 = w3t6
            self.w7t13 = w7t13
            self.w14t20 = w14t20
            self.wo21 = wo21
            self.lu3 = lu3
            self.l3t6 = l3t6
            self.l7t13 = l7t13
            self.l14t20 = l14t20
            self.lo21 = lo21


# Generate a season of Game and Team objects
def create_season(file, key, sheet, csv, team_arr, game_arr):
    game_data = get_array(file, key, sheet, csv) # Array of all game data for the season
    num_games = len(game_data) # Number of games in the season
    team_data = list_of_teams(game_data) # Array of teams in the season

    fcs = Team("fcs") # For any FCS team

    team_dict = {} # Dictionary for team name strings to team objects

    # For each team in the season add the team to the array of teams and
    # the dictionary of teams
    for team in team_data:
        new_team = Team(team)
        team_arr.append(new_team)
        team_dict[team] = new_team

    game_ct = 0 # Counter for number of games

    # Up until every game in the season or the Army/Navy game add each game to the game array
    while game_ct < num_games:
        # String for winner and loser names
        winner_str = game_data[game_ct][0]
        loser_str = game_data[game_ct][3]
        # If winner in dictionary, get team's object, if not, get fcs object
        if winner_str in team_dict:
            game_winner = team_dict[winner_str]
        else:
            game_winner = fcs

        # If loser in dictionary, get team's object, if not, get fcs object
        if loser_str in team_dict:
            game_loser = team_dict[loser_str]
        else:
            game_loser = fcs

        game_loc = game_data[game_ct][2] # The location of the game relative to the winner
        w_score = int(game_data[game_ct][1]) # The score of the winner
        l_score = int(game_data[game_ct][4]) # The score of the loser

        # Create the new Game object to be added using the data from the array of games
        new_game = Game(game_winner, game_loser, game_loc, w_score, l_score)
        # Add the new Game object to the array of games
        game_arr.append(new_game)

        # If the game just added was the Army/Navy game, end the season
        if (winner_str == "Army" and loser_str == "Navy") or (winner_str == "Navy" and loser_str == "Army"):
            break

        game_ct += 1 # Increment the counter

    # No return as outputs passed as ref
    return


# Imports a spreadsheet given the file path, Google sheets key, and sheet name
# and returns a dataframe
def import_sheet(in_file, in_key, in_sheet):
    # Generates dataframe
    access = ps.authorize(service_file=in_file)
    sheet = access.open_by_key(in_key)
    tab = sheet.worksheet_by_title(in_sheet)
    df = tab.get_as_df()
    df = df.drop(axis = 1,labels = ["Rk", "Wk", "Date", "Time", "Day", "Notes"])
    df.rename(columns = {"" : "Loc"}, inplace = True)
    df.to_numpy(dtype = str)
    
    # Returns dataframe
    return df


# Parses data from a schedule array to get into a 5 column format and returns the formatted array
def parse_data(in_arr):

    # Gets rid of preset rankings in team rows and the trash rows
    def clean_data(column, clean_arr):
        # Counter for current cell
        data_count = 0
        
        for _ in clean_arr[:, column]:
            # The current cell being processed
            data_cell = clean_arr[data_count][column]
            # Adds trash rows to arr_del
            if data_cell == "Winner":
                arr_del.append(data_count)
            else:
                # Cleans up the possible formatting in the team cell
                if "(" in data_cell:
                    data_cell = data_cell.replace("(", "")
                    data_cell = data_cell.replace(") ", "")
                    data_cell = data_cell.replace("0", "")
                    data_cell = data_cell.replace("1", "")
                    data_cell = data_cell.replace("2", "")
                    data_cell = data_cell.replace("3", "")
                    data_cell = data_cell.replace("4", "")
                    data_cell = data_cell.replace("5", "")
                    data_cell = data_cell.replace("6", "")
                    data_cell = data_cell.replace("7", "")
                    data_cell = data_cell.replace("8", "")
                    data_cell = data_cell.replace("9", "")
                    # For Miami
                    data_cell = data_cell.replace(")", "")
                    clean_arr[data_count][column] = data_cell

            # Increment cell counter
            data_count += 1

        # Returns the array with the team rows cleaned
        return clean_arr
        
    # The output array
    out_arr = (np.asarray(in_arr))

    # Array of trash rows containing labels
    arr_del = []

    # Gets rid of preset rankings for both winning and losing teams
    out_arr = clean_data(0, out_arr)
    out_arr = clean_data(3, out_arr)

    # Reverse arr_del to avoid index out of bonds error
    arr_del.reverse()
    # Deletes trash rows from arr
    for i in arr_del:
        out_arr = np.delete(out_arr, i, 0)

    # Counter for current cell
    cell_count = 0

    # Formats the location column
    for _ in out_arr[:, 2]:
        # The current cell being processed
        format_cell = out_arr[cell_count][2]
        # Cleans up the possible formatting in the location cell
        if format_cell == "":
            format_cell = format_cell + "H"
        format_cell = format_cell.replace("@", "A")
        out_arr[cell_count][2] = format_cell
        # Increment cell counter
        cell_count += 1

    # Returns the formatted array
    return out_arr


# creates a list of every team
def list_of_teams(arr):
    # List of every team
    out_list = []
    # List of every winning team in each game
    list0 = arr[:, 0]
    # List of every losing team in each game
    list3 = arr[:, 3]
    # List of the location of each game
    list2 = arr[:, 2]

    # Counter for use in location checking
    list_counter = 0
    # For each winning team, if the team isn't already in the list of every
    # team and the game was at a neutral site or a home game, add to list
    for  item in list0:
        if item not in out_list and (list2[list_counter] == ("H" or "N")):
            out_list.append(item)
        # increment counter
        list_counter += 1

    # Reset counter
    list_counter = 0

    # For each losing team, if the team isn't already in the list of every
    # team and the game was at a neutral site or an away game, add to list
    for  item in list3:
        if item not in out_list and (list2[list_counter] == ("A" or "N")):
            out_list.append(item)
        # increment counter
        list_counter += 1

    # Sorts the list of teams by school name
    out_list.sort()

    # Returns the list of every team
    return out_list


# Gets data from a csv file, creating one with the Google sheet if necessary
def get_array(file_imp, key_imp, sheet_imp, csv_file):
    # If the csv file does not already exist
    if not os.path.exists(csv_file):
        # Import and parse the data from the Google sheet
        df = import_sheet(file_imp, key_imp, sheet_imp)
        data_arr = parse_data(df)
        # Create a csv file for the future
        np.savetxt(csv_file, data_arr, fmt="%s", delimiter = ",")

    # Uses the csv file to get the array
    return get_array_csv(csv_file)


# Gets array data from a csv file
def get_array_csv(csv_file):
    # Import and parse the data from the csv file
    df = pd.read_csv(csv_file, header=None)
    data_arr = parse_data(df)

    # Returns the array of data
    return data_arr

    
# Main program
def main():
    # 2024 schedule array data
    file24 = r"C:/Users/digle/Documents/CFBRanking/cfb-scores-2024-a1167a301572.json"
    key24 = "1eLsWt7h0MQLnylBDi_QYnqUgcKCoY78mLvXKkt7vnXM"
    sheet24 = "Games"
    csv24 = "array24.csv"
    # 2024 season test with a season
    game_arr24 = []
    team_arr24 = []
    create_season(file24, key24, sheet24, csv24, team_arr24, game_arr24)

    # Team print test
    # ct = 1
    # for team in team_arr24:
    #     print(ct)
    #     print(team.team_name)
    #     ct += 1

    # Game print test
    # ct = 1
    # for game in game_arr24:
    #     print(f"{game.winner.team_name}: {game.winner_pts} - {game.loser.team_name}: {game.loser_pts} - Margin: {game.margin} - Loc: {game.winner_loc}")
    #     ct += 1

main()
