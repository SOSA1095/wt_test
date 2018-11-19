from flask_restplus import fields
from api.restplus import api
from api.courses.serializers import course
from api.users.serializers import user
from api.assignments.serializers import assignment

comment = api.model('Comment', {
	'id' : fields.Integer(required=True, description="Comment id"),
	'text' : fields.String(required=True, description="Comment text"),
	'forum_id' : fields.Integer(required=True, description="ID del foro al que pertenece el comentario"),
	'isVisible' : fields.Boolean(required=True, description="Comment visible"),
	'likes': fields.Integer(required=True, description="Likes of the comment"),
	'dislikes': fields.Integer(required=True, description="Dislikes of the comment"),
	'author': fields.Nested(user),
	'created': fields.DateTime(required=True, description="Date comment was posted")
})

comment_creation = api.model('CommentCreation', {
	'author_id': fields.Integer(required=True, description="Author of the comment"),
	'text' : fields.String(required=True, description="Comment text")
})

comment_edition = api.model('CommentEdition', {
	'text': fields.String(required=True, description='Comment text')
})