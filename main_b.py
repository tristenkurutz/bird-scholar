import json
import os.path
import time

import requests
from dotenv import load_dotenv


def is_relevant_paper(p):
    heterosexual_keywords = [
        "heterosexual", "heterosexuality",
        "opposite-sex", "opposite sex", "opposite‐sex",
        "female-male", "male-female",
        "female male", "male female",
        "mixed-sex", "mixed sex",
        "mating", "pair bond", "copulate",
        "courtship", "mounting", "pairing",
        "sexual partner", "sex partner",
        "reproductive behavior", "reproductive behaviour",
        "cross-sex", "cross sex",
        "intersex pairing", "mixed pairing",
        "breeding pair", "breeding behavior", "breeding behaviour",
        "mate choice", "mate selection",
        "nesting pair", "clutch", "fertilization"
    ]

    bird_keywords = [
        "bird", "birds", "avian", "aves",
        "songbird", "passerine", "ornithology",
        "finch", "sparrow", "warbler", "thrush",
        "starling", "crane", "parrot", "owl",
        "duck", "goose", "flamingo", "kestrel",
        "corvid", "jay", "wren", "swift",
        "macaw", "dove", "pigeon", "raptor",
        "seabird", "shorebird", "waterfowl",
        "budgerigar", "canary", "zebra finch",
        "quail", "chicken", "poultry"
    ]

    title = p.get("title", "").lower()
    abstract = (p.get("abstract") or "").lower()
    full_text = title + " " + abstract

    has_bird = any(kw in full_text for kw in bird_keywords)

    if not abstract:
        return has_bird and any(kw in title for kw in heterosexual_keywords)

    has_hetero_sex = any(kw in full_text for kw in heterosexual_keywords)
    return has_bird and has_hetero_sex


def create_map(group, api_key=None):
    m = {}
    for p in group:
        m[p["paperId"]] = p

    e = []

    redacted = []
    print("Getting citations per paper...")
    for i, p in enumerate(m.values()):
        refs = get_citations(p["paperId"], api_key)
        if not refs:
            redacted.append(p["paperId"])
            continue
        for ref in refs:
            ref_id = ref.get("citingPaper", {}).get("paperId")
            if ref_id and ref_id in m:
                e.append((p["paperId"], ref_id))
        time.sleep(1)

    save_results("redacted_papers_b", redacted)
    print("Saved redacted results to redacted_papers_b.json")
    print(f"Found {len(e)} edges between papers in dataset")
    return m, e


def get_citations(p_id, api_key=None):
    if api_key:
        headers = {"x-api-key": api_key}
    else:
        headers = {}

    for attempt in range(5):
        response = requests.get(
            f"https://api.semanticscholar.org/graph/v1/paper/{p_id}/citations",
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


def save_results(file_name, data):
    with open(f"{file_name}.json", "w") as f:
        json.dump(data, f)
    if os.path.getsize(f"{file_name}.json") > 0:
        print(f"Successfully saved results to {file_name}.json")
    else:
        print("File saving failed. Try again.")


if __name__ == '__main__':
    load_dotenv()

    # define search variables
    start_year = 2015
    max_entries = 100

    # get api key, if one is defined
    api_key = os.getenv("API_KEY")

    group_b = []
    queries = [
        "heterosexual mating behavior birds",
        "avian pair bond breeding",
        "bird reproductive behavior",
        "avian monogamy breeding pair",
    ]

    for query in queries:
        results = search_articles(query, start_year, max_entries, api_key)
        if results:
            print(f"'{query}' : {len(results)} results")
            group_b += results
            time.sleep(3)
        else:
            print(f"{query} returned null - you may be currently rate limited")
            break

    print(f"Found {len(group_b)} papers")

    if len(group_b) > 0:
        save_results("original_result", group_b)
        print("Saved original response")

        group_b = [p for p in group_b if is_relevant_paper(p)]

        # de-duplicate papers
        seen = set()
        group_b = [p for p in group_b if not (p["paperId"] in seen or seen.add(p["paperId"]))]

        print(f"{len(group_b)} papers after filtering")

        for paper in group_b:
            print(paper["title"], "-", paper.get("citationCount"))

        if len(group_b) > 0:
            save_results("group_b", group_b)

        group_map, edges = create_map(group_b, api_key)

        save_results("group_b_map", group_map)
        save_results("group_b_edges", edges)
    else:
        print("No papers found")
