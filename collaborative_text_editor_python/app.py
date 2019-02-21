from flask import Flask, render_template
from flask_socketio import SocketIO, join_room
from flask import session

app = Flask(__name__)
socketio = SocketIO(app)


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('join')
def joined(message, methods=['GET', 'POST']):
    join_room(message["room"])
    socketio.emit('join', {'msg': message["user"] + ' has entered the room.'}, room=message["room"])


@socketio.on('MSG')
def recieve_msg(json, methods=['GET', 'POST']):
    socketio.emit('MSG', json, room=json["room"])


@socketio.on('DOC')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    socketio.emit('DOC', json, room=json["room"])


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
