"""Fetch the French and Arabic labels and aliases of Algeria's communes from Wikidata (CC0),
which the scanned texts are checked against: an OCR reading that is one of them counts as
a second reading. Nothing from Wikidata goes into the data.

    python3 tools/gazette/wikidata.py > work/wikidata-labels.json

Standard library only.
"""
import sys
import urllib.parse
import urllib.request

QUERY = '''SELECT ?item ?lang ?label ?kind WHERE {
  ?item wdt:P31 wd:Q2989398 .
  { ?item rdfs:label ?label . BIND("label" AS ?kind) }
  UNION { ?item skos:altLabel ?label . BIND("alias" AS ?kind) }
  BIND(LANG(?label) AS ?lang)
  FILTER(?lang IN ("fr", "ar"))
}'''


def main():
    request = urllib.request.Request(
        'https://query.wikidata.org/sparql?' + urllib.parse.urlencode({'query': QUERY}),
        headers={'Accept': 'application/sparql-results+json',
                 'User-Agent': 'wilayas-transcription/0.1 (https://github.com/djazairdev/wilayas)'})
    with urllib.request.urlopen(request, timeout=120) as response:
        sys.stdout.buffer.write(response.read())


if __name__ == '__main__':
    main()
