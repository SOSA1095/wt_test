import logging
import datetime
import pytz

from flask import request, abort, jsonify, g
from flask_restplus import Resource
from api.contests.serializer import contest as api_contests
from api.contests.serializer import contest_creation, contest_with_problem, contest_id_list
from api.restplus import api
from models import db, Problem, Topic, ProblemTopic, Case, Language, Submission
from models import User, Taken, Statistic, Contest, Group, Enrollment, Team, ContestProblem
from sqlalchemy import join, and_
from sqlalchemy.orm import Load
from authorization import auth_required
from api.evaluators.services import update_test_cases_in_filesystem

log = logging.getLogger(__name__)

ns = api.namespace('contests', description='Operations related to contests')

@ns.route('/')
@api.header('Authorization', 'Auth token', required=True)
class ContestCollection(Resource):

    @api.marshal_with(api_contests)
    @auth_required('student')
    def get(self):
        """
        Returns list of contests.
        """
        contests = Contest.query.all()

        return contests

@ns.route('/<int:id>')
@api.header('Authorization', 'Auth token', required=True)
class ContestItem(Resource):

    @api.response(204, 'Contest found.')
    @api.marshal_with(api_contests)
    @auth_required('student')
    def get(self, id):
        """
        Returns a contest with specific id.
        """
        contest = Contest.query.filter(Contest.id == id).one()

        # Get user
        token = request.headers.get('Authorization', None)
        user = User.verify_auth_token(token)

        if not contest:
            return None, 404

        return contest
    
    @api.expect(contest_creation)
    @api.response(204, 'Contest successfully updated.')
    @api.marshal_with(contest_with_problem)
    @auth_required('professor')
    def put(self, id): 
        """
        Updates the contest
        """
        data = request.json
        start_date = data.get('start_date')[:10] + ' ' + data.get('start_date')[11:19]
        end_date = data.get('end_date')[:10] + ' ' + data.get('end_date')[11:19]

        # Convert to type datetime to compare values
        # 2018-04-13T00:13:20.134Z -> 2018-04-13 00:13:20 
        start = datetime.datetime(int(start_date[:4]), int(start_date[5:7]), int(start_date[8:10]), \
                                    int(start_date[11:13]), int(start_date[14:16]), int(start_date[17:]))     
        end = datetime.datetime(int(end_date[:4]), int(end_date[5:7]), int(end_date[8:10]), \
                                   int(end_date[11:13]), int(end_date[14:16]), int(end_date[17:]))

        if end < start:
            # The end date is before the start date 
            return 404

        data['start_date'] = start.strftime('%Y-%m-%d %H:%M:%S')
        data['end_date'] = end.strftime('%Y-%m-%d %H:%M:%S')

        ids = data.get('problems')
        uniqueIDs = list(set(ids))
        problems = getProblems(uniqueIDs)

        contest = Contest.query.filter(Contest.id == id).first()
        contest.problems = problems
        contest.start_date = data.get('start_date')
        contest.end_date = data.get('end_date')
        contest.group_id = data.get('group_id')
        contest.name = data.get('name')
        db.session.commit()

        return contest
    
    @api.response(204, 'Contest successfully deleted.')
    @auth_required('professor')
    def delete(self, id):
        """
        Deletes a contest
        """
        contest = Contest.query.filter(Contest.id == id).one()
        db.session.delete(contest)
        db.session.commit()
        return 204

@ns.route('/create')
@api.header('Authorization', 'Auth token', required=True)
class CreateContest(Resource):
    @api.response(201, 'Contest succesfully created')
    @api.expect(contest_creation)
    @api.marshal_list_with(contest_with_problem)
    @auth_required('professor')
    def post(self):
        '''
        Create new contest with problems
        '''
        data = request.json
        name = data.get('name')
        start_date = data.get('start_date')[:10] + " " + data.get('start_date')[11:19]
        end_date = data.get('end_date')[:10] + " " + data.get('end_date')[11:19]
        group_id = data.get('group_id')
        print("GROUP ID")
        print(group_id)
        # Convert to type datetime to compare values
        # 2018-04-13T00:13:20.134Z <- 2018-04-13 00:13:20 
        start = datetime.datetime(int(start_date[:4]), int(start_date[5:7]), int(start_date[8:10]), \
                                    int(start_date[11:13]), int(start_date[14:16]), int(start_date[17:]))     
        end = datetime.datetime(int(end_date[:4]), int(end_date[5:7]), int(end_date[8:10]), \
                                   int(end_date[11:13]), int(end_date[14:16]), int(end_date[17:]))
        timezone = pytz.timezone("America/Monterrey")
        start_aware = timezone.localize(start)
        end_aware = timezone.localize(end)

        if end < start:
            # The end date is before the start date 
            return None, 404
        # get teams of the group
        teams = Team.query.filter(Team.group_id == group_id).all()
        ids = data.get('problems')
        uniqueIDs = list(set(ids))

        new_contest = Contest(name=name, start_date=start_date,
                                end_date=end_date, group_id=group_id, teams=teams,
                                e_date=end_aware, s_date=start_aware)
        new_contest = add_problems(uniqueIDs, new_contest)

        db.session.add(new_contest)
        db.session.commit()

        return new_contest
    
@ns.route('/professor/<int:id>')
@api.header('Authorization', 'Auth token', required=True)
class ContestProfessor(Resource):

    @api.marshal_list_with(api_contests)
    @auth_required('professor')
    def get(self, id):
        """
        Returns list of contests of a professor.
        """

        # get the ids of the groups the professor is in charge of.
        groups_ids = Group.query.filter(Group.professor_id == id).all()
        # get the contests of this groups
        contests = []
        for g in groups_ids:
            # get the contests with the group id of g.
            g_contests = Contest.query.filter(Contest.group_id == g.id).all()
            # if the results is not an empty list, add it to the results
            if g_contests:
                contests.append(g_contests)

        return contests

@ns.route('/student/<int:id>')
@api.header('Authorization', 'Auth token', required=True)
class ContestStudent(Resource):

    @api.marshal_with(api_contests)
    @auth_required('student')
    def get(self, id):
        """
        Returns list of contests of a student.
        """
        # get the ids of the groups the student belongs to
        # Enrollment is a relationship table with group_id and student_id
        groups_ids = Enrollment.query.filter(Enrollment.student_id == id).all()
        # get the contests of this groups
        contests = []
        for g in groups_ids:
            # get the contests with the group id of g.
            g_contests = Contest.query.filter(Contest.group_id == g.group_id).all()
            # if the results is not an empty list, added to the results
            if g_contests:
                contests.append(g_contests)

        return contests


@ns.route('/contests-problem/<int:problem_id>')
@api.header('Authorization', 'Auth token', required=True)
class ContestStudent(Resource):

    @api.marshal_list_with(contest_id_list)
    @auth_required('student')
    def get(self, problem_id):
        """
        Returns list of contests of a problem
        """
        contests = ContestProblem.query.filter(ContestProblem.problem_id == problem_id).all() 
    
        return contests

@ns.route('/get-table/<int:contest_id>')
@api.header('Authorization', 'Auth token', required=True)
class ContestStudent(Resource):

    # @api.marshal_with(api_contests)
    @auth_required('student')
    def get(self, contest_id):
        """
        Returns latest information(scores) of the status of a contest
        """
        # {
            # team1: { problem1: result ... problemn: result }
        # }
        results = {}
        contest = Contest.query.filter(Contest.id == contest_id).first()
        # print(contest)
        problems = contest.problems
        teams = contest.teams

        for t in teams:
            results.update({t.name: {}})

        start = datetime.datetime.strptime(contest.start_date, "%Y-%m-%d %H:%M:%S")
        start = start + datetime.timedelta(microseconds=1)
        end = datetime.datetime.strptime(contest.end_date, "%Y-%m-%d %H:%M:%S")
        end = end + datetime.timedelta(microseconds=1)

        # for each problem
        for p in problems:
            # for each team
            for t in teams:
                # update the results with each new team
                # get the students of the team
                students = t.students
                for s in students:
                    # check if any of the students has completed the main problem
                    # as long as the date it was submitted is smaller than the 
                    # contest end date and bigger than the start date
                    subs = Submission.query.filter(
                        Submission.user_id == s.id,
                        Submission.problem_id == p.id, 
                        Submission.created > start,
                        Submission.created < end,
                        Submission.grade == 100
                    ).all()
                    print(p.name, s.first_name, len(subs))
                    if len(subs):
                        # update the problem status of the current team
                        results[t.name][p.name] = "done"
                        break 
                    else: 
                        results[t.name][p.name] = "not done"
                    
        return results

def add_problems(ids, contest):
    contest.problems = []
    for id in ids:
        problem = Problem.query.filter(Problem.id == id).first()
        if problem:
            contest.problems.append(problem)
    return contest

def areProblemsRepeated(ids):
    for i in set(ids):
        if ids.count(i) > 1:
            return False
    return True

def getProblems(ids):
    problems = []
    for id in ids:
        problem = Problem.query.filter(Problem.id == id).first()
        if problem:
            problems.append(problem)
    return problems

