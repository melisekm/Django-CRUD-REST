import json
import ciso8601
from django.utils import timezone
from django.http import JsonResponse
from django.http import HttpResponse
from django.db.models import Q, Max
from dbs2021.models import BulletinIssues, OrPodanieIssues, RawIssues


now = timezone.now()


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


def insert_into_podanie_issues(params):
    """zostavi, vlozi zaznam do ov.or_podanie_issues a vrati id"""
    podanie_issue = OrPodanieIssues(
        br_court_name=params["br_court_name"],
        kind_name=params["kind_name"],
        cin=params["cin"],
        registration_date=params["registration_date"],
        corporate_body_name=params["corporate_body_name"],
        br_section=params["br_section"],
        br_insertion=params["br_insertion"],
        text=params["text"],
        street=params["street"],
        postal_code=params["postal_code"],
        city=params["city"],
        created_at=now,
        updated_at=now,
        br_mark=params["br_mark"],
        br_court_code=params["br_court_code"],
        kind_code=params["kind_code"],
        address_line=params["address_line"],
        bulletin_issue=BulletinIssues.objects.get(pk=params["bulletin_issue_id"]),
        raw_issue=RawIssues.objects.get(pk=params["raw_issue_id"]),
    )
    podanie_issue.save()

    return podanie_issue.id


def insert_into_raw(bulletin_issue_id):
    """zostavi, vlozi zaznam do ov.raw_issues a vrati id"""
    raw_issue = RawIssues(
        bulletin_issue=BulletinIssues.objects.get(pk=bulletin_issue_id),
        file_name="-",
        content="-",
        created_at=now,
        updated_at=now,
    )
    raw_issue.save()
    return raw_issue.id


def insert_into_bulletin():
    """zostavi, vlozi zaznam do ov.raw_issues a vrati id"""
    number_query = BulletinIssues.objects.filter(Q(year__exact=now.year)).aggregate(number=Max("number"))
    number = number_query.get("number", 0) + 1

    bulletin_issue = BulletinIssues(
        year=now.year,
        number=number,
        published_at=now,
        created_at=now,
        updated_at=now,
    )
    bulletin_issue.save()
    return bulletin_issue.id


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
                if ciso8601.parse_datetime(date).year != now.year:
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

    params["registration_date"] = ciso8601.parse_datetime(params["registration_date"])

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
        "br_mark": "-",
        "br_court_code": "-",
        "kind_code": "-",
    }


def submissions_POST(request):
    global now
    now = timezone.now()  # cas pre created a updated columny
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
