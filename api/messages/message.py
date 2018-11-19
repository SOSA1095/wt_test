import logging

from flask import request, abort, jsonify, g
from flask_restplus import Resource
from api.problems.serializers import problem as api_problem
from api.problems.serializers import problem_table, problem_description, problem_edition
from api.forums.serializer import (forum as api_forum, forum_creation,forum_edition)
from api.restplus import api
from sqlalchemy import join, and_
from sqlalchemy.orm import Load
from authorization import auth_required
from models import db, User, Problem, Group, Statistic, Student, Submission, Admin, Professor, Topic, ProblemTopic, Forum, Comment, Message
from api.evaluators.services import update_test_cases_in_filesystem
from api.messages.serializer import message as api_message

log = logging.getLogger(__name__)

ns = api.namespace('message', description='Operation related to messages')

@ns.route('/<int:id>')
@api.header('Authorization', 'Auth token', required=True)
class MessagesCollection(Resource):
	@api.marshal_list_with(api_message)
	@auth_required('professor')
	def get(self, id):
		"""
		Return list of messages by team id
		"""
		try:
			id = int(id)
		except ValueError:
			return None, 404
		messages = Message.query.filter(Message.team_id == id).order_by(Message.created).all()
		return messages