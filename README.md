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
### 1. Clone and cd into root (outer 'ebdjango' dir) - all shell commands below are executed from root
### 2. Create a new virtualenv by running: 
       mkvirtualenv django-dev-env
### 3. Activate it:                
       workon django-dev-env
### 4. Install requirements for your virtualenv:
       pip install -r requirements.txt
### 5. Run the application locally:
#### 5.1 Set up [OAuth](https://en.wikipedia.org/wiki/OAuth) authentication for Jira REST API - recommended for both Jira Cloud and Jira Server
#### (skip to 5.2 if you don't want to use Jira REST API)
#### (skip to 5.2 for [Basic](https://developer.atlassian.com/cloud/jira/platform/jira-rest-api-basic-authentication/) authentication - works only for Jira Cloud, but configuration is much easier)
##### 5.1.1 Follow [Step 1: Configure Jira](https://developer.atlassian.com/server/jira/platform/oauth/), but put the created files in same directory as 'jira_oauth_script.py' (overwrite the existing files).
##### 5.1.2 Run the script and follow instructions in the terminal. Remember the contents of 'oauth_token' and 'oauth_token_secret' printed in the terminal. 
       python forecast/helperMethods/oauth/jira_oauth_script.py 
#### 5.2 Set environment variables in your virtualenv
##### 5.2.1 Open the environment file:
       open ~/.virtualenvs/django-dev-env/bin/activate
##### 5.2.2 Edit the environment file with the needed variables (paste them at the end of the file, one per line). If you don't want to fetch data from Jira, just export the Jira Variables as given below. If you've opted for OAuth, edit the jira_oauth_token and jira_oauth_token_secret variables (5.1.2). If you've opted for Basic authentication, edit the jira_email and jira_api_token variables. In both cases, edit the jira_url variable and DON'T edit the variables for the other case. Note that you need the SECRET_KEY variable set up properly (it is used [internally](https://docs.djangoproject.com/en/2.2/topics/signing/) by Django):
       export SECRET_KEY='<your secret Django key>'

       export JIRA_URL='https://<your_jira_domain>.atlassian.net'

       export JIRA_EMAIL='<jira_user_email>'
       export JIRA_API_TOKEN='<jira_api_token>'

       export JIRA_OAUTH_TOKEN = <oauth_token>
       export JIRA_OAUTH_TOKEN_SECRET = <oauth_token_secret>
##### 5.2.3 Deactivate environment:
       deactivate
##### 5.2.4 Activate it back to reload the new changes:
       workon django-dev-env

##### 5.2.5 To verify that the variables are set up, run this for each of them:
       echo $SECRET_KEY
      
#### 5.3 Run the app on localhost:
         python manage.py runserver
     
#### 5.4 Test the app:
         python manage.py test forecast
#### 5.5 Test the app with code coverage:
         coverage run --source='./forecast' manage.py test forecast
####     Followed by:
         coverage report
### 6. Deploy the app with eb cli. 
#### 6.1 Follow steps [1-3](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-django.html#python-django-deploy). The *EB CLI init* steps you'll have to perform just at the time when you clone the repo:
#### 6.2 Set EB environment variables. This has to be done for each new environment you make on AWS EB:
       eb setenv SECRET_KEY=$SECRET_KEY JIRA_API_TOKEN=$JIRA_API_TOKEN JIRA_URL=$JIRA_URL JIRA_EMAIL=$JIRA_EMAIL JIRA_OAUTH_TOKEN=$JIRA_OAUTH_TOKEN JIRA_OAUTH_TOKEN_SECRET=$JIRA_OAUTH_TOKEN_SECRET
       
       You can verify they were set in Elastic Beanstalk by running:
       eb printenv
#### 6.3 Deploy your local repository:
       eb deploy
#### 6.4 Access the website manually / from eb cli [step 7](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-django.html#python-django-deploy):
       eb open
#### 6.5 [Cleanup](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-django.html#python-django-stopping).

### 7. Note: If you install other dependencies (i.e. pip install), before you commit, do:
       pip freeze > requirements.txt