from flask import Flask, render_template, request
from bs4 import BeautifulSoup, NavigableString, Tag
import requests
from unidecode import unidecode
import unidecode

app = Flask(__name__)
@app.route("/")
@app.route("/home")

def home():
    return render_template("bball_index_update.html")

@app.route("/result", methods= ['POST','GET'])
def result():
    #Gather all the names entered and store in an array.
    output = request.form.to_dict()
    alphabet = []
    name_list = output["name_list"].lower()
    if len(name_list)==0:
        return render_template("bball_index_update.html")
    name_arr = name_list.split(",")

    #Append the first letter of the last name of all the names in name_arr into a new array.
    #This will be used to find the players on basketball-reference.com.
    for i in range(len(name_arr)):
        if name_arr[i][0]==" ":
            name_arr[i] = name_arr[i][1:]
        full_name_arr = name_arr[i].split(" ")
        if(len(full_name_arr)==1):
            alphabet.append(full_name_arr[0][0])
        else:
            if(full_name_arr[len(full_name_arr)-1][0] not in alphabet):
                alphabet.append(full_name_arr[len(full_name_arr)-1][0])

    players = {}
    player_array = []
    player_stats = {}
    player_stats_arr = []
    for c in alphabet:
        #Access the page with all the players with a last name starting with character c.
        url = f"https://www.basketball-reference.com/players/{c}/"
        page = requests.get(url).text
        doc = BeautifulSoup(page, "html.parser")
        
        tbody = doc.tbody
        trs = tbody.contents
        #Going through the names starting with character c.
        for tr in trs:
            #Skipping navigable strings.
            if isinstance(tr, NavigableString):
                continue
            
            #Checking if the searched name is a tag and is also contained in name_arr.
            if isinstance(tr, Tag) and (unidecode.unidecode(tr.contents[0].a.text).lower() in name_arr):
                #Gathering basic data of the player.
                name, career_start, career_end, position, height, weight = tr.contents[0:6]
                final_name, final_career_start, final_career_end, final_position, final_height, final_weight = name.a.text, career_start.text, career_end.text, position.text, height.text, weight.text
                colleges = tr.contents[7]
                final_colleges = colleges.text
                goat_score = 0
                players[final_name] = {"Name": final_name, "From": final_career_start, "To": final_career_end, "Position": final_position, "Height": final_height, "Weight": final_weight, "Colleges": final_colleges, "Accolades": [], "GOAT Score": goat_score, "Stats": 0}
                player_link = str(name.a['href'])
                url = f"https://www.basketball-reference.com{player_link}/"
                page = requests.get(url).text
                doc = BeautifulSoup(page, "html.parser")

                #Collecting accolades.
                if(doc.find(id = "bling") == None):
                    arr = []
                    players[final_name]["Accolades"] = arr

                else:
                    accs = doc.find(id = "bling").contents
                    arr = []
                    for acc in accs:
                        if('a' in str(acc)):
                            arr.append(acc.a.text)
                    players[final_name]["Accolades"] = arr

                #Calculating goat_score_acc from the individual accolades
                goat_score_acc = 0
                for i in range(len(arr)):
                    if 'All Star' in arr[i]:
                        arr_split = arr[i].split('x')
                        goat_score_acc+=5*int(arr_split[0])

                    if 'MVP' in arr[i] and 'AS' not in arr[i] and 'x' in arr[i]:
                        arr_split = arr[i].split('x')
                        goat_score_acc+=30*int(arr_split[0])
                    elif 'MVP' in arr[i] and 'AS' not in arr[i] and 'x' not in arr[i]:
                        goat_score_acc+=30

                    if 'All-NBA' in arr[i] and 'x' in arr[i]:
                        arr_split = arr[i].split('x')
                        goat_score_acc+=10*int(arr_split[0])
                    else:
                        goat_score_acc+=10

                    if 'All-Defensive' in arr[i] and 'x' in arr[i]:
                        arr_split = arr[i].split('x')
                        goat_score_acc+=2*int(arr_split[0])
                    else:
                        goat_score_acc+=2
                    
                    if 'NBA Champ' in arr[i] and 'x' in arr[i]:
                        arr_split = arr[i].split('x')
                        goat_score_acc+=int(arr_split[0])
                    else:
                        goat_score_acc+=1

                    if 'Finals MVP' in arr[i] and 'x' in arr[i]:
                        arr_split = arr[i].split('x')
                        goat_score_acc+=10*int(arr_split[0])
                    else:
                        goat_score_acc+=10

                #Adding in the stats aspect of the goat score
                thead = doc.thead
                stats_labels = thead.contents[1].text.split(' ')[6:]
                tfoot = doc.tfoot
                stats_career = tfoot.contents[0].contents[5:]
                player_stats[final_name] = {'Name': final_name}
                goat_score_stats = 0

                for i in range(len(stats_career)):
                    if(stats_career[i].text == ''):
                        player_stats[final_name][stats_labels[i]] = 0
                    else:
                        player_stats[final_name][stats_labels[i]] = float(stats_career[i].text)
                
                #Accounting for the players before 1976 when stats such as steals, blocks, 3 pointers and turnovers didnt exist.
                val = False
                if('STL' not in player_stats[final_name] and 'BLK' not in player_stats[final_name] and 'TOV' not in player_stats[final_name]):
                    val = True
                if('STL' not in player_stats[final_name]):
                    player_stats[final_name]['STL'] = 0
                if('BLK' not in player_stats[final_name]):
                    player_stats[final_name]['BLK'] = 0
                if('3P%' not in player_stats[final_name]):
                    player_stats[final_name]['3P%'] = 0
                if('TOV' not in player_stats[final_name]):
                    player_stats[final_name]['TOV'] = 0
                
                player_stats_arr.append(player_stats[final_name])

                goat_score_stats += player_stats[final_name]['PTS']*10 + player_stats[final_name]['TRB']*6 + player_stats[final_name]['AST']*15 + player_stats[final_name]['STL']*20 + player_stats[final_name]['BLK']*20 - player_stats[final_name]['TOV']*10
                
                if(val==True):
                    goat_score_stats *= 1.25

                #Win Shares which show the contribution and impact to the team
                div = doc.tbody
                trs = div.contents
                goat_score_wins = 0
                for tr in trs:
                    if isinstance(tr, NavigableString):
                        continue
                    if isinstance(tr, Tag):
                        if isinstance(tr.contents[2], NavigableString):
                            continue
                        if isinstance(tr.contents[2], Tag):
                            if tr.contents[2].text == "TOT":
                                continue
                            else:
                                team_link = str(tr.contents[2].find("a")["href"])
                                url = f"https://www.basketball-reference.com{team_link}/"
                                page = requests.get(url).text
                                doc = BeautifulSoup(page, "html.parser")
                                stringer = doc.find(id = "info").find_all("p")[2].text
                                string_arr = stringer.split(",")[0].split("-")[0].split(" ")
                                losses = int(stringer.split(",")[0].split("-")[1])
                                wins = int(string_arr[len(string_arr)-1])
                                total = float(wins+losses)
                                goat_score_wins+= ((wins/total)-(losses/total))*100
                
                goat_score_acc += goat_score_acc*0.40
                goat_score_stats = goat_score_stats*0.25
                goat_score_wins = goat_score_wins*0.35
                
                goat_score = round(goat_score_acc+goat_score_stats+goat_score_wins,1)

                players[final_name]["GOAT Score"] = goat_score
                s = ''
                for i in range(len(players[final_name]["Accolades"])):
                    if('All Star' in players[final_name]["Accolades"][i] or 'NBA Champ' in players[final_name]["Accolades"][i] or 'MVP' in players[final_name]["Accolades"][i] or 'All-Defensive' in players[final_name]["Accolades"][i] or 'Def. POY' in players[final_name]["Accolades"][i] or '75th Anniv' in players[final_name]["Accolades"][i] or 'All-NBA' in players[final_name]["Accolades"][i]):
                        s+=players[final_name]["Accolades"][i]+', '
                if(len(s)==0):
                    s='None'
                else:
                    s = s[:-2]
                
                ss = str(player_stats[final_name]['PTS'])+' ppg, ' + str(player_stats[final_name]['TRB'])+' rpg, ' + str(player_stats[final_name]['AST'])+' apg, ' + str(round(player_stats[final_name]['FG%']*100,1))+'%'+' FG, ' + str(round(player_stats[final_name]['3P%']*100,1))+'%'+' 3P, ' + str(round(player_stats[final_name]['FT%']*100,1))+'%'+' FT '
                players[final_name]["Accolades"] = s
                players[final_name]["Stats"] = ss
                player_array.append(players[final_name])
    
    final_statement = ""
    sorted_array = sorted(player_array, key=lambda i: i['GOAT Score'],reverse=True)
    for item in sorted_array:
        final_statement += item["Name"] + ' > '
    final_statement = final_statement[:-3]
    return render_template("bball_index_update.html", player_array = sorted_array, final_statement = final_statement)

if __name__ == "__main__":
    app.run(debug=True,port=5005)