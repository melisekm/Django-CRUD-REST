import json
import math
import os
from pathlib import Path

import ciso8601
from django.db.models import Q, F
from django.http import JsonResponse

from dbs2021.models import OrPodanieIssues

BASE_DIR = Path(__file__).parent.absolute()

with open(os.path.join(BASE_DIR, "constants.json")) as constants_file:
    constants = json.load(constants_file)


def append_metadata(response, page, per_page, total):
    response["metadata"] = {
        "page": int(page),
        "per_page": int(per_page),
        "pages": math.ceil(total / int(per_page)),
        "total": total,
    }


def format_results(results):
    """vrati naformatovany JSON format z vystupu kurzora"""
    formatted_results = {"items": []}
    for result in results:
        item = {}
        for key, value in result.items():
            if key in constants["available_columns"]:
                item[key] = value
        formatted_results["items"].append(item)
    return formatted_results


def execute_query(params):
    query = OrPodanieIssues.objects.all()
    queryFilter = Q(corporate_body_name__icontains=params["query"]) | Q(city__icontains=params["query"])

    if params["query"]:
        try:
            int(params["query"])
            queryFilter = queryFilter | Q(cin__exact=params["query"])
        except ValueError:
            pass
        query = query.filter(queryFilter)

    if params["registration_date_gte"]:
        query = query.filter(registration_date__gte=params["registration_date_gte"])
    if params["registration_date_lte"]:
        query = query.filter(registration_date__lte=params["registration_date_lte"])

    if params["order_type"].casefold() == "asc":
        query = query.order_by(F(params["order_by"]).asc(nulls_last=True))
    else:
        query = query.order_by(F(params["order_by"]).desc(nulls_last=True))

    total = query.count()

    start = (int(params["page"]) - 1) * int(params["per_page"])
    stop = int(params["page"]) * int(params["per_page"])
    query = query[start:stop]

    return query.values(), total


def validate_params(params):
    """validuje zadane parametre od GET"""
    try:
        if int(params["page"]) <= 0:
            raise ValueError
    except ValueError:
        params["page"] = 1

    try:
        if int(params["per_page"]) <= 0:
            raise ValueError
    except ValueError:
        params["per_page"] = 10

    if params["registration_date_lte"]:
        try:
            # ak sa to da skonvertovat na iso format, inak error
            params["registration_date_lte"] = ciso8601.parse_datetime(params["registration_date_lte"])
        except ValueError:
            params["registration_date_lte"] = None

    if params["registration_date_gte"]:
        try:
            params["registration_date_gte"] = ciso8601.parse_datetime(params["registration_date_gte"])
        except ValueError:
            params["registration_date_gte"] = None

    # ak bol vyplneny(nie je None) a nie je to asc alebo desc
    if params["order_by"] is not None and (params["order_by"].casefold() not in constants["available_columns"]):
        params["order_by"] = "id"

    if (
        params["order_type"] is not None
        and params["order_type"].casefold() not in constants["order_type_available_values"]
    ):
        params["order_type"] = "desc"


def read_params(request):
    """z GET Requestu precita polia"""
    return {
        "page": request.GET.get("page", "1"),
        "per_page": request.GET.get("per_page", "10"),
        "query": request.GET.get("query", None),
        "registration_date_lte": request.GET.get("registration_date_lte", None),
        "registration_date_gte": request.GET.get("registration_date_gte", None),
        "order_by": request.GET.get("order_by", "id"),
        "order_type": request.GET.get("order_type", "desc"),
    }


def submissions_GET(request):
    params = read_params(request)
    validate_params(params)
    results, total = execute_query(params)
    response = format_results(results)
    append_metadata(response, params["page"], params["per_page"], total)

    return JsonResponse(response, status=200)


def format_response(podanie_issue):
    """naformatuje odpoved"""
    response = {"response": {"id": podanie_issue["id"]}}
    for key, value in podanie_issue.items():
        if key in constants["available_columns"]:
            response["response"][key] = value
    return response


def submissions_GET_by_id(idx):
    try:
        podanie_issue = OrPodanieIssues.objects.get(pk=idx)
        response = format_response(podanie_issue.__dict__)
        return JsonResponse(response, status=200)
    except OrPodanieIssues.DoesNotExist:
        return JsonResponse({"error": {"message": "Záznam neexistuje"}}, status=404)
