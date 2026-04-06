socketio = SocketIO(app)

chat_history = []


host_sid = None
pending_users = {}   # sid -> username
approved_users = {}  # sid -> username


@app.route('/')
def index():
    return render_template('index.html')
@@ -30,22 +30,33 @@ def handle_connect():
@socketio.on('join')
def handle_join(username):
    global host_sid

    sid = request.sid

    # First user becomes host
    if host_sid is None:
        host_sid = sid
        approved_users[sid] = username

        # 🔥 IMPORTANT CHANGE (host event)
        emit('you_are_host', room=sid)

        emit('message', f'--- {username} (host) joined ---', broadcast=True)
        emit('user_list', list(approved_users.values()), broadcast=True)
        return

    # Others go to pending
    pending_users[sid] = username

    emit('waiting', room=sid)

    # Notify host
    emit('approval_request', {
        'sid': sid,
        'username': username
    }, room=host_sid)


@socketio.on('approve_user')
def approve_user(sid):
    if sid in pending_users:
@@ -68,14 +79,23 @@ def reject_user(sid):
@socketio.on('disconnect')
def handle_disconnect():
    global host_sid

    sid = request.sid

    username = approved_users.pop(sid, None) or pending_users.pop(sid, None)

    # If host leaves → assign new host
    if sid == host_sid:
        if approved_users:
            host_sid = next(iter(approved_users))

            # 🔥 ALSO IMPORTANT: promote new host
            emit('you_are_host', room=host_sid)

            emit('message', f'--- New host assigned ---', room=host_sid)
        else:
            host_sid = None

    if username:
        emit('message', f'--- {username} left ---', broadcast=True)
        emit('user_list', list(approved_users.values()), broadcast=True)
@@ -84,12 +104,12 @@ def handle_disconnect():
@socketio.on('message')
def handle_message(msg):
    if request.sid not in approved_users:
        return  # block unapproved users

    chat_history.append(msg)
    send(msg, broadcast=True)



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    socketio.run(app, host='0.0.0.0', port=port)
