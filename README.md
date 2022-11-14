# not-kahoot
A game in which the majority always wins.


## Installation
Run
`pip install -r requirements.txt`

or install the following manually:
- python (make sure it's python3)
- Flask
- Flask-socketio
- gunicorn
- gevent-websocket


## Usage

### Linux
To run the webserver:
`gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 main:app`  
then open the link shown in the console in the browser.

### Windows
Comment out the last line and uncomment the second-to-last line in main.py, it should look like this
```python
socketio.run(app)
#app.run()
```
To run the webserver:
`python main.py`  
then open the link shown in the console in the browser.


To play the game, visit here:
https://majority-mins.herokuapp.com


## TODO
(notion doc)

### Future additonal features
- provide capability for handling multiple games simultaneously, group different games into different groups (socketio)
- add persistence for games. probably just load from and save to json file
