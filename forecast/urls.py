from django.urls import path

from . import views

app_name = 'forecast'
urlpatterns = [
    # ex: /forecast/
    path('', views.index, name='index'),
    # ex: /forecast/5/
    path('<int:team_id>/', views.detail, name='detail'),
    # ex: /forecast/5/results/
    path('<int:team_id>/results/', views.results, name='results'),
    # ex: /forecast/5/vote/
    path('<int:team_id>/vote/', views.vote, name='vote'),
]
