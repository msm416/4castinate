from django.urls import path

from . import views

app_name = 'forecast'
urlpatterns = [
    path('', views.index, name='index'),
    # ex: /forecast/
    path('<int:team_id>/', views.detail, name='detail'),
    # ex: /forecast/5/
    path('<int:team_id>/results/<int:forecastinput_id>/', views.results, name='results'),
    # ex: /forecast/5/results/2
    path('<int:team_id>/estimate/', views.estimate, name='estimate')
    # ex: /forecast/5/estimate/
]
