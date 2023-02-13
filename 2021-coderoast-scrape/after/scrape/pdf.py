import re
from os import path

import pdfplumber
from nltk import FreqDist
from nltk.corpus import names, stopwords
from nltk.tokenize import word_tokenize
from scrape.scraper import ScrapeResult


def guess_doi(path_name: str) -> str:
    """Approximates a possible DOI, assuming the file is saved in YYMMDD_DOI.pdf format."""
    basename = path.basename(path_name)
    doi = basename[7:-4]
    return f"{doi[:7]}/{doi[7:]}"


def compute_filtered_tokens(text: list[str]) -> set[str]:
    """Takes a lowercase string, now removed of its non-alphanumeric characters.
    It returns (as a list comprehension) a parsed and tokenized
    version of the postprint, with stopwords and names removed.
    """
    stop_words = set(stopwords.words("english"))
    name_words = set(names.words())
    word_tokens = word_tokenize("\n".join(text))
    return {w for w in word_tokens if w not in stop_words and name_words}


def most_common_words(word_set: set[str], n: int) -> list[tuple[str, int]]:
    """Takes a set of words and returns a list of tuples of the most common words and their frequencies."""
    return FreqDist(word_set).most_common(n)


class PDFScrape:
    """The PDFScrape class takes the provided string from a prior list
    comprehension of PDF files in a directory. From each pdf file, it parses the document
    and returns metrics about its composition and relevance.
    """

    def __init__(
        self, research_words: str, bycatch_words: str, target_words: str
    ) -> None:
        with open(research_words) as f:
            self.research_words = set(f.readlines())
        with open(bycatch_words) as f:
            self.bycatch_words = set(f.readlines())
        with open(target_words) as f:
            self.target_words = set(f.readlines())

    def scrape(self, search_text: str) -> ScrapeResult:
        preprints = []
        with pdfplumber.open(search_text) as study:
            n = len(study.pages)
            pages_to_check = list(study.pages)[:n]
            for page_number, page in enumerate(pages_to_check):
                page = study.pages[page_number].extract_text(
                    x_tolerance=3, y_tolerance=3
                )
                print(
                    f"[sciscraper]: Processing Page {page_number} of {n-1} | {search_text}...",
                    end="\r",
                )
                preprints.append(
                    page
                )  # Each page's string gets appended to preprint []

            manuscripts = [str(preprint).strip().lower() for preprint in preprints]
            # The preprints are stripped of extraneous characters and all made lower case.
            postprints = [re.sub(r"\W+", " ", manuscript) for manuscript in manuscripts]
            # The ensuing manuscripts are stripped of lingering whitespace and non-alphanumeric characters.
            all_words = compute_filtered_tokens(postprints)

            doi = guess_doi(search_text)
            target_words = self.target_words.intersection(all_words)
            bycatch_words = self.bycatch_words.intersection(all_words)
            research_intersection = self.research_words.intersection(all_words)
            word_score = len(target_words) - len(bycatch_words)
            frequency = most_common_words(all_words, 5)
            study_design = most_common_words(research_intersection, 3)

            return ScrapeResult(
                doi=doi,
                wordscore=word_score,
                frequency=frequency,
                study_design=study_design,
            )
