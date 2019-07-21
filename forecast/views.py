from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, world. You're at the forecast index.")


def detail(request, team_id):
    return HttpResponse("You're looking at team %s." % team_id)


def results(request, team_id):
    response = "You're looking at the results of team %s."
    return HttpResponse(response % team_id)


def vote(request, team_id):
    return HttpResponse("You're forecasting on team %s." % team_id)