from flask import Flask, redirect, url_for, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET'] = 'secretkey'

socketio = SocketIO(app)


games = dict()
players = dict()
player_by_sid = dict()


"""
- user goes on site
- user creates new game
- player goes on site
- player joins a game
"""

# TODO: divide different games into different rooms
# TODO: make leaderboard animation
# TODO: final screen with leaderboard and top 3?
# TODO: save and load quizzes from json, make a viewer

# TODO: make more "Kahoot-like"


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        gameId = request.form['gameId']
        return redirect(url_for('game', game_id=gameId))
    else:
        return render_template('index.html')



@app.route('/create/', methods=['GET', 'POST'])
def create():
    global games
    if request.method == 'POST':
        gameId = len(games)
        i = 0
        questions = []
        while True:
            if f'q{i}' not in request.form.keys():
                break

            question = request.form[f'q{i}'] 
            answers = [request.form[f'{i}_a{j}'] for j in range(4) if request.form[f'{i}_a{j}'] != '']


            i += 1
            if question == '':
                continue 

            questions.append({'question': question, 'answers': answers})




     
        # add questions: list of questions;
        # each question is a q: question and a: list of answers
        games[gameId] = {'questions': questions, 'initialized': False, 'hasStarted': False, 'host_sid': None, 'players': dict(), 'next_question': 0, 'player_answers': [[] for _ in range(len(questions))], 'num_players': 0}

        print("qs: " + str(len(questions)))


        return redirect(url_for('game', game_id=gameId))
    else:
        return render_template('create_quiz.html')
    # user can create game, write questions etc.
    # afterwards, the 





@app.route('/<game_id>/')
def game(game_id):
    global games 
    print(games)
    game_id = int(game_id)
    if game_id not in games.keys():
        return f"<h2>This game does not exist!</h2>"

    current_game = games[game_id]

    host_flag = not current_game['initialized']
    lobby_flag = not current_game['hasStarted']
    current_game['initialized'] = True

    if not host_flag:
        if not lobby_flag:
            return f"<h2>This game has already started!</h2>"


    player_list = list(players.keys())
    return render_template('game.html', id=game_id, isHost=host_flag, player_list=player_list)
    # global games
    # game_id = int(game_id)
    # if int(game_id) in games.keys():
    #     # game exists.
    #     # join game?? TODO
    #     return render_template('game.html', id=game_id)
    # else:
    #     # game does not exist
    #     pass

@socketio.event
def host_join(data):
    if data['ishost'] == 'True':
        print('host identified')
        games[int(data['gameId'])]['host_sid'] = request.sid


@socketio.event
def player_join(data):
    print("player_join")
    displayname = data['displayname']
    gameId = int(data['gameId'])
    # TODO: at the moment, players between different games are shared!

    # TODO: make sure no duplicate playernames
    if games[gameId]['hasStarted']:
        # cannot join anymore
        return 


    players[displayname] = {'points': 0, 'prev_points':0 ,'sessionId': request.sid}
    player_by_sid[request.sid] = displayname
    

    games[gameId]['num_players'] += 1
    

    socketio.emit('player_join_game', {'player_name': displayname})
   # emit('')

@socketio.event
def host_start_game(data):
    print("host_start_game")
    gameId = int(data['gameId'])


    if games[gameId]['host_sid'] == request.sid:
        print(f"game {gameId} started")
        games[gameId]['hasStarted'] = True
        socketio.emit('start_game', {'gameId': gameId})



@socketio.event
def get_next_question(data):
    print("get_next_question")
    gameId = int(data['gameId'])
    current_game = games[gameId] 
    if games[gameId]['host_sid'] == request.sid:

        print("good id")

        # current_game['takingSubmissions'] = True

        if current_game['next_question'] >= len(current_game['questions']):
            socketio.emit('game_over')
            print("game over????")
            return
        
        qna = current_game['questions'][current_game['next_question']]
        

        current_game['next_question'] += 1
        # contains question and list of answers

        print(current_game['next_question'])
        print(len(current_game['questions']))

        print("got here")
        print(qna)
        socketio.emit('next_question', qna)

@socketio.event
def submit_answer(data):
    print("received answer " + str(data))
    try:
        gameId = int(data['gameId'])

        answer = data['answer']
       
        # if not games[gameId]['taking_submissions']:
        #     return 

        # should be handled by changing UI of players

        player_name = player_by_sid[request.sid]
        #player = players[player_name]

        current_question = games[gameId]['next_question'] - 1

        round_answers : list = games[gameId]['player_answers'][current_question]

        submission_no = len(round_answers) + 1

        for i in range(len(round_answers)):
            if round_answers[i][0] == player_name:
                round_answers.pop(i)
                break

        round_answers.append((player_name, answer, submission_no))
    except:
        return


@socketio.event
def time_up(data):
    gameId = int(data['gameId'])
    current_game = games[gameId] 
    if request.sid != current_game['host_sid']:
        return
    print("time_up")

    # current_game['taking_submissions'] = False

    # calculate winning answer

    current_round = current_game['next_question'] - 1

    round_answers = current_game['player_answers'][current_round]

    uniq_ans = [ans[1] for ans in round_answers]

    uniq_ans_count = [uniq_ans.count(ans) for ans in uniq_ans]

    max_count = max(uniq_ans_count)

    winning_answers = [uniq_ans[i] for i in range(len(uniq_ans)) if uniq_ans_count[i] == max_count]

    winning_players = [(ans[0], ans[2]) for ans in round_answers if ans[1] in winning_answers]
    winning_players = sorted(winning_players, key=lambda x:x[1])

    n = current_game['num_players']

    for player_name in players.keys():
        players[player_name]['prev_points'] = players[player_name]['points']


    for i in range(len(winning_players)):
        player_name = winning_players[i][0]        
        players[player_name]['points'] += 2*n-i
        print("player " + player_name + " got " + str(2*n-i) + " points!")

    socketio.emit('question_result', {'winning_answers': winning_answers})
    # point formula:
    # n = num_players
    # selecting the right answer: n points
    # plus n - rank points depending on when answer was submitted



    
@socketio.event
def trigger_leaderboard(data):
    gameId = int(data['gameId'])
    current_game = games[gameId] 
    if request.sid != current_game['host_sid']:
        return
    
    print("trigger leaderboard")
    
    player_points = [(p, players[p]['points'], players[p]['prev_points']) for p in players.keys()]
    player_points = sorted(player_points, key=lambda x:x[1])
    player_points.reverse()

    isLast = current_game['next_question'] == len(current_game['questions'])

        

    socketio.emit('show_leaderboard', {'player_points': player_points, 'isLast': isLast})






@socketio.event
def ping():
    print("ping!")
    print("session id: " + str(request.sid))
    socketio.emit('pong', to=request.sid)





if __name__ == '__main__':
    socketio.run(app)

















# '''
# gets called from the game creation page by the user, initalizes and 
# saves the game and redirects the user to the waiting room
# '''
# def game_init(data):
#     game_id = data['id']
     
#     games[game_id]['question_count'] = data['question_count']
#     games[game_id]['questions'] = data['questions']
#     games[game_id]['progress'] = 0

#     questions = data['questions']

#     # can we call a function to render another page here?
#     return game(game_id)


# @socketio.event
# def host_joined():
#     # host gets to create a game
#     emit('create game') 
# # -> setup game

# @socketio.event
# def init_game():
#     # game is initialized, lobby opens
#     pass 
# # -> open lobby

# @socketio.event
# def start_game():
#     # host starts game
#     # maybe this should just be next question with question #1?
#     pass 


# @socketio.event
# def player_joined():
#     # player gets to select name and join game
#     pass 
# # -> setup player

# @socketio.event
# def player_join_lobby():
#     # player is added to lobby
#     pass 
# # -> join lobby

# @socketio.event
# def answer_submitted():
#     # player has submitted an answer
#     pass 
# # wait for result

# @socketio.event
# def next_question():
#     # host has clicked next question
#     pass
# # -> send next question

# @socketio.event
# def time_up():
#     pass

# @socketio.event
# def get_score():
#     pass 




