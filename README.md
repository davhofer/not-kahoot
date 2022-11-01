# not-kahoot
A game in which the majority always wins.


## Installation
Using conda, run
`conda create --name <env_name> --file requirements.txt`

or install the following manually:
- python (make sure it's python3)
- flask
- flask-socketio

## Usage
To run the webserver:
`python main.py`  
then open the link shown in the console in the browser.


## TODO
- expand user interface: countdown, answer selection, playername, etc.
- provide capability for handling multiple games simultaneously, group different games into different groups (socketio)
- add persistence for games (players/scores? probably not needed). probably just load from and save to json file
- make leaderboard animation
- styling of whole application
- final screen with leaderboard, top 3
- see kahoot for nice features
