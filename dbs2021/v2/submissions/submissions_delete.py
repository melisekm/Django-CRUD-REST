from django.http import JsonResponse
from django.http import HttpResponse
from dbs2021.models import OrPodanieIssues


def submissions_DELETE(idx):
    try:
        podanie_issue = OrPodanieIssues.objects.get(pk=idx)
    except OrPodanieIssues.DoesNotExist:
        return JsonResponse({"error": {"message": "Záznam neexistuje"}}, status=404)

    podanie_issue.delete()
    raw_issue = podanie_issue.raw_issue
    bulletin_issue = podanie_issue.bulletin_issue
    if not OrPodanieIssues.objects.filter(raw_issue=raw_issue).exists():
        raw_issue.delete()
    if not OrPodanieIssues.objects.filter(bulletin_issue=bulletin_issue).exists():
        bulletin_issue.delete()

    return HttpResponse(status=204)
