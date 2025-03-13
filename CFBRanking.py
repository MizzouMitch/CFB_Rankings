# Author: Mitchell John Boone
# V 1.1
# Reranks college football teams for any college football season by opponent
#   rank and win/loss margin using a weight system.
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
# For deepcopy
import copy
# To ignore intentional warning regarding empty dataframe cells
import warnings
warnings.filterwarnings("ignore", "At least one column name in the data frame is an empty string")
# For deepcopy recursion depth error
import sys
sys.setrecursionlimit(10000)
# For formatting columns
from tabulate import tabulate
# For exact calculations
from decimal import *
import math


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
        self.rank_pts = 1 # Team's rank pts
        self.rank = 135 # Team's rank

    # Add games participated in to the team's schedule with mutual references to Game objects
    def add_game(self, game_add):
        if game_add not in self.schedule:
            self.schedule.append(game_add)


# A weight multiplier system to be used for ranking teams
class Weights:
    def __init__(self, wu3, w3t6, w7t13, w14t20, wo21, lu3, l3t6, l7t13, l14t20, lo21, loch, loca, locn, exp_mult = 1.0):
        self.wu3 = Decimal(wu3) # win under 3
        self.w3t6 = Decimal(w3t6) # win 3-6
        self.w7t13 = Decimal(w7t13) # win 7-13
        self.w14t20 = Decimal(w14t20) # win 14-20
        self.wo21 = Decimal(wo21) # win 21+
        self.lu3 = Decimal(lu3) # loss under 3
        self.l3t6 = Decimal(l3t6) # loss 3-6
        self.l7t13 = Decimal(l7t13) # loss 7 to 13
        self.l14t20 = Decimal(l14t20) # loss 14 to 20
        self.lo21 = Decimal(lo21) # loss 21+

        self.loch = Decimal(loch) # Game at home
        self.loca = Decimal(loca) # Game on road
        self.locn = Decimal(locn) # Game at neutral site

        self.exp_mult = Decimal(exp_mult) # Power rank to be raised to for exp weight increase for team weights


    # Changes a weight system to new values
    def change_weights(self, wu3, w3t6, w7t13, w14t20, wo21, lu3, l3t6, l7t13, l14t20, lo21, loch, loca, locn, exp_mult = 1.0):
        self.__init__(wu3, w3t6, w7t13, w14t20, wo21, lu3, l3t6, l7t13, l14t20, lo21, loch, loca, locn, exp_mult)


# Generate a season of Game and Team objects
def create_season(file, key, sheet, csv, team_arr, game_arr):
    game_data = get_array(file, key, sheet, csv) # Array of all game data for the season
    num_games = len(game_data) # Number of games in the season
    team_data = list_of_teams(game_data) # Array of teams in the season

    fcs = Team("fcs")  # For any FCS team

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
# noinspection PyUnresolvedReferences
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
        # noinspection PyUnresolvedReferences
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


# Ranks a team given a Team object and a weight system
def rank_team(team_static, team_update, weight_system, num_teams):

    # Calculates the rank pts for a single game
    def calc_game_rank_pts():

        # Gets the game's location relative to the team being ranked
        def get_loc_rel_team():
            # If the team won, the location is the winner location
            if won:
                ret_loc = game.winner_loc
            # If the team lost, the location is the inversion of the winner location
            else:
                if game.winner_loc == "A":
                    ret_loc = "H"
                elif game.winner_loc == "H":
                    ret_loc = "A"
                # Neutral site is same for both winner and loser
                else:
                    ret_loc = "N"

            # Return the location relative to the team being ranked
            return ret_loc


        # Gets the weight for the game based on the location
        def get_loc_weight():
            # Assign the weight based on the location
            if loc == "H":
                ret_weight = weight_system.loch
            elif loc == "A":
                ret_weight = weight_system.loca
            else:
                ret_weight = weight_system.locn

            # Return the weight for the location
            return ret_weight


        loc = get_loc_rel_team() # The location relative to the team being ranked
        loc_weight = get_loc_weight() # The location weight
        rank_weight = (num_teams + 2 - opp.rank) ** weight_system.exp_mult # The rank weight

        # Calculate the rank pts for the game
        ret_rank_pts = rank_weight * margin_weight * loc_weight

        # Return the rank pts for the game
        return ret_rank_pts


    new_rank_pts = 0 # The new rank pts for the team

    # Add the rank pts for each game to the new rank pts
    for game in team_static.schedule:

        margin = game.margin # The margin for the game

        # Checks to see if the team won or lost the game
        if team_static.team_name == game.winner.team_name:
            won = True
        else:
            won = False

        # If the team won, the opponent is the loser
        opp = game.loser

        # If the team lost, invert the margin and make the opponent the winner
        if not won:
            margin = -margin
            opp = game.winner

        # Gets the margin weight from the weight system using the margin
        match margin:
            case n if n >= 21:
                margin_weight = weight_system.wo21
            case n if n >= 14:
                margin_weight = weight_system.w14t20
            case n if n >= 7:
                margin_weight = weight_system.w7t13
            case n if n >= 3:
                margin_weight = weight_system.w3t6
            case n if n >= 1:
                margin_weight = weight_system.wu3
            case n if n <= -21:
                margin_weight = weight_system.lo21
            case n if n <= -14:
                margin_weight = weight_system.l14t20
            case n if n <= -7:
                margin_weight = weight_system.l7t13
            case n if n <= -3:
                margin_weight = weight_system.l3t6
            case n if n <= -1:
                margin_weight = weight_system.lu3

        # Adds the rank pts for the game to the total for the new rank pts
        new_rank_pts += calc_game_rank_pts()

    # Updates the team's rank pts to the new rank pts divided by the number of games played
    team_update.rank_pts = int(new_rank_pts / len(team_static.schedule))

    # No return as output passed as ref
    return


# Ranks teams by rank pts
def rank_teams_pts(teams, weight_system):
    num_teams = len(teams)  # The number of teams
    finished = False # True if rankings are finalized
    it_ct = 0 # To break if no squeeze answer
    teams_new = teams
    # While rankings aren't finalized
    while not finished:
        it_ct += 1
        # print(it_ct)
        teams_old = copy.deepcopy(teams_new) # The old ranks to be used in the calculations
        teams_new = teams # The new ranks which will be updated

        # Rank each team using teams_old and updating teams_new
        team_ct = 0 # Current team counter
        while team_ct < num_teams:
            rank_team(teams_old[team_ct], teams_new[team_ct], weight_system, num_teams)
            team_ct += 1

        # Sort the teams by rank pts
        teams_new.sort(key=lambda x: x.rank_pts, reverse=True)

        # Rerank the teams once sorted
        team_rank = 1 # Current team's rank
        for team in teams_new:
            prev_team = teams_new[team_rank - 2] # The previous team's rank
            # If the previous team has the same rank pts as the current team, they both get same rank
            if team.rank_pts == prev_team.rank_pts:
                team.rank = prev_team.rank
            else:
                team.rank = team_rank
            team_rank += 1

        # Finish ranking if no squeeze after 250 iterations
        if it_ct == 250:
            print("\nNo answer could be squeezed completely - Ranks could differ slightly per sequence in iteration loop")
            finished = True

        # Check if the rankings are finalized by seeing if they match the previous rankings
        team_check_finished = False
        team_check_ct = 0 # Counter to stop when every team matches
        while not team_check_finished:
            if teams_new[team_check_ct].team_name == teams_old[team_check_ct].team_name:
                team_check_ct += 1
                # If every team matches, set both finished variables to true
                if team_check_ct == num_teams:
                    finished = True
                    team_check_finished = True
                    print(f"\nIterations for solution: {it_ct}")
            # If the rankings aren't matching, finish the team check and move on to next rankings
            else:
                # print(f"Failed at check: {team_check_ct}")
                team_check_finished = True


        # print_rankings(teams_new, 2024) # For testing

    # No return as output passed as ref
    return


# Prints the rankings
def print_rankings(team_arr, year):
    ranking_arr = [] # Array for print formatting
    headers = ["Rank", "Team name", "Pts"] # Headers for print formatting
    # Populate array for print formatting
    for team in team_arr:
        ranking_arr.append([team.rank, team.team_name, team.rank_pts])
    print(f"\n{year} Rankings:\n") # Print the year of the rankings
    print(tabulate(ranking_arr, headers = headers)) # Print the formatted rankings

    
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


    # rank_team_pts Test
    weights1 = Weights(3.5, 3.8, 4.1, 4.6, 5, 1.7, 1.4, 0.9, 0.5, 0.1, 1, 2, 1.5)

    weights1.change_weights(2.0, 2.2, 2.4, 2.6, 2.8, 0.5, 0.25, 0.1, 0.05, 0.01, 1, 1.5, 1.25, 1.5)

    # weights1.change_weights(2.0, 2.2, 2.4, 2.5, 2.6, 1.0, 0.8, 0.3, 0.20, 0.10, 1, 1.5, 1.25)

    rank_teams_pts(team_arr24, weights1)

    print_rankings(team_arr24, 2024)


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
