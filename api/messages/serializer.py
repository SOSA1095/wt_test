from flask_restplus import fields
from api.restplus import api

message = api.model('Message', {
	'text' : fields.String(required=True, description = "Message text"),
	'fecha' : fields.String(required=True, description="Message date"),
	'team_id' : fields.Integer(required=True, description="ID del equipo"),
	'created': fields.DateTime(required=True, description="Date message was sent")
})