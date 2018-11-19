import logging

from flask import request, abort, jsonify, g
from flask_restplus import Resource
from api.problems.serializers import problem as api_problem
from api.problems.serializers import problem_table, problem_description, problem_edition
from api.forums.serializer import (forum as api_forum, forum_creation,forum_edition)
from api.comments.serializer import (comment as api_comment, comment_creation,comment_edition)
from api.restplus import api
from sqlalchemy import join, and_
from sqlalchemy.orm import Load
from authorization import auth_required
from models import db, User, Problem, Group, Statistic, Student, Submission, Admin, Professor, Topic, ProblemTopic, Forum, Comment
from api.evaluators.services import update_test_cases_in_filesystem

log = logging.getLogger(__name__)

ns = api.namespace('comment', description='Operations related to comments')

@ns.route('/create/<int:forum_id>')
@api.header('Authorization', 'Auth token', required=True)
class CommentCreation(Resource):
	@api.response(201, 'Comment successfully created')
	@api.expect(comment_creation)
	@auth_required('student')
	def post(self, forum_id):
		"""
		Creates comment
		"""
		data = request.json
		text = data.get('text')
		author = data.get('author_id')
		visible = data.get('isVisible')
		if text == "" or forum_id is None:
			return {'error' : 'Missing arguments'}, 400
		new_comment = Comment(text=text, forum_id=forum_id, author_id=author, isVisible=visible)
		db.session.add(new_comment)
		db.session.commit()
		return 201

@ns.route('/<int:forum_id>')
@api.header('Authorization', 'Auth token', required=True)
@api.response(404, 'Comment not found.')
class CommentItem(Resource):
	@api.marshal_with(api_comment)
	@auth_required('student')
	def get(self, forum_id):
		"""
		Returns all comments from a forum
		"""
		try:
			forum_id = int(forum_id)
		except ValueError:
			return None, 404
		# Check if the comments exist
		comments = Comment.query.filter(Comment.forum_id == forum_id).order_by(Comment.created).all()
		if comments is None:
			return 404
		return comments

@ns.route('/<int:id>')
@api.header('Authorization', 'Auth token', required=True)
class CommentModify(Resource):
	@api.expect(comment_edition)
	@api.response(204, 'Comment successfully updated.')
	@auth_required('student')
	def put(self, id):
		"""
		Updates a comment
		"""
		data = request.json
		Comment.query.filter(Comment.id == id).update(data)
		comment = Comment.query.filter(Comment.id == id).one()
		db.session.commit()

		return comment, 204

	@api.response(204, 'Comment successfully deleted.')
	@auth_required('professor')
	def delete(self, id):
		"""
		Deletes a comment
		"""
		comment = Comment.query.filter(Comment.id == id).one()
		db.session.delete(comment)
		db.session.commit()
		return 204

@ns.route('/')
@api.header('Authorization', 'Auth token', required=True)
class CommentCollection(Resource):
	@api.marshal_list_with(api_comment)
	@auth_required('student')
	def get(self):
		"""
		Get all the comments
		"""
		comments = Comment.query.order_by(Comment.id).all()
		return comments

@ns.route('/like/<int:id>')
@api.header('Authorization', 'Auth token', required=True)
class CommentLike(Resource):
	@api.response(204, 'Comment successfully liked')
	@auth_required('student')
	def put(self, id):
		"""
		Update the likes of a comment
		"""
		comment = Comment.query.filter(Comment.id == id).one()
		comment.likes = comment.likes + 1
		db.session.commit()
		return 204

@ns.route('/dislike/<int:id>')
@api.header('Authorization', 'Auth token', required=True)
class CommentDislike(Resource):
	@api.response(204, 'Comment successfully disliked')
	@auth_required('student')
	def put(self, id):
		"""
		Update the dislikes of a comment
		"""
		comment = Comment.query.filter(Comment.id == id).one()
		comment.dislikes = comment.dislikes + 1
		db.session.commit()
		return 204

@ns.route('/<int:forum_id>')
@api.header('Authorization', 'Auth token', required=True)
class CommentNotVisibleFromForum(Resource):
	@api.marshal_list_with(api_comment)
	@auth_required('professor')
	def get(self, forum_id):
		"""
		Get the invisible comments from a forum
		"""
		comments = db.session.query(Comment).filter(and_(Comment.isVisible == False, Comment.forum_id == forum_id)).all()
		return comments

@ns.route('/<int:id>/<int:visibility>')
@api.header('Authorization', 'Auth token', required=True)
class CommentVisibility(Resource):
	@api.response(204, 'Comment successfully liked')
	@auth_required('professor')
	def put(self, id, visibility):
		"""
		Update the visibility of a comment
		"""
		comment = Comment.query.filter(Comment.id == id).one()
		comment.isVisible = visibility > 0
		db.session.commit()
		return 204