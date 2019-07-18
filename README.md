# 4castinate

## How to use
### 0. Prerequisites:
       - Python 3.6

       - pip

       - virtualenv

       - awsebcli
### 1. Clone and cd into root (outer 'ebdjango' dir)
### 2. Create a new virtualenv. At the end of this step, you should see : 
       'virtualenv ~/django-dev-env'
### 3. Activate it:                
       'source ~/eb-virt/bin/activate'
### 4. Install requirements:
       'pip install -r requirements.txt'
### 5. Run the application locally:
       'python manage.py runserver'
### 6. Deactivate environment:
       'deactivate' 
####   Note: Activate it back only when you need to install other dependencies and before commiting, do: 
       'pip freeze > requirements.txt' to overwrite requirements
### 7. Deploy the app with eb cli. Cleanup when you're done:
       https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-django.html
