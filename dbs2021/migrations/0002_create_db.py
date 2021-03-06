# Generated by Django 3.1.6 on 2021-03-15 11:28

from django.db import connection
from django.db import migrations


def create_db(apps, schema_editor):
    create_db_query = """
    DROP TABLE IF EXISTS ov.companies;
    CREATE TABLE ov.companies (
        cin BIGINT NOT NULL,
        name VARCHAR,
        br_section VARCHAR,
        address_line VARCHAR,
        last_update TIMESTAMP,
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        PRIMARY KEY (cin)
    );"""

    with connection.cursor() as cursor:
        cursor.execute(create_db_query)


class Migration(migrations.Migration):

    dependencies = [
        ("dbs2021", "0001_initial"),
    ]

    operations = [migrations.RunPython(create_db)]
