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


# Class for each game played during the season
class Game:
    def __init__(self, game_line):
        # Variable setting
        self.winner = game_line[0] # Winning team
        self.loser = game_line[3] # Losing team
        self.winner_pts = game_line[1] # Winning team pts
        self.loser_pts = game_line[4] # Losing team pts
        self.winnerLoc = game_line[2] # location relative to winner

        # If no score, sets pts to 0 instead of empty string
        if self.winner_pts == '':
            self.winner_pts = 0
        if self.loser_pts == '':
            self.loser_pts = 0
            
        self.margin = self.winner_pts - self.loser_pts # Margin of victory for winner


# Class for a team and their schedule and data
class Team:
    def __init__(self, name, schedule):
        self.schedule = schedule # List of games played (Game objects)
        self.name = name # Name of team


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
        if item not in out_list and (list2[list_counter] == ('H' or "N")):
            out_list.append(item)
        # increment counter
        list_counter += 1

    # Reset counter
    list_counter = 0

    # For each losing team, if the team isn't already in the list of every
    # team and the game was at a neutral site or an away game, add to list
    for  item in list3:
        if item not in out_list and (list2[list_counter] == ('A' or "N")):
            out_list.append(item)
        # increment counter
        list_counter += 1

    # Returns the list of every team
    return out_list


# Creates a team object
def create_team(arr, team):
    # Array for schedule of games
    schedule_arr = []

    # If a game involved the team being created, add the game to schedule_arr
    for i in range(len(arr)):
        if arr[i, 0] == team:
            game_add = Game(arr[i])
            schedule_arr.append(game_add)
        if arr[i, 3] == team:
            game_add = Game(arr[i])
            schedule_arr.append(game_add)

    # Create a team object using the team's schedule
    team1 = Team(team, schedule_arr)

    # Return the team object
    return team1


# Creates a list of team objects for every team in list
def create_team_arr(list1, arr):
    # List of team objects
    out_arr = []
    
    # For every team in the list, create a team object using createTeam
    for item in list1:
        out_arr.append(create_team(arr, item))

    # Return the array of team objects
    return out_arr

    
# Main program
def main():
    # 2024 schedule array
    file24 = r"C:/Users/digle/Documents/CFBRanking/cfb-scores-2024-a1167a301572.json"
    key24 = "1eLsWt7h0MQLnylBDi_QYnqUgcKCoY78mLvXKkt7vnXM"
    sheet24 = "Games"
    df24 = import_sheet(file24, key24, sheet24)
    arr24 = parse_data(df24)

    # 2024 list of teams
    list24 = list_of_teams(arr24)
    list24.sort()

    # 2024 array of team objects
    team_arr24 = create_team_arr(list24, arr24)


    # List of team objects test
    for item in team_arr24:
        print(item.name)
        for item2 in item.schedule:
            print('Winner: ' + item2.winner + ' - Loser: ' + item2.loser)
        print('\n')


main()
