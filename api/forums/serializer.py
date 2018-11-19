from flask_restplus import fields
from api.restplus import api
from api.courses.serializers import course
from api.users.serializers import user
from api.assignments.serializers import assignment
from api.comments.serializer import comment

forum = api.model('Forum', {
	'id': fields.Integer(required=True, description='Forum id'),
	'name' : fields.String(required=True, description='Forum name'),
	'author' : fields.Nested(user),
	'description' : fields.String(required=True, description='Forum description'),
	'comments': fields.List(fields.Nested(comment))
})

forum_creation = api.model('ForumCreation', {
	'id' : fields.Integer(required=True, description='Forum id'),
	'name' : fields.String(required=True, description='Forum name'),
	'author' : fields.String(required=True, description='Forum author'),
	'description' : fields.String(required=True, description='Forum description')
})

forum_edition = api.model('ForumEdition', {
	'name' : fields.String(required=True, description='Forum name'),
	'description' : fields.String(required=True, description='Forum description'),
	'author_id': fields.Integer(required=True, description='ID of the forum author'),
	'author_name': fields.String(required=True, description='Name of the forum author')
})
