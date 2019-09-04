from django.urls import path

from . import views

app_name = 'forecast'
urlpatterns = [
    path('', views.index, name='index'),
    # ex: /forecast/
    path('<int:query_id>/', views.detail, name='detail'),
    # ex: /forecast/5/
    path('fetch/', views.fetch, name='fetch'),
    # ex: /forecast/fetch/
    path('iterations/', views.iterations, name='iterations'),
    # ex: /forecast/iterations/
    path('issues/', views.issues, name='issues'),
    # ex: /forecast/iterations/
    path('<int:board_id>/results/<int:form_id>/', views.results, name='results'),
    # ex: /forecast/5/results/2
    path('<int:board_id>/estimate/', views.estimate, name='estimate'),
    # ex: /forecast/5/estimate/
    path('<int:query_id>/create-form/', views.create_form, name='create_form'),
    # ex: /forecast/5/create-form/
    path('<int:board_id>/create-query-from-data/', views.create_query_from_data, name='create_query_from_data'),
    # ex: /forecast/5/create_query_from_data/
    path('create-query-from-jql/', views.create_query_from_jql, name='create_query_from_jql'),
    # ex: /forecast/create_query_from_jql/
    path('<int:query_id>/create_simulation/', views.create_simulation, name='create_simulation'),
    # ex: /forecast/5/create_simulation/

    path('webhook/', views.webhook, name='webhook')
    # ex: /forecast/webhook/
    # THIS IS A JIRA WEBHOOK ENDPOINT
]
