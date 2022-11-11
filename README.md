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

## Hosting on PythonAnywhere
https://medium.com/swlh/how-to-host-your-flask-app-on-pythonanywhere-for-free-df8486eb6a42


## TODO

### Visuals, Layout
add styling to:
- background
- title
- countdown
- various messages being displayed
- leaderboard
- (whole page in general)

- add some layout to page, separation of different parts
- make sure colors match

player screen:
- only show large colored buttons, answer text only in host view
- make sure display of player view is optimized for mobile, host for large screen

animations:
- leaderboard update animation
- final winner podium?

### User interface
Player screen:
- show points received after round

Host screen:
- show no. answers submitted so far
- when time is up, display no. votes per answer

- short countdown (3s) before each new question?

### Functionality
- pass and compare answers by id, not by answer text
- creator can choose name for quiz that gets displayed


### Future additonal features
- provide capability for handling multiple games simultaneously, group different games into different groups (socketio)
- add persistence for games (players/scores? probably not needed). probably just load from and save to json file
- see kahoot for nice features
