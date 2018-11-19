import logging

from flask import request, abort, jsonify, g
from flask_restplus import Resource
from api.problems.serializers import problem as api_problem
from api.problems.serializers import problem_table, problem_description, problem_edition, main_problem
from api.restplus import api
from models import db, Problem, Topic, ProblemTopic, \
    Case, Language, User, Taken, Statistic, Team, Teamenroll, Submission
from sqlalchemy import join, and_
from sqlalchemy.orm import Load
from authorization import auth_required
from api.evaluators.services import update_test_cases_in_filesystem

log = logging.getLogger(__name__)

ns = api.namespace('problems', description='Operations related to problems')

@ns.route('/')
@api.header('Authorization', 'Auth token', required=True)
class ProblemCollection(Resource):

    @api.marshal_list_with(api_problem)
    @auth_required('professor')
    def get(self):
        """
        Returns list of problems.
        """
        problems = db.session.query(Problem).filter(Problem.is_subproblem == False).order_by(Problem.id).all()

        # Get user
        token = request.headers.get('Authorization', None)
        user = User.verify_auth_token(token)

        # Retrieve problem's language name
        for problem in problems:
            problem.language = Language.query.filter(Language.value == problem.language).one().name
            if (user.role == 'admin'):
                problem.can_edit = True
            elif (user.role == 'professor' and problem.author_id == user.id):
                problem.can_edit = True
            else:
                problem.can_edit = False

        return problems

@ns.route('/changestatus/<int:problem_id>/<int:status>')
@api.header('Authorization', 'Auth token', required=True)
@api.response(404, 'Problem not found.')
class ProblemStatus(Resource):

    @api.response(204, 'Problem successfully updated.')
    @auth_required('professor')
    def put(self, problem_id, status):
        """
        Updates a problem's status.
        """
        if (status == 0):
            active = False
        else:
            active = True

        Problem.query.filter(Problem.id == problem_id).update({'active' : active})

        db.session.commit()

        return None, 204

@ns.route('/problembyname/<string:problem_name>')
@api.header('Authorization', 'Auth token', required=True)
@api.response(404, 'Problem not found.')
class ProblemStatus(Resource):

    @api.marshal_with(api_problem)
    @api.response(204, 'Problem successfully updated.')
    @auth_required('professor')
    def get(self, problem_name):
        """
        Return problem by name
        """
        # Check if problem exists
        problem = db.session.query(Problem).filter(Problem.name == problem_name).first()

        if (problem is not None):
            problem.language = Language.query.filter(Language.value == problem.language).one().name
        else:
            return None, 404

        return problem

@ns.route('/<int:id>')
@api.header('Authorization', 'Auth token', required=True)
@api.response(404, 'Problem not found.')
class ProblemItem(Resource):

    @api.marshal_with(api_problem)
    @auth_required('professor')
    def get(self, id):
        """
        Returns a problem.
        """

        # Check if id is valid
        try:
            id = int(id)
        except ValueError:
            return None, 404

        # Check if problem exists
        problem = db.session.query(Problem).filter(Problem.id == id).first()

        if (problem is not None):
            problem.language = Language.query.filter(Language.value == problem.language).one().name
        else:
            return None, 404

        return problem

    @api.response(204, 'Problem successfully deleted.')
    @auth_required('admin')
    def delete(self, id):
        """
        Deletes a problem.
        """
        problem = Problem.query.filter(Problem.id == id).one()
        case = Case.query.filter(Case.problem_id == id).one()
        problemtopic = ProblemTopic.query.filter(ProblemTopic.problem_id == id).one()
        statistic = Statistic.query.filter(Statistic.problem_id == id).one()
        db.session.delete(case)
        db.session.delete(problemtopic)
        db.session.delete(statistic)
        db.session.delete(problem)
        db.session.commit()

        return None, 204

    @api.expect(api_problem)
    @api.response(204, 'Problem successfully updated.')
    @auth_required('professor')
    def put(self, id):
        """
        Updates a problem.
        """
        data = request.json

        topics = data['topics']
        test_cases  = data.get('cases')
        data.pop('topics', None)
        data.pop('cases', None)

        # Update problem's common fields
        Problem.query.filter(Problem.id == id).update(data)

        # Update test cases
        if (test_cases is not None):
            Case.query.filter(Case.problem_id == id).delete()

            # Create test cases
            for i in range(len(test_cases)):
                new_case = Case(is_sample=test_cases[i]['is_sample'],
                                input=test_cases[i]['input'],
                                feedback=test_cases[i]['feedback'],
                                output=test_cases[i]['output'],
                                problem_id=id)
                db.session.add(new_case)

            update_test_cases_in_filesystem({'problem_id' : id, 'test_cases' : test_cases})


        # Delete problem's topics
        ProblemTopic.query.filter(ProblemTopic.problem_id == id).delete()

        # Create new problem's topic
        new_problemtopic = ProblemTopic(problem_id=id,
                                    topic_id=topics)
        db.session.add(new_problemtopic)

        db.session.commit()

        return None, 204

@ns.route('/description/<int:id>')
@api.header('Authorization', 'Auth token', required=True)
@api.response(404, 'Problem not found.')
class ProblemDescription(Resource):


    @api.marshal_with(problem_description)
    @auth_required('student')
    def get(self, id):
        """
        Returns the descriptions of a problem.
        """
        # Check if id is valid
        try:
            id = int(id)
        except ValueError:
            return None, 404

        problem = db.session.query(Problem).filter(Problem.id == id).first()

        if (problem is None):
            return None, 404

        # If user is student, check that problem is activated
        # Get user
        token = request.headers.get('Authorization', None)
        user = User.verify_auth_token(token)
        if (user.role == 'student' and problem.active == False):
            return None, 404

        # Complete missing fields
        cases = db.engine.execute("""
            SELECT c.input, c.output
            FROM problem p, \"case\" c
            WHERE c.problem_id = p.id AND p.id = %d AND c.is_sample = TRUE""" % (id)).fetchall()

        descriptions = {}
        descriptions["english"]       = problem.description_english
        descriptions["spanish"]       = problem.description_spanish
        descriptions["title"]         = problem.name
        descriptions["test_cases"]    = cases
        descriptions["signature"]     = problem.signature
        descriptions["language_name"] = Language.query.filter(Language.value == problem.language).one().name
        descriptions["language_code"] = problem.language

        print(descriptions)

        return descriptions

@ns.route('/listbytopic/<int:user_id>/<int:topic_id>')
@api.header('Authorization', 'Auth token', required=True)
@api.response(404, 'Problem not found.')
class ProblemsByTopic(Resource):

    @auth_required('student')
    def get(self, user_id, topic_id):
        """
        Returns list of problems by topic, indicating if the problem has been solved by user
        """

        # Retrieve raw list of problems by topic

        # If topic id == 0, return all problems
        if (topic_id == 0):
            result = db.engine.execute("SELECT p.id, p.name, p.difficulty FROM Problem p WHERE p.active=true AND p.is_subproblem =false")
        else:
            result = db.engine.execute("SELECT p.id, p.name, p.difficulty FROM Problem p, ProblemTopic pt WHERE p.active=true AND p.is_subproblem = false AND p.id = pt.problem_id AND pt.topic_id = %d" % (topic_id))

        problems_list = []

        # Mark problem status (not attempted, attempted but wrong answer, or solved)
        for problem in result:
            # Problem not attempted
            if (len(db.engine.execute("SELECT p.id FROM Problem p WHERE p.id = %d AND NOT EXISTS (SELECT s.id FROM Submission s WHERE p.id = s.problem_id AND s.user_id = %d)" % (problem[0], user_id)).fetchall()) > 0):
                problems_list.append({'problem_id' : problem[0], 'name' : problem[1], 'difficulty' : problem[2], 'status' : 'not_attempted'})
            # Problem attempted but not solved
            elif (len(db.engine.execute("SELECT p.id FROM Problem p WHERE p.id = %d AND NOT EXISTS (SELECT s.id FROM Submission s WHERE p.id = s.problem_id AND s.grade = 100 AND s.user_id = %d)" % (problem[0], user_id)).fetchall()) > 0):
                problems_list.append({'problem_id' : problem[0], 'name' : problem[1], 'difficulty' : problem[2], 'status' : 'wrong_answer'})
            # Problem solved
            else:
                problems_list.append({'problem_id' : problem[0], 'name' : problem[1], 'difficulty' : problem[2], 'status' : 'accepted'})

        return problems_list


@ns.route('/list/')
@api.header('Authorization', 'Auth token', required=True)
class ProblemsList(Resource):

    @api.marshal_list_with(problem_table)
    @auth_required('professor')
    def get(self):
        """
        Returns list of problems for table display
        """

        # Retrieve raw list of problems by topic
        result = db.engine.execute("SELECT p.id, p.name, t.name as topic, p.difficulty, p.active, p.author_id FROM Problem p, Topic t, ProblemTopic pt WHERE p.id = pt.problem_id AND t.id = pt.topic_id").fetchall()

        # Get user
        token = request.headers.get('Authorization', None)
        user = User.verify_auth_token(token)

        problems = []

        # Retrieve problem's language name
        for row in result:
            problem = dict(row.items())
            if (user.role == 'admin'):
                problem["can_edit"] = True
            elif (user.role == 'professor' and row.author_id == user.id):
                problem["can_edit"] = True
            else:
                problem["can_edit"] = False
            problems.append(problem.copy())

        return problems

@ns.route('/mainproblems/')
@api.header('Authorization', 'Auth token', required=True)
class ProblemsList(Resource):

    @api.marshal_list_with(main_problem)
    @auth_required('professor')
    def get(self):
        """
        Returns list of main problems
        """
        # problems = db.engine.execute("""
        # SELECT *
        # FROM Problem p
        # WHERE p.is_subproblem = 'False'
        # """).fetchall()

        problems = Problem.query.filter(Problem.is_subproblem == False).all()

        return problems


# 
@ns.route('/check-parent-team/<int:team_id>/<int:problem_id>')
@api.header('Authorization', 'Auth token', required=True)
@api.response(404, 'Problem not found.')
class ProblemsByTopic(Resource):

    @auth_required('student')
    def get(self, team_id, problem_id):
        """
        Returns a list containing whether the team has done all the subchilds 
        problems or not = can they submit the parent problem?
        """

        # Retrieve raw list of the sub-problems of the main problem(problem_id)
        result = db.engine.execute("SELECT p.id, p.name, p.difficulty, p.is_subproblem FROM Problem p WHERE p.belongs_to = %d" % (problem_id)).fetchall()
        # get students of the team
        users = Teamenroll.query.filter(Teamenroll.team_id == team_id).all()
        # initialize the states of the subproblems. False means they are not done by anyone on the team
        problems_list = [False for p in result]
        index = 0
        for user in users:
            index = 0
            for problem in result:
                res = Submission.query.filter(
                    Submission.user_id == user.student_id, 
                    Submission.problem_id == problem.id,
                    Submission.grade == 100
                    ).all()
                # if the result is not an empty list
                if res:
                    problems_list[index] = True
                index = index + 1

        canSolveParent = True
        for p in problems_list:
            if p == False:
                canSolveParent = False

        if canSolveParent:
            problems_list.append({'all_accepted':'ok'})
        else:
            problems_list.append({'all_accepted':'no'})

        return problems_list

@ns.route('/listbysub-problem/<int:user_id>/<int:problem_id>')
@api.header('Authorization', 'Auth token', required=True)
@api.response(404, 'Problem not found.')
class ProblemsByTopic(Resource):

    @auth_required('student')
    def get(self, user_id, problem_id):
        """
        Returns list of sub-problem by problem, indicating if the problem has been solved by user
        """

        # Retrieve raw list of problems by sub-problems

        result = db.engine.execute("SELECT p.id, p.name, p.difficulty, p.is_subproblem FROM Problem p WHERE p.belongs_to = %d" % (problem_id))
        problems_list = []
        counter = True

        print(result)
        # Mark problem status (not attempted, attempted but wrong answer, or solved)
        for problem in result:
            # Problem not attempted
            print(problem[0])
            if (len(db.engine.execute("SELECT p.id FROM Problem p WHERE p.id = %d AND NOT EXISTS (SELECT s.id FROM Submission s WHERE p.id = s.problem_id AND s.user_id = %d)" % (problem[0], user_id)).fetchall()) > 0):
                problems_list.append({'problem_id' : problem[0], 'name' : problem[1], 'difficulty' : problem[2], 'status' : 'not_attempted', 'is_subproblem': problem[3]})
                counter = False
            # Problem attempted but not solved
            elif (len(db.engine.execute("SELECT p.id FROM Problem p WHERE p.id = %d AND NOT EXISTS (SELECT s.id FROM Submission s WHERE p.id = s.problem_id AND s.grade = 100 AND s.user_id = %d)" % (problem[0], user_id)).fetchall()) > 0):
                problems_list.append({'problem_id' : problem[0], 'name' : problem[1], 'difficulty' : problem[2], 'status' : 'wrong_answer', 'is_subproblem':problem[3]})
                counter = False
            # Problem solved
            else:
                problems_list.append({'problem_id' : problem[0], 'name' : problem[1], 'difficulty' : problem[2], 'status' : 'accepted', 'is_subproblem':problem[3]})

        if counter:
            problems_list.append({'all_accepted':'ok'})
        else:
            problems_list.append({'all_accepted':'no'})

        return problems_list

@ns.route('/take-problem/<int:user_id>/<int:problem_id>/<int:team_id>')
@api.header('Authorization', 'Auth token', required=True)
@api.response(404, 'Problem not found')
class TakeProblem(Resource):
    @auth_required('student')
    def put(self, user_id, problem_id, team_id):
        """
        Marks a problem as Taken
        """
        validates = db.engine.execute("SELECT p.belongs_to FROM Problem p WHERE p.id = %d" % (problem_id))
        main_problem = validates
        for row in main_problem:
            print(row[0])
            if row[0] is not None:
                validates = db.engine.execute("SELECT p.id FROM Problem p WHERE p.belongs_to = %d" % (row[0]))
                sub_problems = validates
                for problem in sub_problems:
                    print(problem[0])
                    validates = db.engine.execute("SELECT t.id FROM Taken t WHERE t.user_id = %d AND t.problem_id = %d" % (user_id, problem[0]))
                    # User already has one problem from the sub_problems taken
                    if validates.rowcount > 0:
                        return None, 404
            else:
                return None, 404

        new_taken = Taken(user_id = user_id, problem_id = problem_id, team_id = team_id)
        db.session.add(new_taken)
        db.session.commit()


@ns.route('/leave_problem/<int:user_id>/<int:problem_id>')
@api.header('Authorization', 'Auth toke', required=True)
@api.response(404, 'Problem not found')
class LeaveProblem(Resource):
    @auth_required('student')
    def delete(self, user_id, problem_id):
        """
        Unmarks a problem
        """
        taken = Taken.query.filter(and_(Taken.user_id == user_id, Taken.problem_id == problem_id)).first()
        print(type(taken))
        if taken is not None:
            db.session.delete(taken)
            db.session.commit()
            return None, 204
        else:
            return None, 404
