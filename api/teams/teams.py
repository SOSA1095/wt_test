import logging
import redis

from flask import request, abort, jsonify, g
from flask_restplus import Resource
from flask_security import auth_token_required, utils
from flask_httpauth import HTTPBasicAuth
from api.teams.serializer import (team as api_team, team_creation, team_with_students, team_edition)
from api.restplus import api
from models import db, User, Team, Student, Group, Teamenroll
from authorization import auth_required


log = logging.getLogger(__name__)

auth = HTTPBasicAuth()

ns = api.namespace('teams', description='Operations related to team')

@ns.route('/')
@api.header('Authorization', 'Auth token', required=True)
class TeamCollection(Resource):

    @api.marshal_list_with(api_team)
    @auth_required('professor')
    def get(self):
        """
        Returns list of teams.
        """

        # Retrieve just groups of professor
        token = request.headers.get('Authorization', None)
        user = User.verify_auth_token(token)
        teams = Team.query.order_by(Team.id).all()
        #teams = Team.query.filter(Team.professor_id == user.id).order_by(Team.id).all()


        return teams

@ns.route('/create')
@api.header('Authorization', 'Auth token', required=True)
class TeamCreation(Resource):
    @api.response(201, 'Team succesfully created')
    @api.expect(team_creation)
    @api.marshal_with(team_with_students)
    @auth_required('professor')
    def post(self):
        """
        Creates team
        """
        data = request.json
        #period = data.get('period')
        name = data.get('name')
        professor_id = data.get('professor_id')
        group_id = data.get('group_id')
        #course_id = data.get('course_id')

        new_team = Team(professor_id=professor_id, group_id=group_id, name=name)

        enrollments = data.get('enrollments')
        new_team = add_enrollments(enrollments, new_team)

        db.session.add(new_team)
        db.session.commit()

        return new_team, 201


@ns.route('/<int:group_id>')
@api.header('Authorization', 'Auth token', required=True)
@api.response(404, 'Group not found.')
class TeamGroup(Resource):

    @api.marshal_with(api_team)
    @auth_required('professor')
    def get(self, group_id):
        """
        Returns teams from a group.
        """
        # Check if id is valid
        try:
            group_id = int(group_id)
        except ValueError:
            return None, 404

        teams = Team.query.filter(Team.group_id == group_id).all()

        # If user is professor, check that professor belongs to group
        # Get user
        token = request.headers.get('Authorization', None)
        user = User.verify_auth_token(token)

        for team in teams:
            if (user.role == 'professor' and team.professor_id != user.id):
                return None, 404

        return teams

@ns.route('/get-team/<int:user_id>')
@api.header('Authorization', 'Auth token', required=True)
class GetTeam(Resource):
    
    @api.marshal_with(api_team)
    @auth_required('student')
    def get(self, user_id):
        """
        Get team based on user id
        """
        t_id = Teamenroll.query.filter(Teamenroll.student_id == user_id).first()
        team = {}
        if t_id is not None:
            team = Team.query.filter(Team.id == t_id.team_id).one()    
        return team
        
        # for row in team:
        #     if row.students[0].id is user_id:
        #         return team
        # return None, 404

@ns.route('/<int:id>')
@api.header('Authorization', 'Auth token', required=True)
@api.response(404, 'Team not found.')
class TeamItem(Resource):

    @api.marshal_with(api_team)
    @auth_required('professor')
    def get(self, id):
        """
        Returns a team.
        """
        # Check if id is valid
        try:
            id = int(id)
        except ValueError:
            return None, 404

        team = Team.query.filter(Team.id == id).first()

        # Check that group exists
        if (team is None):
            return None, 404

        # If user is professor, check that professor belongs to group
        # Get user
        token = request.headers.get('Authorization', None)
        user = User.verify_auth_token(token)
        if (user.role == 'professor' and team.professor_id != user.id):
            return None, 404

        return team

    @api.expect(team_edition)
    @api.response(204, 'Team successfully updated.')
    @api.marshal_with(team_with_students)
    @auth_required('professor')
    def put(self, id):
        """
        Updates a team.
        Use this method to edit a team.
        """
        data = request.json
        Team.query.filter(Team.id == id).update({'name': data.get('name')})
        team = Team.query.filter(Team.id == id).one()
        enrollments = data.get('enrollments')
        team = add_enrollments(enrollments, team)

        db.session.commit()
        return team, 204

    @api.response(204, 'Team successfully deleted.')
    @auth_required('professor')
    def delete(self, id):
        """
        Deletes a team.
        """
        team = Team.query.filter(Team.id == id).one()
        db.session.delete(team)
        db.session.commit()
        return None, 204

# get-all-teams
@ns.route('/get-all-teams/<int:user_id>')
@api.header('Authorization', 'Auth token', required=True)
class GetTeam(Resource):
    
    @api.marshal_with(api_team)
    @auth_required('student')
    def get(self, user_id):
        """
        Get all teams a user(which is a student) belogns to
        """
        result = []
        teamIDs = Teamenroll.query.filter(Teamenroll.student_id == user_id).all()
        for team in teamIDs:
            t = Team.query.filter(Team.id == team.team_id).one()
            result.append(t)    
        return result
        

def add_enrollments(enrollments, team):
    team.students.clear()
    for i in range(len(enrollments)):
        enrollment = enrollments[i].lower()
        new_student = Student.query.filter_by(enrollment=enrollment).first()
        if not new_student:
            new_student = Student(email=enrollment + '@itesm.mx',
                                  role='student', enrollment=enrollment)
            new_student.hash_password(enrollment)
        team.students.append(new_student)
    return team
