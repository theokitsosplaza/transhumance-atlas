import json
from rdflib import Graph

graph = Graph()
graph.parse("pastures.ttl", format="turtle")


def last_part(uri):
    return str(uri).split("/")[-1]


def labels_of_concepts(scheme_name):
    query = """
    PREFIX ex: <https://example.org/atlas/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    SELECT ?concept ?label WHERE {
      ?concept skos:inScheme ex:""" + scheme_name + """ ;
               skos:prefLabel ?label .
    }
    """
    labels_by_concept = {}
    for result_row in graph.query(query):
        labels_by_concept.setdefault(last_part(result_row.concept), {})[result_row.label.language] = str(result_row.label)
    return labels_by_concept


season_labels = labels_of_concepts("seasons")
type_labels = labels_of_concepts("pastureTypes")

season_order_query = """
PREFIX ex: <https://example.org/atlas/>
SELECT ?season ?order WHERE { ?season ex:order ?order . }
"""
season_order = {last_part(row.season): int(row.order) for row in graph.query(season_order_query)}

pastures_query = """
PREFIX ex: <https://example.org/atlas/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
SELECT ?pasture ?type ?season ?label ?region ?wkt ?until WHERE {
  ?pasture a ex:Pasture ;
           ex:pastureType ?type ;
           ex:usedIn ?season ;
           rdfs:label ?label ;
           ex:locatedIn ?region ;
           geo:hasGeometry/geo:asWKT ?wkt .
  OPTIONAL { ?pasture ex:inUseUntil ?until . }
}
ORDER BY ?pasture
"""

pastures_by_id = {}
for result_row in graph.query(pastures_query):
    pasture_id = last_part(result_row.pasture)
    if pasture_id not in pastures_by_id:
        # WKT is "POINT(longitude latitude)", Leaflet wants latitude first
        longitude_text, latitude_text = str(result_row.wkt).replace("POINT(", "").replace(")", "").split()
        pastures_by_id[pasture_id] = {
            "id": pasture_id,
            "type": last_part(result_row.type),
            "seasons": [],
            "region": last_part(result_row.region),
            "lat": float(latitude_text),
            "lon": float(longitude_text),
            "in_use_until": int(result_row.until) if result_row.until is not None else None,
            "labels": {},
        }
    pasture = pastures_by_id[pasture_id]
    pasture["labels"][result_row.label.language] = str(result_row.label)
    if last_part(result_row.season) not in pasture["seasons"]:
        pasture["seasons"].append(last_part(result_row.season))

for pasture in pastures_by_id.values():
    pasture["seasons"].sort(key=lambda season_id: season_order[season_id])

interviews_query = """
PREFIX ex: <https://example.org/atlas/>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT ?interview ?date ?language ?pasture WHERE {
  ?interview a ex:Interview ;
             dcterms:date ?date ;
             dcterms:language ?language ;
             ex:mentions ?pasture .
}
ORDER BY ?interview ?pasture
"""
interviews_by_id = {}
for result_row in graph.query(interviews_query):
    interview_id = "interview " + last_part(result_row.interview)
    if interview_id not in interviews_by_id:
        interviews_by_id[interview_id] = {
            "id": interview_id,
            "date": str(result_row.date),
            "language": str(result_row.language),
            "mentions": [],
        }
    interviews_by_id[interview_id]["mentions"].append(last_part(result_row.pasture))

moves_query = """
PREFIX ex: <https://example.org/atlas/>
SELECT ?region ?year ?timing WHERE {
  ?move a ex:SeasonalMove ;
        ex:region ?region ;
        ex:year ?year ;
        ex:timing ?timing .
}
"""
summer_move_timing = {}
for result_row in graph.query(moves_query):
    summer_move_timing.setdefault(last_part(result_row.region), {})[int(result_row.year)] = str(result_row.timing)

# the graph only stores the Wikidata IDs of the regions, so their labels and map extent are added here
regions = [
    {"id": "Q2712698", "labels": {"en": "Fındıklı district", "tr": "Fındıklı ilçesi"},
     "bounds": [[40.85, 40.95], [41.35, 41.45]]},
    {"id": "Q486375", "labels": {"en": "Naryn Region", "ky": "Нарын облусу"},
     "bounds": [[41.05, 75.4], [41.55, 76.15]]},
]

atlas_data = {
    "pastures": list(pastures_by_id.values()),
    "interviews": list(interviews_by_id.values()),
    "regions": regions,
    "season_labels": season_labels,
    "season_order": season_order,
    "type_labels": type_labels,
    "summer_move_timing": summer_move_timing,
}

page = open("atlas_template.html", encoding="utf-8").read()
page = page.replace("/*ATLAS_DATA*/", json.dumps(atlas_data, ensure_ascii=False, indent=1))
open("index.html", "w", encoding="utf-8").write(page)
