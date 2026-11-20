# Transhumance atlas prototype

A small interactive map of seasonal pastures and herding routes in Fındıklı (Türkiye) and Naryn (Kyrgyzstan).

Live page: https://theokitsosplaza.github.io/transhumance-atlas/

All pastures, positions, interviews and timings are invented demo data. Nothing here is a research finding. The Wikidata IDs of the two regions and the background map are real.

## What it shows

- Winter, spring and summer pastures with the yearly route between them
- One ID per place, with names in Turkish, Kyrgyz and English
- Pasture types and seasons from a small shared vocabulary (SKOS)
- Interviews linked to the places they mention, shown by description only
- Search that matches Turkish letters without accents and Cyrillic typed in Latin letters
- Regions linked to Wikidata, and the data downloadable as Turtle

## Files

- `pastures.csv`: the input table
- `build_graph.py`: turns the table into an RDF graph, `pastures.ttl`
- `build_atlas.py`: queries the graph with SPARQL and writes `index.html`
- `atlas_template.html`: the page layout and map code (Leaflet)

## Rebuild

    pip install rdflib
    python build_graph.py
    python build_atlas.py
