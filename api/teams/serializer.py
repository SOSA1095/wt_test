from flask_restplus import fields
from api.restplus import api
from api.courses.serializers import course
from api.users.serializers import user
from api.assignments.serializers import assignment

team = api.model('Team', {
    'id': fields.Integer(required=True, description='Team id'),
    'name': fields.String(required=True, description='Team name'),
    'professor_id': fields.Integer(required=True, description='Team professor id'),
    'group_id': fields.Integer(required=True, description='Team group id'),
    'students': fields.List(fields.Nested(user))
})

team_with_students = api.model('TeamWithStudents', {
    'id': fields.Integer(required=True, description='Team id'),
    'name': fields.String(required=True, description='Team name'),
    'professor_id': fields.Integer(required=True, description='Team professor id'),
    'group_id': fields.Integer(required=True, description='Team group id'),
    'students': fields.List(fields.Nested(user))
})

# team_with_assignments = api.model('TeamWithAssignments', {
#     'id': fields.Integer(required=True, description='Team id'),
#     'professor_id': fields.Integer(required=True, description='Team professor id'),
#     'group_id': fields.Integer(required=True, description='Team group id'),
# })

team_creation = api.model('TeamCreation', {
    'professor_id': fields.Integer(required=True, description='Team professor id'),
    'name': fields.String(required=True, description='Team name'),
    'group_id': fields.Integer(required=True, description='Team group id'),
    'enrollments': fields.List(
        fields.String(required=True, description='Student id'))
})

team_edition = api.model('TeamEdition', {
    'name': fields.String(required=True, description='Team name'),
    'enrollments': fields.List(
        fields.String(required=True, description='Student id'))       
})
