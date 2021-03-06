# Generated by Django 3.1.6 on 2021-03-18 20:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("dbs2021", "0003_insert_into_companies"),
    ]

    operations = [
        migrations.RunSQL(
            """
            ALTER TABLE ov.likvidator_issues
            ADD COLUMN company_id BIGINT;

            ALTER TABLE ov.likvidator_issues
            ADD CONSTRAINT fk_company_id
            FOREIGN KEY (company_id)
            REFERENCES ov.companies(cin);

            ALTER TABLE ov.konkurz_vyrovnanie_issues
            ADD COLUMN company_id BIGINT;

            ALTER TABLE ov.konkurz_vyrovnanie_issues
            ADD CONSTRAINT fk_company_id
            FOREIGN KEY (company_id)
            REFERENCES ov.companies(cin);

            ALTER TABLE ov.znizenie_imania_issues
            ADD COLUMN company_id BIGINT;

            ALTER TABLE ov.znizenie_imania_issues
            ADD CONSTRAINT fk_company_id
            FOREIGN KEY (company_id)
            REFERENCES ov.companies(cin);

            ALTER TABLE ov.konkurz_restrukturalizacia_actors
            ADD company_id BIGINT;

            ALTER TABLE ov.konkurz_restrukturalizacia_actors
            ADD CONSTRAINT fk_company_id
            FOREIGN KEY (company_id)
            REFERENCES ov.companies(cin);

            ALTER TABLE ov.or_podanie_issues
            ADD COLUMN company_id BIGINT;

            ALTER TABLE ov.or_podanie_issues
            ADD CONSTRAINT fk_company_id
            FOREIGN KEY (company_id)
            REFERENCES ov.companies(cin);


            UPDATE ov.likvidator_issues
            SET company_id = cin;

            UPDATE ov.konkurz_vyrovnanie_issues
            SET company_id = cin;

            UPDATE ov.znizenie_imania_issues
            SET company_id = cin;

            UPDATE ov.konkurz_restrukturalizacia_actors
            SET company_id = cin;

            UPDATE ov.or_podanie_issues
            SET company_id = cin;
            """
        )
    ]
