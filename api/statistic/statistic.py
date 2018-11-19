import logging

from flask import request, abort, jsonify, g
from flask_restplus import Resource
from api.problems.serializers import problem as api_problem
from api.problems.serializers import problem_table, problem_description, problem_edition
from api.restplus import api
from sqlalchemy import join, and_
from sqlalchemy.orm import Load
from authorization import auth_required
from models import db, User, Problem, Group, Statistic, Student, Submission, Admin, Professor, Topic, ProblemTopic
from api.evaluators.services import update_test_cases_in_filesystem

log = logging.getLogger(__name__)

ns = api.namespace('statistics', description='Operations related to statistics')

@ns.route('/Amount-Users')
@api.header('Authorization', 'Auth token', required=True)
class AmountUsers(Resource):

    @auth_required('professor')
    def get(self):
        """
        Statistic regarding amout of users by category
        """
        user_list = {'Student':0, 'Professor':0, 'Admin':0}

        # Retrive amount of users per category
        students = Student.query.order_by(User.id).all()
        professor = Professor.query.order_by(User.id).all()
        admin = Admin.query.order_by(User.id).all()

        # Update dictionaries
        user_list['Student'] = len(students)
        user_list['Professor'] = len(professor)
        user_list['Admin'] = len(admin)


        return jsonify(user_list)

@ns.route('/<int:group_id>')
@api.header('Authorization', 'Auth token', required=True)
class GroupStatistic(Resource):

    @auth_required('professor')
    def get(self, group_id):
        """
        Statistics of entire group
        """

        Submissions_Total = 0.0
        AC_Total = 0.0

        students = Group.query.filter(Group.id == group_id).all()

        for i in range(len(students[0].students)):
            student = students[0].students[i].id
            # print(student)
            submissions = Submission.query.filter(Submission.user_id == student)
            for submission in submissions:
                if submission.grade is 100:
                    AC_Total = AC_Total + 1.0
                Submissions_Total = Submissions_Total + 1.0
        return (AC_Total / Submissions_Total) * 100

@ns.route('/GroupsStats')
@api.header('Authorization', 'Auth token', required=True)
class GroupVSGroup(Resource):

    @auth_required('professor')
    def get(self):
        """
        Statistic of all groups
        """

        group_list = []

        groups = Group.query.order_by(Group.id).all()
        for group in groups:
            students = Group.query.filter(Group.id == group.id).all()
            Submissions_Total = 0.0
            AC_Total = 0.0

            for i in range(len(students[0].students)):
                student = students[0].students[i].id
                submissions = Submission.query.filter(Submission.user_id == student)
                for submission in submissions:
                    if submission.grade is 100:
                        AC_Total = AC_Total + 1.0
                    Submissions_Total = Submissions_Total + 1.0
            if Submissions_Total == 0:
                percent = 0
            else:
                percent = (AC_Total / Submissions_Total) * 100
            group_list.append({ 'Group ' + str(group.id) + ' ' + group.course.name + ' ' + group.period : percent})
        return jsonify(group_list)

@ns.route('/AC-Ratio/<int:problem_id>')
@api.header('Authorization', 'Auth token', required=True)
class AcceptedStatisticOne(Resource):

    @auth_required('professor')
    def get(self, problem_id):
        """
        Statistic of one single problem (AC)
        """

        problem = Statistic.query.filter(Statistic.problem_id == problem_id).one()
        if problem.total_submissions is 0:
            return 0
        return (problem.total_accepted_submissions / problem.total_submissions) * 100

@ns.route('/WA-Ratio/<int:problem_id>')
@api.header('Authorization', 'Auth token', required=True)
class AcceptedStatisticTwo(Resource):

    @auth_required('professor')
    def get(self, problem_id):
        """
        Statistic of one single problem (WA)
        """

        problem = Statistic.query.filter(Statistic.problem_id == problem_id).one()
        if problem.total_submissions is 0:
            return 0
        return 100 - ((problem[0].total_accepted_submissions / problem[0].total_submissions) * 100)

@ns.route('/Amount-Problem-Topic')
@api.header('Authorization', 'Auth token', required=True)
class ProblemAmountPerTopic(Resource):

    @auth_required('professor')
    def get(self):
        """
        Statistic of amount of problem per topic
        """
        list_topics = {}
        topics = Topic.query.order_by(Topic.id).all()
        for row in topics:
            list_topics[row.name] = 0
            problem_topic = ProblemTopic.query.filter(ProblemTopic.topic_id == row.id).all()
            list_topics[row.name] = len(problem_topic)

        return list_topics

@ns.route('/AC-Ratio-Topic')
@api.header('Authorization', 'Auth token', required=True)
class StatisticPerTopic(Resource):

    @auth_required('professor')
    def get(self):
        """
        Statistic of AC per topic
        """
        list_topics = {}
        topics = Topic.query.order_by(Topic.id).all()
        for row in topics:
            list_topics[row.name] = 0.0
            problem_topic = ProblemTopic.query.filter(ProblemTopic.topic_id == row.id).all()
            AC = 0.0
            total = 0.0
            for problem in problem_topic:
                child = Problem.query.filter(Problem.belongs_to == problem.problem_id)
                for each in child:
                    stat = Statistic.query.filter(Statistic.problem_id == each.id).all()
                    AC = AC + stat[0].total_accepted_submissions
                    total = total + stat[0].total_submissions
            print(total, AC)
            if total == 0.0 or AC == 0.0:
                percent = 0.0
            else:
                percent = (AC / total) * 100
            list_topics[row.name] = percent
        return list_topics
