from django.urls import path

from . import views

urlpatterns = [
    path("v1/health/", views.health, name="health"),
    # V1
    path("v1/ov/submissions", views.v1submissions, name="v1submissions"),
    path("v1/ov/submissions/", views.v1submissions, name="v1submissions"),
    path("v1/ov/submissions/<int:idx>", views.v1submissions_delete, name="v1submissions_delete"),
    path("v1/companies", views.v1companies, name="v1companies"),
    path("v1/companies/", views.v1companies, name="v1companies"),
    # V2
    path("v2/ov/submissions", views.v2submissions, name="v2submissions"),
    path("v2/ov/submissions/", views.v2submissions, name="v2submissions"),
    path("v2/ov/submissions/<int:idx>", views.v2submissions_id, name="v2submissions_id"),
    path("v2/companies", views.v2companies, name="v2companies"),
    path("v2/companies/", views.v2companies, name="v2companies"),
]
