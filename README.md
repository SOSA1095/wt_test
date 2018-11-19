### Install all the stuff you need to run the website.

You can install everything from brew (or another packet manager)
In this example I'm using Homebrew
Node + npm:
	`brew install node` (This command also install npm)
Python (To make a virtual environment for the project in your computer):
	`brew install python3`
Angular-cli:	
	`brew install angular-cli`
Docker:
	`brew install docker`


### Virtual Environment

`pip3 install virtualenv`

### Recommended versions

Once you have the virtual enviroment set up download the .txt file that contains all the packages and versions you need for this project.

run "pip install -r requirements.txt"

(verify all requirements are installed, perhaps when you run python app.py you'll realize some are missing)

pip install psycopg2==2.6.1 Flask-SQLAlchemy===2.1 Flask-Migrate==1.8.0


### Database

For this we are going to use PostresSQL. 
`brew install postgres`
Once you have it installed to create the database use:
`psql postgres`
then
`CREATE DATABASE t247_dev;`

\q

### Redis - Server   
`brew install redis`

A quick startup guide, in case you need it.

<http://redis.io/topics/quickstart>


### Once you have the project installed

Change apiURL in file Angular/t247-app/src/environment.ts and environemtn.prod.ts to 'http://localhost:5000/api'. 
This is to avoid changes on tutoring24/7

export DATABASE_URL="postgresql://localhost/t247_dev"

### Activate Virtual Environment
`source env/bin/activate`
### Update Database
`python manage.py db upgrade`
### Run all programs

`redis-server & python app.py`

### Create a User

Once you have everything running, go to localhost:5000/api 

Go to the tab of user and create a new user admin of your choice.

#Stop server:
`control-c`
`fg`
`control-c`
`deactivate`