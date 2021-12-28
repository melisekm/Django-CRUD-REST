import json
import os
import math
from pathlib import Path
import ciso8601
from django.http import JsonResponse
from django.db.models import Q, F, Count, Subquery, OuterRef
from dbs2021.models import (
    Companies,
    OrPodanieIssues,
    ZnizenieImaniaIssues,
    LikvidatorIssues,
    KonkurzVyrovnanieIssues,
    KonkurzRestrukturalizaciaActors,
)


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
            if key in constants["companies_order_by_available_values"]:
                if value is None and key not in ("br_section", "address_line"):
                    value = 0
                item[key] = value
        formatted_results["items"].append(item)
    return formatted_results


def execute_query(params):
    query = Companies.objects.annotate(
        or_podanie_issues_count=Subquery(
            OrPodanieIssues.objects.filter(company_id=OuterRef("cin"))
            .values("company_id")
            .annotate(count=Count("*"))
            .values("count")
        ),
        znizenie_imania_issues_count=Subquery(
            ZnizenieImaniaIssues.objects.filter(company_id=OuterRef("cin"))
            .values("company_id")
            .annotate(count=Count("*"))
            .values("count")
        ),
        likvidator_issues_count=Subquery(
            LikvidatorIssues.objects.filter(company_id=OuterRef("cin"))
            .values("company_id")
            .annotate(count=Count("*"))
            .values("count")
        ),
        konkurz_vyrovnanie_issues_count=Subquery(
            KonkurzVyrovnanieIssues.objects.filter(company_id=OuterRef("cin"))
            .values("company_id")
            .annotate(count=Count("*"))
            .values("count")
        ),
        konkurz_restrukturalizacia_actors_count=Subquery(
            KonkurzRestrukturalizaciaActors.objects.filter(company_id=OuterRef("cin"))
            .values("company_id")
            .annotate(count=Count("*"))
            .values("count")
        ),
    )

    if params["query"]:
        query = query.filter(Q(name__icontains=params["query"]) | Q(address_line__icontains=params["query"]))

    if params["last_update_gte"]:
        query = query.filter(last_update__gte=params["last_update_gte"])
    if params["last_update_lte"]:
        query = query.filter(last_update__lte=params["last_update_lte"])

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

    if params["last_update_lte"]:
        try:
            # ak sa to da skonvertovat na iso format, inak error
            params["last_update_lte"] = ciso8601.parse_datetime(params["last_update_lte"])
        except ValueError:
            params["last_update_lte"] = None

    if params["last_update_gte"]:
        try:
            params["last_update_gte"] = ciso8601.parse_datetime(params["last_update_gte"])
        except ValueError:
            params["last_update_gte"] = None

    # ak bol vyplneny(nie je None) a nie je to asc alebo desc
    if (
        params["order_by"] is not None
        and params["order_by"].casefold() not in constants["companies_order_by_available_values"]
    ):
        params["order_by"] = "cin"

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
        "last_update_lte": request.GET.get("last_update_lte", None),
        "last_update_gte": request.GET.get("last_update_gte", None),
        "order_by": request.GET.get("order_by", "id"),
        "order_type": request.GET.get("order_type", "desc"),
    }


def companies_GET(request):
    params = read_params(request)
    validate_params(params)
    results, total = execute_query(params)
    response = format_results(results)
    append_metadata(response, params["page"], params["per_page"], total)

    return JsonResponse(response, status=200)
