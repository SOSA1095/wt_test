redis: redis-server
worker0: rq worker j_0
worker1: rq worker j_2
worker2: rq worker j_2
worker3: rq worker j_3
worker4: rq worker j_4
create_admin: python manage.py create_admin 
init: python manage.py db init
migrate: python manage.py db migrate
upgrade: python manage.py db upgrade
web: python manage.py runserver --host 0.0.0.0 --port ${PORT}