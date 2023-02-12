from fnmatch import fnmatch
from os import listdir, path

import pandas as pd
from tqdm import tqdm

from scrape.pdf import PDFScrape
from scrape. scraper import Scraper


def fetch_terms_from_pdf_files(paper_folder: str):
    search_terms = [
        path.join(paper_folder, file)
        for file in listdir(paper_folder)
        if fnmatch(path.basename(file), "*.pdf")
    ]
    scraper = PDFScrape()
    return pd.DataFrame([scraper.scrape(file) for file in tqdm(search_terms)])


def fetch_terms_from_doi(target: str, scraper: Scraper):
    print(f"\n[sciscraper]: Getting entries from file: {target}")
    with open(target, newline="") as f:
        df = [doi for doi in pd.read_csv(f, usecols=["DOI"])["DOI"]]
        search_terms = [
            search_text for search_text in df if search_text is not None
        ]
        return pd.DataFrame(
            [
                scraper.scrape(search_text)
                for search_text in tqdm(search_terms)
            ]
        )


def fetch_terms_from_pubid(target: pd.DataFrame, scraper: Scraper):
    df = target.explode("cited_dimensions_ids", "title")
    search_terms = [
        search_text
        for search_text in df["cited_dimensions_ids"]
        if search_text is not None
    ]
    src_title = pd.Series(df["title"])

    return pd.DataFrame(
        [
            scraper.scrape(search_text)
            for search_text in tqdm(search_terms)
        ]
    ).join(src_title)
