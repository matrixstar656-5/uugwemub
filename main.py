import os
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

chat_history = []
users = {}


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    for msg in chat_history:
        send(msg)


@socketio.on('join')
def handle_join(username):
    users[request.sid] = username

    emit('message', f'--- {username} joined ---', broadcast=True)
    emit('user_list', list(users.values()), broadcast=True)


@socketio.on('disconnect')
def handle_disconnect():
    username = users.get(request.sid)

    if username:
        del users[request.sid]
        emit('message', f'--- {username} left ---', broadcast=True)
        emit('user_list', list(users.values()), broadcast=True)


@socketio.on('message')
def handle_message(msg):
    chat_history.append(msg)
    send(msg, broadcast=True)



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    socketio.run(app, host='0.0.0.0', port=port)
