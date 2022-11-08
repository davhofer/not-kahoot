from flask import Flask, redirect, url_for, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET'] = 'secretkey'

socketio = SocketIO(app)


games = dict()
players = dict()
player_by_sid = dict()



# TODO: divide different games into different rooms
# TODO: make leaderboard animation
# TODO: final screen with leaderboard and top 3?
# TODO: save and load quizzes from json, make a viewer

# TODO: make more "Kahoot-like"



# TODO: each question should have at least 2 answers (?)


'''
log some output to stdout on the server
'''
def log(msg):
    print("===== LOG =====\n" + str(msg) + "\n")

'''
Index page, initially shown to the user. Redirects to an existing game when provided with a gameId.
'''
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        # show the index page
        return render_template('index.html')
    else: # request.method == POST
        # post request is made if the user is looking to join an existing game, providing an id
        gameId = request.form['gameId']
        return redirect(url_for('game', game_id=gameId))


'''
Page where the user can create a new quiz. Each quiz can contain an unlimited number of questions, and each question can contain up to 4 answers.
'''
@app.route('/create/', methods=['GET', 'POST'])
def create():
    global games
    if request.method == 'GET':
        # initially, show the page with the blank form
        return render_template('create_quiz.html')

    else: # request.method == POST
    # post request is made if the user sends the filled out form with questions and answers

        # get next id (could also choose a random value between e.g. 00000 and 99999)
        gameId = len(games)

        # check how many questions the user entered, and store them together with the answers in a dict
        i = 0
        questions = []
        while True:
            # check for next question in the submitted form
            if f'q{i}' not in request.form.keys():
                break

            question = request.form[f'q{i}'] 

            # get the 4 answers (but leave empty answers away)
            answers = [request.form[f'{i}_a{j}'] for j in range(4) if request.form[f'{i}_a{j}'] != '']

            # TODO: should be at least 2 answers


            i += 1

            # if question was empty, skip before storing
            if question == '':
                continue 
            
            questions.append({'question': question, 'answers': answers})


        # game is represented as a dict, containing all necessary info and various flags
        games[gameId] = {'questions': questions, 'initialized': False, 'hasStarted': False, 'host_sid': None, 'players': dict(), 'next_question': 0, 'player_answers': [[] for _ in range(len(questions))], 'num_players': 0}


        return redirect(url_for('game', game_id=gameId))




'''
Returns game page, the place where all the action happens. A game with a given id can be accessed by just adding <id>/ to the homepage link.
'''
@app.route('/<game_id>/')
def game(game_id):
    global games 
    game_id = int(game_id)

    # check that game exists
    if game_id not in games.keys():
        return f"<h2>This game does not exist!</h2>"

    current_game = games[game_id]

    # if this game has not yet been initialized, we are the host
    host_flag = not current_game['initialized']

    # if the game has not yet been started, go to the lobby
    lobby_flag = not current_game['hasStarted']

    current_game['initialized'] = True

    # if game has already been initialized and has started: cannot join anymore
    if not host_flag:
        if not lobby_flag:
            return f"<h2>This game has already started!</h2>"

    # get players that have joined so far
    players = current_game['players']
    player_list = list(players.keys())

    # show page
    return render_template('game.html', id=game_id, isHost=host_flag, player_list=player_list)

'''
event that gets triggered when the host (first connection) joins.
used to identify the session id (connection) to the host
'''
@socketio.event
def host_join(data):
    if data['ishost'] == 'True':
        # store their session id
        games[int(data['gameId'])]['host_sid'] = request.sid


'''
event that gets triggered when a new player submits his name
'''
@socketio.event
def player_join(data):

    displayname = data['displayname']
    gameId = int(data['gameId'])

    # TODO: make sure no duplicate playernames

    if games[gameId]['hasStarted']:
        # cannot join anymore
        return 

    players = games[gameId]['players']

    # create new player
    players[displayname] = {'points': 0, 'prev_points':0 ,'sessionId': request.sid}

    # also store map from session id to player name
    player_by_sid[request.sid] = displayname
    

    games[gameId]['num_players'] += 1

    log(f"Player {displayname} joined game {gameId}.")
    
    # notify the other players that a new one has joined
    socketio.emit('player_join_game', {'player_name': displayname})


'''
event that gets triggered when the host starts the game
'''
@socketio.event
def host_start_game(data):

    gameId = int(data['gameId'])

    # make sure it was triggered from host
    if games[gameId]['host_sid'] == request.sid:

        games[gameId]['hasStarted'] = True

        # notify the players that the game started (triggers their countdown)
        socketio.emit('start_game', {'gameId': gameId})


'''
event that gets triggered when the previous round is over and next question should be served
'''
@socketio.event
def get_next_question(data):

    gameId = int(data['gameId'])
    current_game = games[gameId] 

    # make sure it was triggered from host
    if games[gameId]['host_sid'] == request.sid:

        # TODO: shouldn't be necessary, handled in html?
        if current_game['next_question'] >= len(current_game['questions']):
            socketio.emit('game_over')
            return
        
        # get next question and answers
        qna = current_game['questions'][current_game['next_question']]
        
        current_game['next_question'] += 1

        # send to the players
        socketio.emit('next_question', qna)


''' 
event that gets triggered when a player submits an answer
'''
@socketio.event
def submit_answer(data):

    try:
        gameId = int(data['gameId'])

        answer = data['answer']

        player_name = player_by_sid[request.sid]

        current_question_id = games[gameId]['next_question'] - 1

        # all the answers provided by players for this question
        round_answers : list = games[gameId]['player_answers'][current_question_id]

        # order of submissions
        submission_no = len(round_answers) + 1

        log(f"Answer submission: {player_name}, {answer}, nr. {submission_no}")

        # if the player submitted an answer before, remove it and only keep new one (players can change their mind)
        for i in range(len(round_answers)):
            if round_answers[i][0] == player_name:
                round_answers.pop(i)
                break
        
        # store answer
        round_answers.append((player_name, answer, submission_no))
    except:
        return


'''
event that gets triggered when the countdown i.e. time for submitting answers is over
'''
@socketio.event
def time_up(data):
    gameId = int(data['gameId'])
    current_game = games[gameId] 

    players = current_game['players']

    # make sure it was triggered by the host
    if request.sid != current_game['host_sid']:
        return

    # find out which answer(s) were chosen by the most people

    current_round = current_game['next_question'] - 1

    round_answers = current_game['player_answers'][current_round]

    # which anwers (unique) were submitted
    uniq_ans = [ans[1] for ans in round_answers]

    # for each of them, how often
    uniq_ans_count = [uniq_ans.count(ans) for ans in uniq_ans]

    # max number
    max_count = max(uniq_ans_count)

    # get answers which were submitted the max number of times
    winning_answers = [uniq_ans[i] for i in range(len(uniq_ans)) if uniq_ans_count[i] == max_count]

    # players that submitted a winning answer
    winning_players = [(ans[0], ans[2]) for ans in round_answers if ans[1] in winning_answers]

    # sort order of submission
    winning_players = sorted(winning_players, key=lambda x:x[1])


    # formula for rewarding points: # TODO: better schemes?
    # n = num_players
    # selecting the right answer: n points
    # add (n - rank) points depending on when answer was submitted (more points for faster submission)
    # => something like 2*n - r where r is the rank (amongst winning players) 

    n = current_game['num_players']

    # TODO: prev_points would be used for animating the leaderboard changing
    # for player_name in players.keys():
    #     players[player_name]['prev_points'] = players[player_name]['points']

    # reward points
    for i in range(len(winning_players)):
        player_name = winning_players[i][0]     

        # give points
        players[player_name]['points'] += 2*n-i 

    # send the winning answers to the players
    # TODO: send number of submissions for each answer, to display it nicely with the results
    socketio.emit('question_result', {'winning_answers': winning_answers})
    


'''
event that gets triggered when the leaderboard should be shown
'''
@socketio.event
def trigger_leaderboard(data):
    gameId = int(data['gameId'])
    current_game = games[gameId] 

    players = current_game['players']

    if request.sid != current_game['host_sid']:
        return
        
    # get players, their current points, and points before this round (for animation purposes)
    player_points = [(p, players[p]['points'], players[p]['prev_points']) for p in players.keys()]

    # sort by current points
    player_points = sorted(player_points, key=lambda x:x[1])
    player_points.reverse()

    # TODO: initial idea was to first sort the players by points in round before, then show a javascript animation that updates the leaderboard to the current status

    # check if that was the last question
    isLast = current_game['next_question'] == len(current_game['questions'])

    # send leaderboard info
    socketio.emit('show_leaderboard', {'player_points': player_points, 'isLast': isLast})

    





# run server
if __name__ == '__main__':
    socketio.run(app)

