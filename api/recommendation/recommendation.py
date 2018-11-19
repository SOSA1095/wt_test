import logging

from flask import request, abort, jsonify, g
from flask_restplus import Resource
from api.restplus import api
from sqlalchemy import join, and_
from sqlalchemy.orm import Load
from authorization import auth_required
from api.problems.serializers import problem as api_problem
from models import db, Submission, Problem

from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


import functools

import numpy as np

log = logging.getLogger(__name__)

ns = api.namespace('recomendation', description='Operations related to recomendation of problem')

def distance(x, y):
	return np.sqrt(np.sum((x-y)**2))


@ns.route('/recommend/<int:id>')
@api.header('Authorization', 'Auth token', required=True)
class Recommendation(Resource):
	@api.marshal_with(api_problem)
	@auth_required('student')
	def get(self, id):
		"""
		Returns a recommended problem
		"""
		x_columns = ['grade', 'no_of_attempt']
		y_column = ['problem_id']

		general_statistics_grades = db.session.query(Submission.grade).filter(Submission.user_id != id).all()
		general_statistics_attempts = db.session.query(Submission.no_of_attempt).filter(Submission.user_id != id).all()
		general_statistics_problem_id = db.session.query(Submission.problem_id).filter(Submission.user_id != id).all()
		user_statistic_grade = db.session.query(Submission.grade).filter(Submission.user_id == id).all()
		user_statistic_attempts = db.session.query(Submission.no_of_attempt).filter(Submission.user_id == id).all()
		user_statistic_problem_id = db.session.query(Submission.problem_id).filter(Submission.user_id == id).all()
		# The user hasn't submitted any problems so we can't recommend anything
		if len(user_statistic_attempts) is 0:
			return None

		# Calculate user data
		# Calculate the average no of attemps for the user
		# we do it this way since sqlalchemy returns a weird format
		user_attempts_sum = 0
		min_user_attempts = 9999999999
		max_user_attempts = -1
		for i in user_statistic_attempts:
			for key in i:
				min_user_attempts = min(min_user_attempts, key)
				max_user_attempts = max(max_user_attempts, key)
				user_attempts_sum += key

		# Same stuff for the grades
		user_grade_sum = 0;
		min_user_grade = 9999999999
		max_user_grade = -1
		for i in user_statistic_grade:
			for key in i:
				user_grade_sum += key
				min_user_grade = min(min_user_grade, key)
				max_user_grade = max(max_user_grade, key)

		# Store the IDS of the general problems
		problems_ids = []
		for i in general_statistics_problem_id:
			for key in i:
				problems_ids.append(key)

		user_statistic_attempts = user_attempts_sum / len(user_statistic_attempts)
		user_statistic_grade = user_grade_sum / len(user_statistic_grade)
		# Get the min and max from the grades and attemps
		# these could be new minimum/maximum

		# Calculate the min and max to normalize the data
		min_grade = min(general_statistics_grades)[0]
		min_grade = min(min_grade, min_user_attempts)
		max_grade = max(general_statistics_grades)[0]
		max_grade = max(max_grade, max_user_grade)
		min_attemps = min(general_statistics_attempts)[0]
		min_attemps = min(min_attemps, min_user_grade)
		max_attemps = max(general_statistics_attempts)[0]
		max_attemps = max(max_attemps, max_user_attempts)


		normalized_general_statistics_grades = []
		normalized_general_statistics_attempts = []
		# Normalize the general data
		for i in general_statistics_grades:
			for key in i:
				normalized_general_statistics_grades.append(((key-min_grade)/(max_grade-min_grade)))
		for i in general_statistics_attempts:
			for key in i:
				normalized_general_statistics_attempts.append(((key-min_attemps)/(max_attemps-min_attemps)))

		# Normalize the user data
		user_statistic_grade = (user_statistic_grade - min_grade) / (max_grade - min_grade)
		user_statistic_attempts = (user_statistic_attempts - min_attemps) / (max_attemps - min_attemps)

		current_min_distance = 99999999
		counter = 0
		problem_id_index = -1
		for grade, attempt in zip(normalized_general_statistics_grades, normalized_general_statistics_attempts):
			user_data = np.array([[user_statistic_grade, user_statistic_attempts]])
			general_data = np.array([[grade], [attempt]])
			if distance(user_data, general_data) < current_min_distance:
				current_min_distance = distance(user_data, general_data)
				problem_id_index = counter
			counter += 1
		problem_id = problems_ids[problem_id_index]
		problem = db.session.query(Problem).filter(Problem.id == problem_id).first()
		return problem