import os
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

chat_history = []

host_sid = None
pending_users = {}   # sid -> username
approved_users = {}  # sid -> username


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    for msg in chat_history:
        send(msg)


@socketio.on('join')
def handle_join(username):
    global host_sid
    sid = request.sid
    if host_sid is None:
        host_sid = sid
        approved_users[sid] = username
        emit('you_are_host', room=sid)
        emit('message', f'--- {username} (host) joined ---', broadcast=True)
        emit('user_list', list(approved_users.values()), broadcast=True)
        return
    pending_users[sid] = username
    emit('waiting', room=sid)
    emit('approval_request', {
        'sid': sid,
        'username': username
    }, room=host_sid)


@socketio.on('approve_user')
def approve_user(sid):
    if sid in pending_users:
        username = pending_users.pop(sid)
        approved_users[sid] = username
        emit('approved', room=sid)
        emit('message', f'--- {username} joined ---', broadcast=True)
        emit('user_list', list(approved_users.values()), broadcast=True)


@socketio.on('reject_user')
def reject_user(sid):
    if sid in pending_users:
        emit('rejected', room=sid)
        pending_users.pop(sid)


@socketio.on('disconnect')
def handle_disconnect():
    global host_sid
    sid = request.sid
    username = approved_users.pop(sid, None) or pending_users.pop(sid, None)
    if sid == host_sid:
        if approved_users:
            host_sid = next(iter(approved_users))
            emit('you_are_host', room=host_sid)
            emit('message', f'--- New host assigned ---', room=host_sid)
        else:
            host_sid = None
    if username:
        emit('message', f'--- {username} left ---', broadcast=True)
        emit('user_list', list(approved_users.values()), broadcast=True)


@socketio.on('message')
def handle_message(msg):
    if request.sid not in approved_users:
        return
    chat_history.append(msg)
    send(msg, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    socketio.run(app, host='0.0.0.0', port=port)
