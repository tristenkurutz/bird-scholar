import json
import os.path
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

    for p in group_map.values():
        refs = get_references(p["paperId"])
        for ref in refs:
            ref_id = ref.get("paperId")
            if ref_id and ref_id in group_map:
                edges.append((p["paperId"], ref_id))

    print(f"Found {len(edges)} edges between papers in dataset")


def get_references(p_id, api_key=None):
    if api_key:
        headers = {"x-api-key": api_key}
    else:
        headers = {}

    for attempt in range(5):
        response = requests.get(
            f"https://api.semanticscholar.org/graph/v1/paper/{p_id}/references",
            params={"fields": "paperId,title"}, headers=headers
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


def search_articles(q, s_year, m_entries, api_key=None):
    if api_key:
        headers = {"x-api-key": api_key}
    else:
        headers = {}

    params = {
        "query": q,
        "fields": "title,referenceCount,citationCount,year,publicationTypes,fieldsOfStudy,authors,abstract",
        "year": f"{s_year}-",
        "fieldsOfStudy": "Biology",
        "limit": m_entries
    }
    for attempt in range(5):
        response = requests.get("https://api.semanticscholar.org/graph/v1/paper/search", params=params, headers=headers)

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


def save_results(file_name):
    with open(f"{file_name}.json", "w") as f:
        json.dump(group_a, f)
    if os.path.getsize(f"{file_name}.json") > 0:
        print(f"Successfully saved results to {file_name}.json")
    else:
        print("File saving failed. Try again.")


if __name__ == '__main__':
    # define search variables
    start_year = 2020
    max_entries = 200

    group_a = []
    queries = [
        "same-sex behavior songbird",
        "same-sex behavior avian",
        "homosexual behavior avian",
        "homosexual behavior songbird"
    ]

    for query in queries:
        results = search_articles(query, start_year, max_entries)
        print(f"'{query}' : {len(results)} results")
        group_a += results
        time.sleep(3)

    print(f"Found {len(group_a)} papers")

    group_a = [p for p in group_a if is_bird_paper(p)]

    # de-duplicate papers
    seen = set()
    group_a = [p for p in group_a if not (p["paperId"] in seen or seen.add(p["paperId"]))]

    print(f"{len(group_a)} papers after filtering")

    for paper in group_a:
        print(paper["title"], "-", paper.get("citationCount"))

    if len(group_a) > 0:
        save_results("group_a")
