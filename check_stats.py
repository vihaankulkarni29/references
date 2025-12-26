import csv

with open('data/processed/master_leads.csv', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

print(f'Total leads: {len(rows)}')
print(f'With email: {sum(1 for r in rows if r.get("email") and r["email"] not in ["","N/A"])}')
print(f'With phone: {sum(1 for r in rows if r.get("phone") and r["phone"] not in ["","N/A"] and len(r["phone"]) > 5)}')
print(f'With instagram: {sum(1 for r in rows if r.get("instagram") and r["instagram"] not in ["","N/A"])}')

cities = {}
for r in rows:
    city = r.get('city')
    cities[city] = cities.get(city, 0) + 1

print('\nTop 10 cities:')
for city, count in sorted(cities.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f'  {city}: {count}')
