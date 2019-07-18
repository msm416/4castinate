# 4castinate

## How to use
### 0. Prerequisites:
       - Python 3.6

       - pip

       - virtualenv

       - awsebcli
### 1. Clone and cd into root (outer 'ebdjango' dir)
### 2. Create a new virtualenv. At the end of this step, you should see: 
       virtualenv ~/django-dev-env
### 3. Activate it:                
       source ~/django-dev-env/bin/activate
### 4. Install requirements:
       pip install -r requirements.txt
### 5. Run the application locally:
#### 5.1 Set environment variable in your terminal: 
       export SECRET_KEY='YOUR_AWS_SECRET_KEY'
       e.g. export SECRET_KEY='abcd1234'
       you can verify it with:
       echo $SECRET_KEY
#### 5.2 Run the app
       python manage.py runserver
### 6. Deactivate environment:
       deactivate
####   Note: Activate it back only when you need to install other dependencies and before commiting, do: 
       pip freeze > requirements.txt
### 7. Deploy the app with eb cli. 
#### 7.1 Follow steps [1-6](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-django.html#python-django-deploy). The *EB CLI init* steps you'll have to perform just at the time when you clone the repo:
#### 7.2 Set environment variable in environment. This has to be done for each new environment you make on AWS EB:
       eb setenv SECRET_KEY='YOUR_AWS_SECRET_KEY' 
       e.g. eb setenv SECRET_KEY='abcd1234'
       you can verify it with:
       eb printenv
#### 7.2 Access the website manually / from eb cli [step 7](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-django.html#python-django-deploy):
       eb open
### 8. [Cleanup](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-django.html#python-django-stopping).
