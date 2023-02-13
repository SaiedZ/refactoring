import time

from scrape.fetch import fetch_terms_from_pdf_files
from scrape.export import export
from scrape.config import read_config
from scrape.log import log_msg


def main():

    # read the configuration settings from a JSON file
    config = read_config("./config.json")

    # fetch data from the PDF files and export it
    start = time.perf_counter()
    results = fetch_terms_from_pdf_files(config)
    export(results, config.export_dir)
    elapsed = time.perf_counter() - start
    log_msg(f"\n[sciscraper]: Extraction finished in {elapsed} seconds.\n")


if __name__ == "__main__":
    main()
