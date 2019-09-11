from django.urls import path

from . import views

app_name = 'forecast'
urlpatterns = [
    path('', views.index, name='index'),
    # ex: /forecast/
    path('<int:query_id>/', views.detail, name='detail'),
    # ex: /forecast/5/
    path('<int:query_id>/<str:run_simulation_response>', views.detail, name='detail'),
    # ex: /forecast/5/message
    path('<int:query_id>/results/<int:simulation_id>/', views.results, name='results'),
    # ex: /forecast/5/results/2
    path('<int:query_id>/run-simulation/', views.run_simulation, name='run_simulation'),
    # ex: /forecast/5/create-form/
    path('create-query/', views.create_query, name='create_query'),
    # ex: /forecast/create-query/
]
