from flask_restplus import fields
from api.restplus import api
from api.users.serializers import user
from api.topics.serializers import topic
from api.groups.serializers import group
from api.teams.serializer import team


contest_creation = api.model('Contest-creation', {
    'name': fields.String(required=True, description='Contest name'),
    'start_date' : fields.DateTime(required=True, description='Contest start date'),
    'end_date' : fields.DateTime(required=True, description='Contest end date'),
    'group_id': fields.Integer(required=True, description="Grouu ID"),
    'problems': fields.List(fields.Integer(required=True, description='Problem id'))
})

test_case = api.model('Case', {
    'id': fields.Integer(required=True, description='Test case id'),
    'feedback': fields.String(required=True, description='Test case feedback'),
    'input': fields.String(required=True, description='Test case input'),
    'output': fields.String(required=True, description='Test case output'),
    'is_sample': fields.Boolean(required=True, description='Is test case sample?')
  })

problem = api.model('Problem', {
    'id': fields.Integer(required=True, description='Problem id'),
    'name': fields.String(required=True, description='Problem name'),
    'language': fields.String(required=True, description='Problem lang'),
    'code': fields.String(required=True, description='Problem code'),
    'template': fields.String(required=False, description='Problem template'),
    'signature': fields.String(required=False, description='Problem signature'),
    'difficulty': fields.Integer(required=True, description='Problem difficulty'),
    'active': fields.Boolean(required=True, description='Problem active'),
    'author': fields.Nested(user),
    'description_english': fields.String(required=True, description='Problem description in English'),
    'description_spanish': fields.String(required=True, description='Problem description in Spanish'),
    'cases': fields.List(fields.Nested(test_case)),
    'time_limit': fields.Integer(required=True,
                                 description='Test case time limit'),
    'memory_limit': fields.Integer(required=True,
                                  description='Test Case memory limit'),
    'topics': fields.List(fields.Nested(topic)),
    'can_edit': fields.Boolean(required=True, description='Can current user edit this problem?')
  })

contest = api.model('Contest', {
    'id': fields.Integer(required=True, description='Contest ID'),
    'group_id': fields.Integer(required=True, description='Group ID it belongs to'),
    'group': fields.Nested(group),
    'name': fields.String(required=True, description='Contest name'),
    'start_date' : fields.String(required=True, description='Contest start date'),
    'end_date' : fields.String(required=True, description='Contest end date'),
    's_date': fields.DateTime(required=True, description='Contest start date with datetime format'),
    'e_date': fields.DateTime(required=True, description='Contest start date with datetime format'),
    'problems': fields.List(fields.Nested(problem)),
    'teams': fields.List(fields.Nested(team))
})

contest_with_problem = api.model('ContestCreation', {
    'id': fields.Integer(required=True, description='Contest id'),
    'group_id': fields.Integer(required=True, description='Group ID it belongs to'),
    'name': fields.String(required=True, description='Contest name'),
    'group': fields.Nested(group),
    'start_date' : fields.String(required=True, description='Contest start date with special format'),
    'end_date' : fields.String(required=True, description='Contest end date with special format'),
    's_date': fields.DateTime(required=True, description='Contest start date with datetime format'),
    'e_date': fields.DateTime(required=True, description='Contest start date with datetime format'),
    'problems': fields.List(fields.Nested(problem)),
    'teams': fields.List(fields.Nested(team))
})

contest_id_list = api.model('ContesProblem', {
    'contest_id': fields.Integer(required=True, description="Contest id"),
    'problem_id': fields.Integer(required=True, description="Problem id")
})
