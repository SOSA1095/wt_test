
from flask_socketio import Namespace, emit, join_room, leave_room, send
import json

class ContestNamespace(Namespace):
    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    # joining a room
    def on_join(self, data):
        d = json.loads(data)
        room = d['room']
        message = room
        join_room(room)
        emit('join_response', message, room=room)
    
    #leaving a room
    def on_leave(self, data):
        d = json.loads(data)
        room = d['room']
        message = room
        emit('leave_response', message, room=room)
        leave_room(room)
    
    def on_update_contest(self, data):
        d = json.loads(data)
        room_id = d['room'] # represents the contest id
        emit('message', room_id, room=room_id) # sent the contest id to update

    def on_message(self, msg):
        send(msg, broadcast=True)

