# Author: Mitchell John Boone
# V 1.1
# Reranks college football teams for any college football season by opponent
#   rank and win/loss margin using weighting system.
# Schedules can be found at https://www.sports-reference.com/cfb/years/
# Schedules can be imported using:
# https://docs.google.com/spreadsheets/d/1eLsWt7h0MQLnylBDi_QYnqUgcKCoY78mLvXKkt7vnXM/edit?usp=sharing


from io import StringIO

# For retrieving sheet
import pygsheets as ps
# For formatting a dataframe into an array
import numpy as np


# Class for each game played during the season
class Game:
    def __init__(self, gameLine):
        # Variable setting
        self.winner = gameLine[0] # Winning team
        self.loser = gameLine[3] # Losing team
        self.winnerPts = gameLine[1] # Winning team pts
        self.loserPts = gameLine[4] # Losing team pts
        self.winnerLoc = gameLine[2] # location relative to winner

        # If no score, sets pts to 0 instead of empty string
        if self.winnerPts == '':
            self.winnerPts = 0
        if self.loserPts == '':
            self.loserPts = 0
            
        self.margin = self.winnerPts - self.loserPts # Margin of victory for winner


# Class for a team and their schedule and data
class Team:
    def __init__(self, name, schedule):
        self.schedule = schedule # List of games played (Game objects)
        self.name = name # Name of team


# Imports a spreadsheet given the file path, Google sheets key, and sheet name
# and returns a dataframe
def importSheet(inFile, inKey, inSheet):
    # Generates dataframe
    access = ps.authorize(service_file=inFile)
    sheet = access.open_by_key(inKey)
    tab = sheet.worksheet_by_title(inSheet)
    df = tab.get_as_df()
    df = df.drop(axis = 1,labels = ["Rk", "Wk", "Date", "Time", "Day", "Notes"])
    df.rename(columns = {"" : "Loc"}, inplace = True)
    df.to_numpy(dtype = str)
    
    # Returns dataframe
    return df


# Parses data from a schedule array to get into a 5 column format and returns the formatted array
def parseData(inArr):

    # Gets rid of preset rankings in team rows and the trash rows
    def cleanData(column, cleanArr):
        # Counter for current cell
        count = 0
        
        for i in cleanArr[:, column]:
            # The current cell being processed
            cell = cleanArr[count][column]
            # Adds trash rows to arrDel
            if cell == "Winner":
                arrDel.append(count)
            else:
                # Cleans up the possible formatting in the team cell
                if "(" in cell:
                    cell = cell.replace("(", "")
                    cell = cell.replace(") ", "")
                    cell = cell.replace("0", "")
                    cell = cell.replace("1", "")
                    cell = cell.replace("2", "")
                    cell = cell.replace("3", "")
                    cell = cell.replace("4", "")
                    cell = cell.replace("5", "")
                    cell = cell.replace("6", "")
                    cell = cell.replace("7", "")
                    cell = cell.replace("8", "")
                    cell = cell.replace("9", "")
                    # For Miami
                    cell = cell.replace(")", "")
                    cleanArr[count][column] = cell

            # Increment cell counter
            count += 1

        # Returns the array with the team rows cleaned
        return cleanArr
        
    # The output array
    outArr = (np.asarray(inArr))

    # Array of trash rows containing lables
    arrDel = []

    # Gets rid of preset rankings for both winning and losing teams
    outArr = cleanData(0, outArr)
    outArr = cleanData(3, outArr)

    # Reverse arrDel to avoid index out of bonds error
    arrDel.reverse()
    # Deletes trash rows from arr
    for i in arrDel:
        outArr = np.delete(outArr, i, 0)

    # Counter for current cell
    count = 0

    # Formats the location column
    for i in outArr[:, 2]:
        # The current cell being processed
        cell = outArr[count][2]
        # Cleans up the possible formatting in the location cell
        if cell == "":
            cell = cell.replace("", "H")
        cell = cell.replace("@", "A")
        outArr[count][2] = cell
        # Increment cell counter
        count += 1

    # Returns the the formatted array
    return outArr


# creates a list of every team
def listOfTeams(arr):
    # List of every team
    outList = []
    # List of every winning team in each game
    list0 = arr[:, 0]
    # List of every losing team in each game
    list3 = arr[:, 3]
    # List of the location of each game
    list2 = arr[:, 2]

    # Counter for use in location checking
    counter = 0
    # For each winning team, if the team isn't already in the list of every
    # team and the game was at a neutral site or a home game, add to list
    for  item in list0:
        if item not in outList and (list2[counter] == ('H' or "N")):
            outList.append(item)
        # increment counter
        counter += 1

    # Reset counter
    counter = 0
    # Counter for use in location checking
    counter = 0
    # For each losing team, if the team isn't already in the list of every
    # team and the game was at a neutral site or an away game, add to list
    for  item in list3:
        if item not in outList and (list2[counter] == ('A' or "N")):
            outList.append(item)
        # increment counter
        counter += 1

    # Returns the list of every team
    return outList


# Creates a team object
def createTeam(list1, arr, team):
    # Array for schedule of games
    scheduleArr = []

    # If a game involved the team being created, add the game to scheduleArr
    for i in range(len(arr)):
        if arr[i, 0] == team:
            gameAdd = Game(arr[i])
            scheduleArr.append(gameAdd)
        if arr[i, 3] == team:
            gameAdd = Game(arr[i])
            scheduleArr.append(gameAdd)

    # Create a team object using the team's schedule
    team1 = Team(team, scheduleArr)

    # Return the team object
    return team1


# Creates a list of team objects for every team in list
def createTeamArr(list1, arr):
    # List of team objects
    outArr = []
    
    # For every team in the list, create a team object using createTeam
    for item in list1:
        outArr.append(createTeam(list1, arr, item))

    # Return the array of team objects
    return outArr

    
# Main program
def main():
    # 2024 schedule array
    file24 = r"C:/Users/digle/Documents/CFBRanking/cfb-scores-2024-a1167a301572.json"
    key24 = "1eLsWt7h0MQLnylBDi_QYnqUgcKCoY78mLvXKkt7vnXM"
    sheet24 = "Games"
    df24 = importSheet(file24, key24, sheet24)
    arr24 = parseData(df24)

    # 2024 list of teams
    list24 = listOfTeams(arr24)
    list24.sort()

    # 2024 array of team objects
    teamArr24 = createTeamArr(list24, arr24)


    # List of team objects test
    for item in teamArr24:
        print(item.name)
        for item2 in item.schedule:
            print('Winner: ' + item2.winner + ' - Loser: ' + item2.loser)
        print('\n')


main()
