import csv
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF, RDFS, DCTERMS, XSD, SKOS

EX = Namespace("https://example.org/atlas/")
WD = Namespace("http://www.wikidata.org/entity/")
GEO = Namespace("http://www.opengis.net/ont/geosparql#")

graph = Graph()
graph.bind("ex", EX)
graph.bind("wd", WD)
graph.bind("geo", GEO)
graph.bind("dcterms", DCTERMS)
graph.bind("skos", SKOS)

# shared vocabularies: one concept per season and per pasture type, with the local words attached
seasons = [
    ("winter", 1, {"en": "Winter", "tr": "Kış", "ky": "Кыш"}),
    ("spring", 2, {"en": "Spring", "tr": "İlkbahar", "ky": "Жаз"}),
    ("summer", 3, {"en": "Summer", "tr": "Yaz", "ky": "Жай"}),
]
for season_id, season_order, season_labels in seasons:
    season = EX["season/" + season_id]
    graph.add((season, RDF.type, SKOS.Concept))
    graph.add((season, SKOS.inScheme, EX.seasons))
    graph.add((season, EX.order, Literal(season_order)))
    for language, label in season_labels.items():
        graph.add((season, SKOS.prefLabel, Literal(label, lang=language)))

pasture_types = [
    ("winter-quarters", {"en": "Winter quarters", "tr": "kışlak", "ky": "кыштоо"}),
    ("spring-pasture", {"en": "Spring pasture", "ky": "жаздоо"}),
    ("summer-pasture", {"en": "Summer pasture", "tr": "yayla", "ky": "жайлоо"}),
]
for type_id, type_labels in pasture_types:
    pasture_type = EX["type/" + type_id]
    graph.add((pasture_type, RDF.type, SKOS.Concept))
    graph.add((pasture_type, SKOS.inScheme, EX.pastureTypes))
    for language, label in type_labels.items():
        graph.add((pasture_type, SKOS.prefLabel, Literal(label, lang=language)))

with open("pastures.csv", encoding="utf-8") as csv_file:
    for row in csv.DictReader(csv_file):
        pasture = EX["pasture/" + row["pasture_id"]]
        geometry = EX["geometry/" + row["pasture_id"]]
        graph.add((pasture, RDF.type, EX.Pasture))
        graph.add((pasture, EX.pastureType, EX["type/" + row["pasture_type"]]))
        for season_id in row["seasons_used"].split("|"):
            graph.add((pasture, EX.usedIn, EX["season/" + season_id]))
        if row["in_use_until"]:
            graph.add((pasture, EX.inUseUntil, Literal(int(row["in_use_until"]))))
        graph.add((pasture, RDFS.label, Literal(row["name_en"], lang="en")))
        graph.add((pasture, RDFS.label, Literal(row["name_local"], lang=row["local_language"])))
        graph.add((pasture, EX.locatedIn, WD[row["region_wikidata_id"]]))
        # WKT puts longitude first, which is the opposite of how people usually write coordinates
        wkt_point = "POINT(" + row["longitude"] + " " + row["latitude"] + ")"
        graph.add((pasture, GEO.hasGeometry, geometry))
        graph.add((geometry, GEO.asWKT, Literal(wkt_point, datatype=GEO.wktLiteral)))

interviews = [
    ("007", "2027-07-14", "tr", ["tr-01", "tr-03"]),
    ("012", "2027-08-03", "ky", ["kg-01", "kg-02"]),
]
for interview_number, interview_date, interview_language, mentioned_pastures in interviews:
    interview = EX["interview/" + interview_number]
    graph.add((interview, RDF.type, EX.Interview))
    graph.add((interview, DCTERMS.date, Literal(interview_date, datatype=XSD.date)))
    graph.add((interview, DCTERMS.language, Literal(interview_language)))
    for pasture_id in mentioned_pastures:
        graph.add((interview, EX.mentions, EX["pasture/" + pasture_id]))

# made-up timings for the move up to the summer pastures, only to show how change over time could be stored
summer_moves = [
    ("Q2712698", 1985, "early June"), ("Q2712698", 2005, "late May"), ("Q2712698", 2025, "mid May"),
    ("Q486375", 1985, "mid June"), ("Q486375", 2005, "early June"), ("Q486375", 2025, "late May"),
]
for region_id, year, timing in summer_moves:
    move = EX["move/" + region_id + "-" + str(year)]
    graph.add((move, RDF.type, EX.SeasonalMove))
    graph.add((move, EX.region, WD[region_id]))
    graph.add((move, EX.toSeason, EX["season/summer"]))
    graph.add((move, EX.year, Literal(year)))
    graph.add((move, EX.timing, Literal(timing, lang="en")))

graph.serialize("pastures.ttl", format="turtle")

summer_pastures_query = """
PREFIX ex: <https://example.org/atlas/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?pasture ?label ?region WHERE {
  ?pasture ex:usedIn <https://example.org/atlas/season/summer> ;
           rdfs:label ?label ;
           ex:locatedIn ?region .
  FILTER(lang(?label) = "en")
}
"""
for result_row in graph.query(summer_pastures_query):
    print(result_row.pasture, result_row.label, result_row.region)

mentioned_query = """
PREFIX ex: <https://example.org/atlas/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?interview ?localName WHERE {
  ?interview ex:mentions ?pasture .
  ?pasture rdfs:label ?localName .
  FILTER(lang(?localName) = "tr")
}
"""
for result_row in graph.query(mentioned_query):
    print(result_row.interview, result_row.localName)
