# Fáza 5
+ Object–relational mapping (ORM) pre fázu 2 a 3
+ Pridanie PUT Endpoint -> modifikácia záznamu
+ Rozšírenie o získanie konkrétného záznamu podľa id

# Fáza 3
+ Vytvorenie normalizovanej tabuľky companies -> dbs2021/migrations/
+ create db, insert rows, add foreign keys, create view
+ Vytvorenie View, ktorý obsahuje počty záznamov z pôvodných tabuliek
+ Pridanie cudzích kľúčov
+ dbs2021/view_ov/companies*.py
+ GET API -> rovnaké ako vo fáze 2
    + page, per_page
    + query (name, address_line)
    + last_update_lte, last_update_gte
    + order_by, order_type   

# Fáza 2
+ dbs2021/view_ov/submissions*.py
+ REST API
    + GET -> vráti údaje z DB na základe parametrov
        + page, per_page
        + query (corporate_body_name, city, cin)
        + registration_date_lte, registration_date_gte
        + order_by, order_type
    + POST -> pridá záznam do DB
    + DELETE -> zmaže záznam z DB
# Fáza 1
+ vrati JSON vo formate 
```{"pgsql": {"uptime": "1 day 10:31:17"}}```
+ pristup k datam napr. cez python 
```python
import requests
response = requests.get("https://fiit-dbs-xmelisek-app.azurewebsites.net/v1/health")
data = response.json()
uptime = data["pgsql"]["uptime"]
```
