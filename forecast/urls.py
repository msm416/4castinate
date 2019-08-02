from django.urls import path

from . import views

app_name = 'forecast'
urlpatterns = [
    path('', views.index, name='index'),
    # ex: /forecast/
    path('<int:board_id>/', views.detail, name='detail'),
    # ex: /forecast/5/
    path('<int:board_id>/results/<int:form_id>/', views.results, name='results'),
    # ex: /forecast/5/results/2
    path('<int:board_id>/estimate/', views.estimate, name='estimate'),
    # ex: /forecast/5/estimate/

    path('webhook/', views.webhook, name='webhook')
    # ex: /forecast/webhook/
    # THIS IS A JIRA WEBHOOK ENDPOINT
]
