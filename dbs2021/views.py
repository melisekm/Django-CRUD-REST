from django.db import connection
from django.http import JsonResponse
from django.http import HttpResponse
from .v1.submissions.submissions_get import submissions_GET as v1_sub_get
from .v1.submissions.submissions_post import submissions_POST as v1_sub_post
from .v1.submissions.submissions_delete import submissions_DELETE as v1_sub_del
from .v1.companies.companies_get import companies_GET as v1_comp_get


from .v2.submissions.submissions_get import submissions_GET as v2_sub_get
from .v2.submissions.submissions_get import submissions_GET_by_id as v2_sub_get_by_id
from .v2.submissions.submissions_post import submissions_POST as v2_sub_post
from .v2.submissions.submissions_delete import submissions_DELETE as v2_sub_del
from .v2.submissions.submissions_put import submissions_PUT as v2_sub_put

from .v2.companies.companies_get import companies_GET as v2_comp_get


def health(request):
    del request
    with connection.cursor() as cursor:
        cursor.execute("SELECT date_trunc('second', current_timestamp - pg_postmaster_start_time()) as uptime;")
        time = str(cursor.fetchone()[0])

    response = {
        "pgsql": {
            "uptime": time.replace(",", ""),
        }
    }
    return JsonResponse(response)


# V1
def v1submissions(request):
    if request.method == "GET":
        return v1_sub_get(request)
    if request.method == "POST":
        return v1_sub_post(request)

    return HttpResponse(status=404)


def v1submissions_delete(request, idx):
    if request.method == "DELETE":
        return v1_sub_del(idx)
    return HttpResponse(status=404)


def v1companies(request):
    if request.method == "GET":
        return v1_comp_get(request)
    return HttpResponse(status=404)


# V2
def v2submissions(request):
    if request.method == "GET":
        return v2_sub_get(request)
    if request.method == "POST":
        return v2_sub_post(request)

    return HttpResponse(status=404)


def v2submissions_id(request, idx):
    if request.method == "DELETE":
        return v2_sub_del(idx)
    if request.method == "PUT":
        return v2_sub_put(request, idx)
    if request.method == "GET":
        return v2_sub_get_by_id(idx)
    return HttpResponse(status=404)


def v2companies(request):
    if request.method == "GET":
        return v2_comp_get(request)
    return HttpResponse(status=404)
