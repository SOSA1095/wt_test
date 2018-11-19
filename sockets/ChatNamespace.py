
from flask_socketio import Namespace, emit, send, join_room, leave_room
from models import db, Message
import json
import datetime

class ChatNamespace(Namespace):
    '''
    methods = on_ + event_name
    '''
    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    # joining a room
    def on_join(self, data):
        d = json.loads(data)
        username = d['username']
        room_id = d['room']
        userRole = d['userRole']
        senderID = d['senderID']
        join_room(room_id)
        date = datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p")
        message = username + ' entered the chat.'
        if userRole == 'student': # Don't save the messages from the admin
            new_message = Message(text=message, fecha=date, team_id=room_id, sender_id=senderID)
            db.session.add(new_message)
            db.session.commit()
        emit('join_response', message, room=room_id)
    
    #leaving a room
    def on_leave(self, data):
        d = json.loads(data)
        username = d['username']
        room_id = d['room']
        userRole = d['userRole']
        senderID = d['senderID']
        date = datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p")
        message = username + ' left the chat.'
        if userRole == 'student': # Don't save the messages from the admin or professor
            new_message = Message(text=message, fecha=date, team_id=room_id, sender_id=senderID)
            db.session.add(new_message)
            db.session.commit()
        emit('leave_response', message, room=room_id)
        leave_room(room_id)

    def on_chat_message(self, data):
        d = json.loads(data)
        message = d['first_name'] + ": " + d['msg']
        room_id = d['room']
        userRole = d['userRole']
        senderID = d['senderID']
        date = datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p")
        if userRole == "student": # Don't save the messages from the admin or professor
            new_message = Message(text=message, fecha=date, team_id=room_id, sender_id=senderID)
            db.session.add(new_message)
            db.session.commit()
        emit('message', message, room=room_id)

    def on_message(self, msg):
        send(msg, broadcast=True)
