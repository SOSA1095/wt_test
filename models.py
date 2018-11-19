from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from sqlalchemy.ext.declarative import declared_attr
from enums import SubmissionState, SubmissionResult
from sqlalchemy import inspect
import pytz

db = SQLAlchemy()


class Base(db.Model):

    """A base class that automatically creates the table name and
    primary key.
    """

    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.now(tz=pytz.timezone('America/Monterrey')))
    updated = db.Column(db.DateTime, default=datetime.now(tz=pytz.timezone('America/Monterrey')))
    # updated = db.Column(db.DateTime, default=datetime.now)

    # @declared_attr
    # def __tablename__(cls):
    #     return cls.__name__.lower()

    def readable_date(self, date, format='%H:%M on %-d %B'):
        """Format the given date using the given format."""
        return date.strftime(format)


class User(Base, UserMixin):

    """
    A forum user. `UserMixin` provides the following methods:
        `is_active(self)`
            Returns ``True`` if the user is active.
        `is_authenticated(self)`
            Always returns ``True``.
        `is_anonymous(self)`
            Always returns ``False``.
        `get_auth_token(self)`
            Returns the user's authentication token.
        `has_role(self, role)`
            Returns ``True`` if the user identifies with the specified role.
        `get_id(self)`
            Returns ``self.id``.
        `__eq__(self, other)`
            Returns ``True`` if the two users have the same id.
        `__ne__(self, other)`
            Returns the opposite of `__eq__`.
    """
    __tablename__ = 'user'
    email = db.Column(db.String(255), unique=True, nullable=False)
    enrollment = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    active = db.Column(db.Boolean)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    role = db.Column(db.String(20))
    problems = db.relationship("Problem", back_populates="author", cascade="save-update, merge, delete")
    submissions = db.relationship("Submission", back_populates="user", cascade="save-update, merge, delete")
    taken = db.relationship("Taken", back_populates="user", cascade="save-update, merge, delete")
    forums = db.relationship("Forum", back_populates="author", cascade="save-update, merge, delete")
    comments = db.relationship("Comment", back_populates="author")
    messages = db.relationship("Message", back_populates="sender")

    __mapper_args__ = {
        'polymorphic_on': role,
        'polymorphic_identity': 'user'
    }

    def __repr__(self):
        return '<User(%s, %s)>' % (self.id, self.email)

    def __unicode__(self):
        return self.email

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=60*60*24*30):
        s = Serializer('this-really-needs-to-be-changed', expires_in=60*60*24*30)
        return s.dumps({'id': self.id, 'role': self.role})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer('this-really-needs-to-be-changed')
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        user = User.query.get(data['id'])
        return user


class Admin(User):
    """docstring for Admin"""
    __mapper_args__ = {
        'polymorphic_identity': 'admin'
    }


class Student(User):
    """docstring for Student"""
    groups = db.relationship("Group", secondary="enrollment", back_populates="students")
    # relationship for several teams, not just one team
    team = db.relationship("Team", secondary="teamenroll", back_populates="students")

    __mapper_args__ = {
        'polymorphic_identity': 'student'
    }


class Professor(User):
    """docstring for Professor"""
    managed_groups = db.relationship("Group", back_populates="professor", cascade="save-update, merge, delete")

    __mapper_args__ = {
        'polymorphic_identity': 'professor'
    }


class Course(Base):
    """docstring for Course"""
    __tablename__ = 'course'
    name = db.Column(db.String(255), nullable=False)
    groups = db.relationship("Group", back_populates="course", cascade="save-update, merge, delete")
    topics = db.relationship("Topic", secondary="relevanttopic",
                             back_populates="courses")


class Topic(Base):
    """docstring for Course"""
    __tablename__ = 'topic'
    name = db.Column(db.String(255), nullable=False)
    courses = db.relationship("Course", secondary="relevanttopic",
                              back_populates="topics")
    problems = db.relationship("Problem", secondary="problemtopic",
                               back_populates="topics")


class RelevantTopic(Base):
    """docstring for Course"""
    __tablename__ = 'relevanttopic'
    name = db.Column(db.String(255))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))


class Group(Base):
    """docstring for Group"""
    __tablename__ = 'group'
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    course = db.relationship("Course", back_populates="groups")
    period = db.Column(db.String(255), nullable=False)
    students = db.relationship("Student", secondary="enrollment",
                               back_populates="groups")
    teams = db.relationship("Team", back_populates='group')
    professor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    professor = db.relationship("Professor", back_populates="managed_groups")
    assignments = db.relationship("Assignment", back_populates="group", cascade="save-update, merge, delete")
    contests = db.relationship("Contest", back_populates="group", cascade="save-update, merge, delete")


class Enrollment(Base):
    """docstring for Enrollment"""
    __tablename__ = 'enrollment'
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Teamenroll(Base):
    """docstring for Teamenroll"""
    __tablename__ = 'teamenroll'
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class ProblemTopic(Base):
    """docstring for Course"""
    __tablename__ = 'problemtopic'
    name = db.Column(db.String(255))
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'))
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))

class Problem(Base):
    """docstring for Problem"""
    __tablename__ = 'problem'
    name = db.Column(db.String(255), unique=True, nullable=False)
    difficulty = db.Column(db.Integer)
    active = db.Column(db.Boolean)
    language = db.Column(db.String(255), nullable=False)
    code = db.Column(db.Text, nullable=False)
    template = db.Column(db.Text)
    signature = db.Column(db.Text)
    description_english = db.Column(db.Text, nullable=False)
    description_spanish = db.Column(db.Text)
    time_limit = db.Column(db.Integer)
    memory_limit = db.Column(db.Integer)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship("User", back_populates="problems")

    cases = db.relationship("Case", back_populates="problem",
                            order_by="Case.id", cascade="save-update, merge, delete, delete-orphan")
    assignments = db.relationship("Assignment", back_populates="problem", cascade="save-update, merge, delete")
    submissions = db.relationship("Submission", back_populates="problem", cascade="save-update, merge, delete")
    topics = db.relationship("Topic", secondary="problemtopic",
                             back_populates="problems", cascade="save-update, merge, delete")
    stat = db.relationship("Statistic", uselist=False, back_populates="problem", cascade="save-update, merge, delete")

    contests = db.relationship("Contest", secondary="contestproblem", back_populates="problems")

    # these lines represent a 1 to N relation, which is also recursive for Problem.
    # i.e. a problem may have several 'subproblems' (functions or parts)
    id = db.Column(db.Integer, primary_key=True)

    is_subproblem = db.Column(db.Boolean)
    belongs_to = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=True)
    sub_problems = db.relationship("Problem", backref=db.backref('problem', remote_side=id), cascade="save-update, merge, delete")

class Case(Base):
    """docstring for Case"""
    __tablename__ = 'case'
    input = db.Column(db.Text, nullable=False)
    feedback = db.Column(db.Text)
    output = db.Column(db.Text)
    is_sample = db.Column(db.Boolean)

    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=False)
    problem = db.relationship("Problem", back_populates="cases")


class Submission(Base):
    """docstring for Submission"""
    __tablename__ = 'submission'
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(255), nullable=False)
    feedback_list = db.Column(db.JSON)
    grade = db.Column(db.Integer)
    no_of_attempt = db.Column(db.Integer)
    state = db.Column(db.Enum(SubmissionState))
    result = db.Column(db.Enum(SubmissionResult))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship("User", back_populates="submissions")
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'))
    problem = db.relationship("Problem", back_populates="submissions")


class Assignment(Base):
    """docstring for Assignment"""
    __tablename__ = 'assignment'
    title = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.DateTime(timezone=True), default=datetime.now(tz=pytz.timezone('America/Monterrey')), nullable=False)
    due_date = db.Column(db.DateTime(timezone=True), default=datetime.now(tz=pytz.timezone('America/Monterrey')), nullable=False)

    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    group = db.relationship("Group", back_populates="assignments")
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=False)
    problem = db.relationship("Problem", back_populates="assignments")


class Language(Base):
    """docstring for Assignment"""
    __tablename__ = 'language'

    name = db.Column(db.String(255), nullable=False)
    value = db.Column(db.String(255), nullable=False, unique=True)
    extension = db.Column(db.String(255), nullable=False)

class Team(Base):
    """docstring for Team"""
    __tablename__ = 'team'

    name = db.Column(db.String(255), nullable=True)

    students = db.relationship("Student", secondary="teamenroll", back_populates="team")
    professor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    group = db.relationship("Group", back_populates='teams')
    messages = db.relationship('Message', back_populates="parent")
    contests = db.relationship('Contest', secondary='contestteam', back_populates='teams')

class Taken(Base):
    """docstring for Taken"""
    __tablename__ = 'taken'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship("User", back_populates="taken")
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)

class Statistic(Base):
    """docstring for Statistic"""
    __tablename__ = 'statistic'

    total_submissions = db.Column(db.Integer)
    total_accepted_submissions = db.Column(db.Integer)
    problem_id = db.Column(db.Integer, db.ForeignKey("problem.id"), nullable = False)
    problem = db.relationship("Problem", back_populates="stat")

class Forum(Base):
    """docstring for Forum"""
    __tablename__ = 'forum'
    name = db.Column(db.String(255), nullable=False)
    author_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))
    # author id has the id of a professor or admin, since only they can create forum
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship("User", back_populates="forums")

    comments = db.relationship("Comment", back_populates="forum")

class Comment(Base):
    """docstring for Comment"""
    __tablename__ = 'comment'

    text = db.Column(db.String(255), nullable=False)
    isVisible = db.Column(db.Boolean, default = False)
    likes = db.Column(db.Integer, default = 0)
    dislikes = db.Column(db.Integer, default = 0)
    forum_id = db.Column(db.Integer, db.ForeignKey("forum.id"), nullable=False)
    forum = db.relationship("Forum", back_populates="comments")

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship("User", back_populates="comments")

class Message(Base):
    """ docstring for Message """
    __tablename__ = 'message'
    text = db.Column(db.String(255), nullable=False)
    fecha = db.Column(db.String(255), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    parent = db.relationship("Team", back_populates="messages")
    # user relation
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sender = db.relationship("User", back_populates="messages")

class ContestProblem(Base):
    """docstring for ContestProblem"""
    __tablename__ = 'contestproblem'
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'))
    contest_id = db.Column(db.Integer, db.ForeignKey('contest.id'))

class ContestTeam(Base):
    """docstring for ContestTeam"""
    __tablename__ = 'contestteam'
    contest_id = db.Column(db.Integer, db.ForeignKey('contest.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))

class Contest(Base):
    """docstring for Contest"""
    __tablename__ = 'contest'
    name = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.DateTime(timezone=True), default=datetime.now(tz=pytz.timezone('America/Monterrey')), nullable=False)
    end_date = db.Column(db.DateTime(timezone=True), default=datetime.now(tz=pytz.timezone('America/Monterrey')), nullable=False)
    # timezone aware dates
    s_date = db.Column(db.DateTime(timezone=True), default=datetime.now(tz=pytz.timezone('America/Monterrey')), nullable=False)
    e_date = db.Column(db.DateTime(timezone=True), default=datetime.now(tz=pytz.timezone('America/Monterrey')), nullable=False)
    problems = db.relationship("Problem", secondary="contestproblem", back_populates="contests") 

    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    group = db.relationship("Group", back_populates="contests")

    teams = db.relationship('Team', secondary='contestteam', back_populates='contests')