import json

import ciso8601
from django.http import HttpResponse
from django.http import JsonResponse
from django.utils import timezone

from dbs2021.models import OrPodanieIssues
from .submissions_get import format_response


class ParamError:
    """
    ak je param nejaky nespravny udaj alebo je nevyplneny
    tato trieda wrapuje 1 element(atributa description), ktory vratime v json
    """

    def __init__(self, field, reasons):  # variable amount of reasons
        self.description = {"field": field, "reasons": reasons}


def execute_query(params, podanie_issue):
    updated_fields = []
    for key, value in params.items():
        if value is not None:
            setattr(podanie_issue, key, value)
            updated_fields.append(key)
    podanie_issue.save(update_fields=updated_fields)


def params_contain_atleast_one_column(params):
    for value in params.values():
        if value is not None:
            return True
    return False


def validate_put_params(params):
    """validuje zadane parametre od PUT"""
    errors = {"errors": []}  # ak by boli zdetekovane errory vratime tento objekt

    def check_put_parameter(key, value, p_type, wrong_type_msg):
        reasons = []
        if value:
            if not isinstance(value, p_type):
                reasons.append(wrong_type_msg)
        if reasons:
            err = ParamError(key, reasons)
            errors["errors"].append(err.description)

    def check_reg_date(date):
        reasons = []
        if date:
            try:
                if ciso8601.parse_datetime(date).year != timezone.now().year:
                    raise ValueError
            except (ValueError, TypeError):
                reasons.append("invalid_range")
        if reasons:
            err = ParamError("registration_date", reasons)
            errors["errors"].append(err.description)

    for key, value in params.items():
        if key not in ("cin", "registration_date"):
            check_put_parameter(key, value, str, "not_string")
    check_put_parameter("cin", params["cin"], int, "not_number")
    check_reg_date(params["registration_date"])
    if errors["errors"]:
        return errors

    if params["registration_date"]:
        params["registration_date"] = ciso8601.parse_datetime(params["registration_date"])

    return "validated"


def read_put_params(request):
    """z PUT Requestu precita polia"""
    body = json.loads(request.body.decode("utf-8"))
    if not body:
        raise ValueError
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
    }


def submissions_PUT(request, idx):
    try:
        podanie_issue = OrPodanieIssues.objects.get(pk=idx)
    except OrPodanieIssues.DoesNotExist:
        return JsonResponse({"error": {"message": "Záznam neexistuje"}}, status=404)
    try:
        params = read_put_params(request)
    except json.JSONDecodeError:
        return HttpResponse(status=400)
    except ValueError:
        return HttpResponse(status=422)
    if not params_contain_atleast_one_column(params):
        return HttpResponse(status=422)

    validate_result = validate_put_params(params)
    if validate_result != "validated":
        return JsonResponse(validate_result, status=422)
    execute_query(params, podanie_issue)

    response = format_response(podanie_issue.__dict__)
    return JsonResponse(response, status=201)
