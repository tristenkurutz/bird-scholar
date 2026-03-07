import time

import requests


def is_bird_paper(p):
    bird_keywords = [
        "avian", "songbird", "passerine", "raptor", "waterfowl",
        "finch", "sparrow", "warbler", "thrush", "starling",
        "crane", "macaw", "parrot", "owl", "duck", "goose",
        "shorebird", "seabird", "hummingbird", "pigeon", "dove",
        "corvid", "jay", "bunting", "oriole", "cisticola",

        "bird", "birds", "ornitholog", "aves", "poultry", "chicken",
        "zebra finch", "budgerigar", "canary"
    ]
    text = (p.get("title", "") + " " + (p.get("abstract") or "")).lower()
    has_bird = any(kw in text for kw in bird_keywords)

    return has_bird


def create_map(group):
    group_map = {}
    for p in group:
        group_map[p["paperId"]] = p

    edges = []

    for paper in group_map.values():
        refs = get_references(paper["paperId"])
        for ref in refs:
            ref_id = ref.get("paperId")
            if ref_id and ref_id in group_map:
                edges.append((paper["paperId"], ref_id))

    print(f"Found {len(edges)} edges between papers in dataset")


def get_references(p_id):
    for attempt in range(5):
        response = requests.get(
            f"https://api.semanticscholar.org/graph/v1/paper/{p_id}/references",
            params={"fields": "paperId,title"},
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        elif response.status_code == 429:
            wait = 2 ** attempt
            time.sleep(wait)
        else:
            print(f"Error {response.status_code} for paper {p_id}")
            return []
    return []


def search_articles(query, s_year, m_entries):
    params = {
        "query": query,
        "fields": "title,referenceCount,citationCount,year,publicationTypes,fieldsOfStudy,authors,abstract",
        "year": f"{s_year}-",
        "fieldsOfStudy": "Biology",
        "limit": m_entries
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
