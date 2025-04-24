from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, emit
import uuid

# Initialize the app and socketio instance
app = Flask(
    __name__,
    static_folder="../frontend/static",
    template_folder="../frontend/templates",
)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)

# Manage all game rooms and their states
rooms = {}

# Each room has structure like:
# room[room_id] =
# {
#   'players': {'1': session_id1, '2': session_id2},
#   'roles': {'1':'X','2':'O'},
#   'flip': False,
#   'board': ['']*9,
#   'turn': 'player_id who is X',
#   'stats': {'1':{'X':n,'O':m}, '2':{'X':p,'O':q}, 'D':d},
#   'history': [ { 'winner':'1'/'2'/'D', 'symbol': 'X'/'O'/None } ... ],
#   'rematch': {'1': False, '2': False}
# }


# Route: render main game interface
@app.route("/")
def index():
    return render_template("index.html")


# Hanlde join event: player join the room
@socketio.on("join")
def handle_join():
    # Get session ID and log it
    session_id = request.sid
    print(f"[JOIN] Player connected: SessionID = {session_id}")

    for room_id, room in rooms.items():
        # When the room already has a player, add the second player and initialize player2's information
        if len(room["players"]) == 1:
            room["players"]["2"] = session_id
            room["roles"] = (
                {"1": "O", "2": "X"} if room["flip"] else {"1": "X", "2": "O"}
            )
            room["board"] = [""] * 9
            room["turn"] = "1" if room["roles"]["1"] == "X" else "2"
            room["rematch"] = {"1": False, "2": False}
            join_room(room_id)
            print(f"[ROOM] session_id {session_id} joined room {room_id} as Player 2")

            # After joining, socketio will send start message with corresponding player information to all players in the room.
            for player_id, player_session_id in room["players"].items():
                emit(
                    "start",
                    {
                        "playerId": player_id,
                        "symbol": room["roles"][player_id],
                        "room": room_id,
                        "roles": room["roles"],
                        "stats": room["stats"],
                        "history": room["history"],
                    },
                    room=player_session_id,
                )
            return

    # No room available, create new
    room_id = str(uuid.uuid4())
    rooms[room_id] = {
        "players": {"1": session_id},
        "roles": {},
        "flip": False,
        "board": [],
        "turn": "",
        "stats": {"1": {"X": 0, "O": 0}, "2": {"X": 0, "O": 0}, "D": 0},
        "history": [],
        "rematch": {},
    }
    join_room(room_id)
    print(f"[ROOM] session_id {session_id} created new room {room_id} as Player 1")
    emit("wait", {"room": room_id})


# Handle a player's move event
@socketio.on("move")
def handle_move(data):
    try:
        player_id = data.get("playerId")
        room_id = data.get("room")
        idx = data.get("index")
        room = rooms.get(room_id)
        # Determine symbol: either provided or from server roles
        sym = data.get("symbol") or (
            room["roles"][player_id] if room and "roles" in room else None
        )
        # Validate move
        if (
            not room
            or sym is None
            or idx is None
            or idx < 0
            or idx >= 9
            or room["board"][idx]
            or room["turn"] != player_id
        ):
            return
        # Apply move
        room["board"][idx] = sym
        emit("move", {"index": idx, "symbol": sym}, room=room_id)
        # Check win condition
        lines = [
            (0, 1, 2),
            (3, 4, 5),
            (6, 7, 8),
            (0, 3, 6),
            (1, 4, 7),
            (2, 5, 8),
            (0, 4, 8),
            (2, 4, 6),
        ]
        for a, b, c in lines:
            if room["board"][a] == room["board"][b] == room["board"][c] == sym:
                room["history"].append({"winner": player_id, "symbol": sym})
                room["stats"][player_id][sym] += 1
                for pid2, player_session_id2 in room["players"].items():
                    msg = "You win!" if pid2 == player_id else "Unfortunately you lose."
                    emit("game_over", {"message": msg}, room=player_session_id2)
                emit("stats", room["stats"], room=room_id)
                emit("history", room["history"], room=room_id)
                return
        # Check draw
        if all(room["board"]):
            room["history"].append({"winner": "D", "symbol": None})
            room["stats"]["D"] += 1
            emit("game_over", {"message": "Draw!"}, room=room_id)
            emit("stats", room["stats"], room=room_id)
            emit("history", room["history"], room=room_id)
            return
        room["turn"] = "2" if player_id == "1" else "1"
    except Exception as e:
        print(f"[ERROR] Error handling move: {e}")

# Handle chat event from
@socketio.on("chat")
def handle_chat(data):
    try:
        print(f"[CHAT] Player {data['playerId']} in room {data['room']}: {data['message']}")
        emit(
            "chat",
            {"playerId": data["playerId"], "message": data["message"]},
            room=data["room"],
        )
    except Exception as e:
        print(f"[ERROR] Error handling chat: {e}")


@socketio.on("rematch")
def handle_rematch(data):
    try:
        player_id, room_id = data["playerId"], data["room"]
        room = rooms[room_id]

        print(f"[REMATCH] Player {player_id} in room {room_id} requested a rematch")

        room["rematch"][player_id] = True
        other = "2" if player_id == "1" else "1"

        if room["rematch"].get(other):
            room["flip"] = not room["flip"]
            room["roles"] = {"1": "O", "2": "X"} if room["flip"] else {"1": "X", "2": "O"}
            room["board"] = [""] * 9
            room["turn"] = "1" if room["roles"]["1"] == "X" else "2"
            room["rematch"] = {"1": False, "2": False}

            print(f"[REMATCH] Both players agreed. Restarting game in room {room_id}")
            for pid2, player_session_id2 in room["players"].items():
                emit(
                    "start",
                    {
                        "playerId": pid2,
                        "symbol": room["roles"][pid2],
                        "room": room_id,
                        "roles": room["roles"],
                        "stats": room["stats"],
                        "history": room["history"],
                        "rematch": True,
                    },
                    room=player_session_id2,
                )
        else:
            print(f"[REMATCH] Waiting for Player {other} in room {room_id}")
            emit("rematch_pending", {}, room=room["players"][player_id])
            emit("rematch_request", {}, room=room["players"][other])
    except KeyError as ke:
        print(f"[ERROR] Missing key in rematch data: {ke}")
    except Exception as e:
        print(f"[ERROR] Error handling rematch: {e}")

# Start the server
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)
