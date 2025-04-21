from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, emit
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# rooms[rid] structure:
# {
#   'players': {'1': sid1, '2': sid2},
#   'roles': {'1':'X','2':'O'},
#   'flip': False,
#   'board': ['']*9,
#   'turn': 'pid who is X',
#   'stats': {'1':{'X':n,'O':m}, '2':{'X':p,'O':q}, 'D':d},
#   'history': [ { 'winner':'1'/'2'/'D', 'symbol': 'X'/'O'/None } ... ],
#   'rematch': {'1': False, '2': False}
# }

# Manage all game rooms and their states
rooms = {}

# Route: render main game interface
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join():
    sid = request.sid
    print(f"[JOIN] Player connected: SID = {sid}")
    for rid, room in rooms.items():
        if len(room['players']) == 1:
            room['players']['2'] = sid
            room['roles'] = {'1': 'O', '2': 'X'} if room['flip'] else {'1': 'X', '2': 'O'}
            room['board'] = [''] * 9
            room['turn'] = '1' if room['roles']['1'] == 'X' else '2'
            room['rematch'] = {'1': False, '2': False}
            join_room(rid)
            print(f"[ROOM] SID {sid} joined room {rid} as Player 2")
            for pid, psid in room['players'].items():
                emit('start', {
                    'playerId': pid,
                    'symbol': room['roles'][pid],
                    'room': rid,
                    'roles': room['roles'],
                    'stats': room['stats'],
                    'history': room['history']
                }, room=psid)
            return

    # No room available, create new
    rid = str(uuid.uuid4())
    rooms[rid] = {
        'players': {'1': sid},
        'roles': {}, 'flip': False,
        'board': [], 'turn': '',
        'stats': {'1': {'X': 0, 'O': 0}, '2': {'X': 0, 'O': 0}, 'D': 0},
        'history': [],
        'rematch': {}
    }
    join_room(rid)
    print(f"[ROOM] SID {sid} created new room {rid} as Player 1")
    emit('wait', {'room': rid})


# Handle a player's move
@socketio.on('move')
def handle_move(data):
    pid = data.get('playerId')
    rid = data.get('room')
    idx = data.get('index')
    room = rooms.get(rid)
    # Determine symbol: either provided or from server roles
    sym = data.get('symbol') or (room['roles'][pid] if room and 'roles' in room else None)
    # Validate move
    if not room or sym is None or idx is None or idx < 0 or idx >= 9 or room['board'][idx] or room['turn'] != pid:
        return
    # Apply move
    room['board'][idx] = sym
    emit('move', {'index': idx, 'symbol': sym}, room=rid)
    emit('move', {'index': idx, 'symbol': sym}, room=rid)
    # Check win condition
    lines=[(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a,b,c in lines:
        if room['board'][a]==room['board'][b]==room['board'][c]==sym:
            room['history'].append({'winner':pid,'symbol':sym})
            room['stats'][pid][sym]+=1
            for pid2, psid2 in room['players'].items():
                msg = 'You win!' if pid2==pid else 'Unfortunately you lose.'
                emit('game_over', {'message': msg}, room=psid2)
            emit('stats', room['stats'], room=rid)
            emit('history', room['history'], room=rid)
            return
    # Check draw
    if all(room['board']):
        room['history'].append({'winner':'D','symbol':None})
        room['stats']['D']+=1
        emit('game_over', {'message':'Draw!'}, room=rid)
        emit('stats', room['stats'], room=rid)
        emit('history', room['history'], room=rid)
        return
    room['turn']='2' if pid=='1' else '1'

@socketio.on('chat')
def handle_chat(data):
    print(f"[CHAT] Player {data['playerId']} in room {data['room']}: {data['message']}")
    emit('chat', {'playerId': data['playerId'], 'message': data['message']}, room=data['room'])

@socketio.on('rematch')
def handle_rematch(data):
    pid, rid = data['playerId'], data['room']
    room = rooms[rid]

    print(f"[REMATCH] Player {pid} in room {rid} requested a rematch")

    room['rematch'][pid] = True
    other = '2' if pid == '1' else '1'

    if room['rematch'].get(other):
        room['flip'] = not room['flip']
        room['roles'] = {'1': 'O', '2': 'X'} if room['flip'] else {'1': 'X', '2': 'O'}
        room['board'] = [''] * 9
        room['turn'] = '1' if room['roles']['1'] == 'X' else '2'
        room['rematch'] = {'1': False, '2': False}

        print(f"[REMATCH] Both players agreed. Restarting game in room {rid}")
        for pid2, psid2 in room['players'].items():
            emit('start', {
                'playerId': pid2,
                'symbol': room['roles'][pid2],
                'room': rid,
                'roles': room['roles'],
                'stats': room['stats'],
                'history': room['history'],
                'rematch': True
            }, room=psid2)
    else:
        print(f"[REMATCH] Waiting for Player {other} in room {rid}")
        emit('rematch_pending', {}, room=room['players'][pid])
        emit('rematch_request', {}, room=room['players'][other])

# Start the server
if __name__=='__main__':
    socketio.run(app,host='0.0.0.0',port=5001,debug=True)