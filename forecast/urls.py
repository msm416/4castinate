from django.urls import path

from . import views

app_name = 'forecast'
urlpatterns = [
    path('', views.index, name='index'),
    # ex: /forecast/
    path('<int:query_id>/', views.detail, name='detail'),
    # ex: /forecast/5/
    path('<int:query_id>/<str:run_estimation_response>', views.detail, name='detail'),
    # ex: /forecast/5/message
    path('<int:query_id>/results/<int:estimation_id>/', views.results, name='results'),
    # ex: /forecast/5/results/2
    path('<int:query_id>/run-estimation/', views.run_estimation, name='run_estimation'),
    # ex: /forecast/5/create-form/
    path('create-query/', views.create_query, name='create_query'),
    # ex: /forecast/create-query/
    path('<int:query_id>/delete-estimation/<int:estimation_id>/', views.delete_estimation, name='delete_estimation'),
    # ex: /forecast/5/delete-estimation/2
    path('delete-query/<int:query_id>/', views.delete_query, name='delete_query')
    # ex: /forecast/delete-query/5
]
