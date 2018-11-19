import logging

from flask import request, abort, jsonify, g
from flask_restplus import Resource
from api.submissions.serializers import submission as api_submission
from api.submissions.serializers import last_submission, choosing_create
from api.submissions.serializers import submission_to_a_problem, choosing
from api.users.serializers import user
from api.restplus import api
from models import db, Submission, Problem, Taken, User
from sqlalchemy import and_
from authorization import auth_required

log = logging.getLogger(__name__)

ns = api.namespace('submissions', description='Operations related to submissions')


@ns.route('/')
@api.header('Authorization', 'Auth token', required=True)
class SubmissionCollection(Resource):
    @api.marshal_list_with(api_submission)
    @auth_required('student')
    def get(self):
        """
        Returns list of submissions.
        """
        submissions = Submission.query.order_by(Submission.id).all()
        return submissions


@ns.route('/<int:id>')
@api.header('Authorization', 'Auth token', required=True)
@api.response(404, 'Submission not found.')
class SubmissionItem(Resource):
    @api.marshal_with(api_submission)
    @auth_required('student')
    def get(self, id):
        """
        Returns a submission.
        """
        return Submission.query.filter(Submission.id == id).one()


@ns.route('/last/<int:student_id>/<int:problem_id>/<int:all_submissions>')
@api.header('Authorization', 'Auth token', required=True)
@api.response(404, 'Submission not found.')
class LastSubmissions(Resource):
    @api.marshal_list_with(last_submission)
    @auth_required('student')
    def get(self, student_id, problem_id, all_submissions):
        """
        Returns last submissions of a problem by user
        """
        if (all_submissions == 1):
            response = Submission.query.filter(
                and_(Submission.user_id == student_id, Submission.problem_id == problem_id)).order_by(
                Submission.id.desc()).all()
        else:
            response = Submission.query.filter(
                and_(Submission.user_id == student_id, Submission.problem_id == problem_id)).order_by(
                Submission.id.desc()).limit(3).all()

        return response


@ns.route('/attempts/<int:student_id>/')
@api.header('Authorization', 'Auth token', required=True)
@api.response(404, 'Submission not found.')
class SubmissionAttempts(Resource):
    @api.marshal_list_with(submission_to_a_problem)
    @auth_required('student')
    def get(self, student_id):
        """
         Returns number of attempts and status of a submission
        """
        result = db.engine.execute("""
            SELECT p.name, COUNT(p.name) as no_of_attempts, MAX(s.grade) as max_grade 
            FROM Problem p, Submission s, \"user\" u 
            WHERE p.id = s.problem_id AND s.user_id = u.id AND u.id = %d GROUP BY p.name;
            """ % (student_id)).fetchall()

        return result

@ns.route('/chosen_by/<int:team_id>/<int:problem_id>')
@api.header('Authorization', 'Auth token', required=True)
@api.response(204, 'Could not find choosing.')
class ChosenBy(Resource):
    @api.marshal_with(user)
    @auth_required('student')
    def get(self, team_id, problem_id):
        """
        Returns who picked a problem from a team
        """
        result = Taken.query.filter(Taken.team_id == team_id, Taken.problem_id == problem_id).all()

        if(len(result)):
            user_id = result[0].user_id
            u = User.query.filter(User.id == user_id).one()
            return u
        else:
            return None, 204


@ns.route('/attempts/contest/<int:contest_id>/<int:team_id>')
@api.header('Authorization', 'Auth token', required=True)
@api.response(404, 'Submission not found.')
class SubmissionAttemptsTwo(Resource):
    @api.marshal_list_with(submission_to_a_problem)
    @auth_required('student')
    def get(self, contest_id, team_id):
        """
        Returns attempts results for each problem in a contest of a specific team
        """
        result = db.engine.execute("""
            """ % (contest_id)).fetchall()

        return result

@ns.route('/choose')
@api.header('Authorization', 'Auth token', required=True)
@api.response(404, 'Problem already chosen.')
class ChooseProblem(Resource):
    @auth_required('student')
    @api.marshal_with(user)
    @api.expect(choosing_create)
    def post(self):
        """
        Saves who picked a problem in a team
        """
        data = request.json
        user = data.get("user_id")
        team = data.get("team_id")
        problem = data.get("problem_id")

        # first check if someone on th team hasn't chosen this problem

        check = Taken.query.filter(
            Taken.user_id == user, 
            Taken.team_id == team, 
            Taken.problem_id == problem).all()

        if(len(check)):
            return None, 404
        else:
            new_taken = Taken(user_id=user, team_id=team, problem_id=problem)
            db.session.add(new_taken)
            db.session.commit()
            u = User.query.filter(User.id == user).one()
            return u

@ns.route('/unchoose/<int:user_id>/<int:team_id>/<int:problem_id>')
@api.header('Authorization', 'Auth token', required=True)
@api.response(404, 'User not found.')
class UnchooseProblem(Resource):

    @api.marshal_with(choosing)
    @auth_required('student')
    def get(self, user_id, team_id, problem_id):
        """
        Returns a Taken instance.
        """
        return Taken.query.filter(
            Taken.user_id == user_id, 
            Taken.team_id == team_id,
            Taken.problem_id == problem_id).one()

    @api.response(204, 'Choosing successfully updated.')
    @auth_required('student')
    def put(self, user_id, team_id, problem_id):
        """
        Updates a Taken instance
        """
        data = request.json
        Taken.query.filter(
            Taken.user_id == user_id, 
            Taken.team_id == team_id,
            Taken.problem_id == problem_id).update(data)
        db.session.commit()
        return None, 204

    @api.response(204, 'Problem succesfully unchosen.')
    @auth_required('student')
    def delete(self, user_id, team_id, problem_id):
        """
        Deletes a choosing.
        """
        taken = Taken.query.filter(
            Taken.user_id == user_id, 
            Taken.team_id == team_id,
            Taken.problem_id == problem_id
        ).one()
        db.session.delete(taken)
        db.session.commit()
        return None, 204

