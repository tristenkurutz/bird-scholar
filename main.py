import time

import requests


def is_bird_paper(paper):
    bird_keywords = [
        "avian", "songbird", "passerine", "raptor", "waterfowl",
        "finch", "sparrow", "warbler", "thrush", "starling",
        "crane", "macaw", "parrot", "owl", "duck", "goose",
        "shorebird", "seabird", "hummingbird", "pigeon", "dove",
        "corvid", "jay", "bunting", "oriole", "cisticola",

        "bird", "birds", "ornitholog", "aves", "poultry", "chicken",
        "zebra finch", "budgerigar", "canary"
    ]
    text = (paper.get("title", "") + " " + (paper.get("abstract") or "")).lower()
    has_bird = any(kw in text for kw in bird_keywords)

    return has_bird


def search_articles(query, start_year, max_entries):
    params = {
        "query": query,
        "fields": "title,referenceCount,citationCount,year,publicationTypes,fieldsOfStudy,authors,abstract",
        "year": f"{start_year}-",
        "fieldsOfStudy": "Biology",
        "limit": max_entries
    }
    for attempt in range(5):
        response = requests.get("https://api.semanticscholar.org/graph/v1/paper/search", params=params)

        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        elif response.status_code == 429:
            # exponential backoff
            wait = 2 ** attempt
            time.sleep(wait)
        else:
            print(f"Error {response.status_code}: {response.json()}")
            break
    print("Status code:", response.status_code)
    print("Raw response:", response.json())

    data = response.json()
    papers = data.get("data", [])
    return papers


if __name__ == '__main__':
    # define search variables
    start_year = 2020
    max_entries = 200

    group_a = search_articles("same-sex behavior songbird", start_year, max_entries)
    group_a = search_articles("same-sex behavior avian", start_year, max_entries)
    group_a += search_articles("homosexual behavior avian", start_year, max_entries)
    group_a += search_articles("homosexual behavior songbird", start_year, max_entries)

    print(f"Found {len(group_a)} papers")

    group_a = [p for p in group_a if is_bird_paper(p)]
    print(f"{len(group_a)} papers after filtering")

    for paper in group_a:
        print(paper["title"], "-", paper.get("citationCount"))
