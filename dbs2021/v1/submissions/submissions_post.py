import json
import os
from pathlib import Path
import datetime
import ciso8601
from django.db import connection
from django.http import JsonResponse
from django.http import HttpResponse

now = datetime.datetime.utcnow().isoformat()  # cas pre created a updated columny

BASE_DIR = Path(__file__).parent.absolute()

with open(os.path.join(BASE_DIR, "constants.json")) as constants_file:
    constants = json.load(constants_file)


class ParamError:
    """
    ak je param nejaky nespravny udaj alebo je nevyplneny
    tato trieda wrapuje 1 element(atributa description), ktory vratime v json
    """

    def __init__(self, field, reasons):  # variable amount of reasons
        self.description = {"field": field, "reasons": reasons}


def format_response(params):
    """naformatuje odpovd ak sa podari pridanie"""
    response = {"response": {"id": params["podanie_issues_id"]}}
    for key, value in params.items():
        response["response"][key] = value
        if key == "city":
            break
    return response


def insert_into_table(insert_query, insert_params):
    """vseobecna funkcia na vlozenie do tabulky a vratenie id vlozeneho"""
    with connection.cursor() as cursor:
        cursor.execute(insert_query, insert_params)
        idx = cursor.fetchone()[0]
    return idx


def insert_into_podanie_issues(params):
    """zostavi, vlozi zaznam do ov.or_podanie_issues a vrati id"""
    insert_query = (
        "INSERT INTO ov.or_podanie_issues"
        + constants["insert_columns"]
        + "VALUES("
        + "%s, " * 18  # je to 19 stlpcov
        + "%s)"
        + "RETURNING id;"
    )
    insert_params = list(params.values())  # vsetky sa nachadazaju v params
    return insert_into_table(insert_query, insert_params)


def insert_into_raw(bulletin_issue_id):
    """zostavi, vlozi zaznam do ov.raw_issues a vrati id"""
    insert_query = (
        "INSERT INTO ov.raw_issues(bulletin_issue_id, file_name, content, created_at, updated_at)"
        + "VALUES (%s, '-', '-', %s, %s)"
        + "RETURNING id;"
    )
    insert_params = [bulletin_issue_id, now, now]
    return insert_into_table(insert_query, insert_params)


def insert_into_bulletin():
    """zostavi, vlozi zaznam do ov.raw_issues a vrati id"""
    select_query = "SELECT MAX(number) + 1" + "FROM ov.bulletin_issues WHERE year = EXTRACT(YEAR from now());"
    with connection.cursor() as cursor:
        cursor.execute(select_query)
        number = cursor.fetchone()[0]

    insert_query = (
        "INSERT INTO ov.bulletin_issues(year, number, published_at, created_at, updated_at)"
        + "VALUES(EXTRACT(YEAR from now()), %s, %s, %s, %s)"
        + "RETURNING id;"
    )
    insert_params = [number, now, now, now]
    return insert_into_table(insert_query, insert_params)


def execute_query(params):
    """vykona vsetky inserty do tabuliek v db a vrati id"""
    params["bulletin_issue_id"] = insert_into_bulletin()
    params["raw_issue_id"] = insert_into_raw(params["bulletin_issue_id"])
    params["podanie_issues_id"] = insert_into_podanie_issues(params)


def validate_post_params(params):
    """validuje zadane parametre od POST"""
    errors = {"errors": []}  # ak by boli zdetekovane errory vratime tento objekt

    def check_post_parameter(key, value, p_type, wrong_type_msg):
        reasons = []
        if value is None:
            reasons.append("required")
        elif not isinstance(value, p_type):
            reasons.append(wrong_type_msg)
        if reasons:
            err = ParamError(key, reasons)
            errors["errors"].append(err.description)

    def check_reg_date(date):
        reasons = []
        if not date:
            reasons.append("required")
        else:
            try:
                if ciso8601.parse_datetime(date).year != datetime.datetime.utcnow().year:
                    raise ValueError
            except (ValueError, TypeError):
                reasons.append("invalid_range")
        if reasons:
            err = ParamError("registration_date", reasons)
            errors["errors"].append(err.description)

    for key, value in params.items():
        if key not in ("cin", "registration_date"):
            check_post_parameter(key, value, str, "required")
    check_post_parameter("cin", params["cin"], int, "not_number")
    check_reg_date(params["registration_date"])
    if errors["errors"]:
        return errors

    params["address_line"] = f"{params['street']}, {params['postal_code']} {params['city']}"
    return "validated"


def read_post_params(request):
    """z POST Requestu precita polia"""
    body = json.loads(request.body.decode("utf-8"))
    return {
        "br_court_name": body.get("br_court_name", None),
        "kind_name": body.get("kind_name", None),
        "cin": body.get("cin", None),
        "registration_date": body.get("registration_date", None),
        "corporate_body_name": body.get("corporate_body_name", None),
        "br_section": body.get("br_section", None),
        "br_insertion": body.get("br_insertion", None),
        "text": body.get("text", None),
        "street": body.get("street", None),
        "postal_code": body.get("postal_code", None),
        "city": body.get("city", None),
        "created_at": now,
        "updated_at": now,
        "br_mark": "-",
        "br_court_code": "-",
        "kind_code": "-",
    }


def submissions_POST(request):
    global now
    now = datetime.datetime.utcnow().isoformat()  # cas pre created a updated columny
    try:
        params = read_post_params(request)
    except json.JSONDecodeError:
        return HttpResponse(status=400)
    validate_result = validate_post_params(params)
    if validate_result != "validated":
        return JsonResponse(validate_result, status=422)
    execute_query(params)
    response = format_response(params)
    return JsonResponse(response, status=201)
