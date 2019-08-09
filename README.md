# 4castinate
## About
### Automated forecasting tool for Agile Teams. 
### Developed at [FundingCircle](https://www.fundingcircle.com/uk/). Inspired by [FocusedObjective](http://focusedobjective.com/story-size-estimates-matter-experiment/).
## How to use
### 0. Prerequisites:
       - Python 3.6

       - pip

       - virtualenv
       
       - virtualenvwrapper

       - awsebcli
### 1. Clone and cd into root (outer 'ebdjango' dir).
### 2. Create a new virtualenv by running: 
       mkvirtualenv django-dev-env
### 3. Activate it:                
       workon django-dev-env
### 4. Install requirements for your virtualenv:
       pip install -r requirements.txt
### 5. Run the application locally:
#### 5.1 Set environment variables in your virtualenv
##### 5.1.1 Open the environment file:
       open ~/.virtualenvs/django-dev-env/bin/activate
##### 5.1.2 Edit the environment file with the needed variables (paste them at the end of the file, one per line). If you don't want to fetch data from Jira, just export the 3 Jira Variables as given below (and ignore step 5.1.6):
       export SECRET_KEY='<your secret Django key>'

       export API_TOKEN='<jira_api_token>'
       export JIRA_URL='https://<your_jira_domain>.atlassian.net/rest/agile/1.0/board'
       export JIRA_EMAIL='<jira_user_email>'
     
##### 5.1.3 Deactivate environment:
       deactivate
##### 5.1.4 Activate it back to reload the new changes:
       workon django-dev-env

##### 5.1.5 To verify that the variables are set up, run this for each of them:
       echo $SECRET_KEY

##### 5.1.6 To verify that the Jira variables are correct, run this and [check the response](https://developer.atlassian.com/cloud/jira/software/rest/#api-rest-agile-1-0-board-get):
       curl --request GET \
       --url $JIRA_URL/board \
       --user $JIRA_EMAIL:$API_TOKEN \
       --header 'Accept: application/json'
      
#### 5.2 Run the app on localhost:
         python manage.py runserver
     
#### 5.3 Test the app:
         python manage.py test forecast
#### 5.4 Test the app with code coverage:
         coverage run --source='./forecast' manage.py test forecast
####     Followed by:
         coverage report
### 6. Deploy the app with eb cli. 
#### 6.1 Follow steps [1-3](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-django.html#python-django-deploy). The *EB CLI init* steps you'll have to perform just at the time when you clone the repo:
#### 6.2 Set EB environment variables. This has to be done for each new environment you make on AWS EB:
       eb setenv SECRET_KEY=$SECRET_KEY API_TOKEN=$API_TOKEN JIRA_URL=$JIRA_URL JIRA_EMAIL=$JIRA_EMAIL
       
       You can verify they were set in Elastic Beanstalk by running:
       eb printenv
#### 6.3 Deploy your local repository:
       eb deploy
#### 6.4 Access the website manually / from eb cli [step 7](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-django.html#python-django-deploy):
       eb open
#### 6.5 [Cleanup](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-django.html#python-django-stopping).

### 7. Note: If you install other dependencies (i.e. pip install), before you commit, do:
       pip freeze > requirements.txt