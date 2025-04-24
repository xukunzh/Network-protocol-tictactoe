# Network-Protocol-Tictactoe

A real-time multiplayer Tic-Tac-Toe game implemented using WebSocket protocol.

Config the environment
`python3 venv venv`
`souce venv/bin/activate`
`pip install -r requirements.txt`

Start the app
`cd backend`
`python3 server.py`

The server triggers events using emit() - “wait”, “start”, “move”, “game_over”, “chat”, “rematch”, and sends data to the client via socketio.

The client triggers events to the server using socket.emit() - “join”, “move”, “chat”, “rematch” to perform game actions.
