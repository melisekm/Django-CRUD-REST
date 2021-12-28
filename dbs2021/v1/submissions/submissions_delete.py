from django.db import connection
from django.http import JsonResponse
from django.http import HttpResponse


def submissions_DELETE(idx):
    main_query = (
        "DELETE FROM ov.or_podanie_issues " + "WHERE id = %s " + "RETURNING raw_issue_id, bulletin_issue_id;"
    )
    rid_query = (
        "DELETE FROM ov.raw_issues "
        + "WHERE id = %s AND NOT EXISTS("
        + "SELECT * FROM ov.or_podanie_issues WHERE raw_issue_id = %s);"
    )

    bid_query = (
        "DELETE FROM ov.bulletin_issues "
        + "WHERE id = %s AND NOT EXISTS("
        + "SELECT * FROM ov.or_podanie_issues WHERE bulletin_issue_id = %s);"
    )
    with connection.cursor() as cursor:
        cursor.execute(main_query, [idx])

        if cursor.rowcount == 0:
            return JsonResponse({"error": {"message": "Záznam neexistuje"}}, status=404)
        rid, bid = cursor.fetchone()
        cursor.execute(rid_query, [rid, rid])
        cursor.execute(bid_query, [bid, bid])

    return HttpResponse(status=204)
