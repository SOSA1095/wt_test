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
from models import db, User, Problem, Group, Statistic, Student, Submission, Admin, Professor, Topic, ProblemTopic, Forum, Comment
from api.evaluators.services import update_test_cases_in_filesystem

log = logging.getLogger(__name__)

ns = api.namespace('forum', description='Operations related to forums')

@ns.route('/create')
@api.header('Authorization', 'Auth token', required=True)
class ForumCreation(Resource):
	@api.response(201, 'Forum successfully created')
	@api.expect(forum_creation)
	@auth_required('professor')
	def post(self):
		"""
		Creates forum
		"""
		data = request.json
		name = data.get('name')
		author_id = data.get('author_id')
		author_name = data.get('author_name')
		description = data.get('description')
		if (name == "" or author_id == "") or description == "":
			return {'error': 'Missing arguments'}, 400
		if db.session.query(Forum).filter(Forum.name == name).first():
			return {'error': 'Forum name already exist'}, 400 
		new_forum = Forum(name=name, author_name=author_name, author_id=int(author_id), description=description)
		db.session.add(new_forum)
		db.session.commit()

		return 201


@ns.route('/<int:id>')
@api.header('Authorization', 'Auth token', required=True)
@api.response(404, 'Forum not found.')
class ForumItem(Resource):

	@api.marshal_with(api_forum)
	@auth_required('student')
	def get(self, id):
		"""
		Returns a forum.
		"""
		# Check if id is valid
		try:
			id = int(id)
		except ValueError:
			return None, 404
		# Check if problem exists
		forum = db.session.query(Forum).filter(Forum.id == id).first()
		if forum is None:
			return None, 404
		return forum

	@api.expect(forum_edition)
	@api.response(204, 'Forum successfully updated.')
	@auth_required('professor')
	def put(self, id):
		"""
		Updates a forum
		"""
		data = request.json

		forum = Forum.query.filter(Forum.id == id).\
		update(dict(name=data.get('name'), author_name = data.get('author_name'),\
		author_id = data.get('author_id'),description = data.get('description')))
		
		db.session.commit()

		return forum, 204

	@api.response(204, 'Forum successfully deleted.')
	@auth_required('professor')
	def delete(self, id):
		"""
		Deletes a forum
		"""
		forum = Forum.query.filter(Forum.id == id).one()
		db.session.delete(forum)
		db.session.commit()
		return 204

@ns.route('/')
@api.header('Authorization', 'Auth token', required=True)
class ForumCollection(Resource):
		@api.marshal_list_with(api_forum)
		@auth_required('student')
		def get(self):
			"""
			Return list of all forums
			"""
			forums = Forum.query.order_by(Forum.id).all()
			return forums

@ns.route('/owner/<int:author_id>')
@api.header('Authorization', 'Auth token', required=True)
class ForumOwner(Resource):
		@api.marshal_list_with(api_forum)
		@auth_required('student')
		def get(self, author_id):
			"""
			Return list of forums with specific author_id
			"""
			forums = Forum.query.filter(Forum.author_id == author_id).all()
			return forums
