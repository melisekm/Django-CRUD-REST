import json
import os
import math
from pathlib import Path
import ciso8601
from django.db import connection
from django.http import JsonResponse


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


# prevzata funkcia https://docs.djangoproject.com/en/3.1/topics/db/sql/#executing-custom-sql-directly
def dict_fetch_all(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def format_results(results):
    """vrati naformatovany JSON format z vystupu kurzora"""
    formatted_results = {"items": []}
    for result in results:
        item = {}
        for key, value in result.items():
            item[key] = value
        formatted_results["items"].append(item)
    return formatted_results


def execute_query(params):
    """
    vykona poskladany SQL SELECT, obsahuje zakladny vyber stlpcov z tabulky
    prida WHERE ak:
        existuje query tak fulltext hladanie
        existuje filter na registraciu lt/gt urcity datum
    moznosti sa daju kombinovat\n
    zapise LIMIT a offset
    """
    base_sql_query = (
        "SELECT id, br_court_name, kind_name, cin, registration_date, corporate_body_name,"
        + "br_section, br_insertion, text, street,postal_code, city "
        + "FROM ov.or_podanie_issues "
    )
    sql_query = base_sql_query
    sql_params = []  # pre parametrizovany execute, postupne pridavam parametre zo vstupu

    where_query = ""  # skladanie where klauzuly
    reg_date_gte = ""  # pomocna pre pridanie "AND"

    if params["query"]:
        where_query += "(corporate_body_name ILIKE %s OR city ILIKE %s OR cin::text = %s )"  # ILIKE ignore case
        sql_params.extend(["%%" + params["query"] + "%%"] * 2)  # staci vyskyt tak to surroundneme
        sql_params.append(params["query"])

    if params["registration_date_gte"]:
        reg_date_gte = "AND " if where_query else ""
        reg_date_gte += "registration_date >= %s "
        where_query += reg_date_gte
        sql_params.append(params["registration_date_gte"])

    if params["registration_date_lte"]:
        reg_date_lte = "AND " if where_query or reg_date_gte else ""
        reg_date_lte += "registration_date <= %s "
        where_query += reg_date_lte
        sql_params.append(params["registration_date_lte"])

    if where_query:
        sql_query += "WHERE " + where_query

    order = f"ORDER BY {params['order_by']} {params['order_type']} "
    pagination = "LIMIT %s OFFSET %s;"

    row_query = "SELECT COUNT(*) FROM ov.or_podanie_issues "
    if where_query:
        row_query += "WHERE " + where_query

    with connection.cursor() as cursor:
        cursor.execute(row_query, sql_params)
        total = cursor.fetchone()[0]

        sql_query += order + pagination
        sql_params.append(params["per_page"])
        page_id = str((int(params["page"]) - 1) * int(params["per_page"]))  # index od 1, vynasobi inty
        sql_params.append(page_id)  # lebo je to offset, LIMIT 10 OFFSET 0

        cursor.execute(sql_query, sql_params)
        results = dict_fetch_all(cursor)
    return results, total


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
            ciso8601.parse_datetime(params["registration_date_lte"])
        except ValueError:
            params["registration_date_lte"] = None

    if params["registration_date_gte"]:
        try:
            ciso8601.parse_datetime(params["registration_date_gte"])
        except ValueError:
            params["registration_date_gte"] = None

    # ak bol vyplneny(nie je None) a nie je to asc alebo desc
    if (
        params["order_by"] is not None
        and params["order_by"].casefold() not in constants["order_by_available_values"]
    ):
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
