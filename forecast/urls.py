from django.urls import path

from . import views

app_name = 'forecast'
urlpatterns = [
    path('', views.index, name='index'),
    # ex: /forecast/
    path('<int:query_id>/', views.detail, name='detail'),
    # ex: /forecast/5/
    path('<int:query_id>/results/<int:simulation_id>/', views.results, name='results'),
    # ex: /forecast/5/results/2
    path('<int:query_id>/modify-form/', views.modify_form, name='modify_form'),
    # ex: /forecast/5/create-form/
    path('create-query/', views.create_query, name='create_query'),
    # ex: /forecast/create-query/
    path('<int:query_id>/create_simulation/', views.create_simulation, name='create_simulation'),
    # ex: /forecast/5/create-simulation/
]
