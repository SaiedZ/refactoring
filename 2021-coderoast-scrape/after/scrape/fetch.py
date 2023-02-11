from fnmatch import fnmatch
from os import listdir, path

import pandas as pd
from tqdm import tqdm

from scrape.pdf import PDFScrape


def fetch_terms_from_pdf_files(paper_folder: str):
    search_terms = [
        path.join(paper_folder, file)
        for file in listdir(paper_folder)
        if fnmatch(path.basename(file), "*.pdf")
    ]
    scraper = PDFScrape()
    return pd.DataFrame([scraper.scrape(file) for file in tqdm(search_terms)])
