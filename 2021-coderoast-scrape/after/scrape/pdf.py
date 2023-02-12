import re
from os import path

import pdfplumber
from nltk import FreqDist
from nltk.corpus import names, stopwords
from nltk.tokenize import word_tokenize
from scrape.scraper import ScrapeResult


TARGET_WORDS = {
    "prosocial",
    "design",
    "intervention",
    "reddit",
    "humane",
    "social media",
    "user experience",
    "nudge",
    "choice architecture",
    "user interface",
    "misinformation",
    "disinformation",
    "Trump",
    "conspiracy",
    "dysinformation",
    "users",
    "Thaler",
    "Sunstein",
    "boost",
}

BYCATCH_WORDS = {
    "psychology",
    "pediatric",
    "pediatry",
    "autism",
    "mental",
    "medical",
    "oxytocin",
    "adolescence",
    "infant",
    "health",
    "wellness",
    "child",
    "care",
    "mindfulness",
}

RESEARCH_WORDS = {
    "big data",
    "data",
    "analytics",
    "randomized controlled trial",
    "RCT",
    "moderation",
    "community",
    "social media",
    "conversational",
    "control",
    "randomized",
    "systemic",
    "analysis",
    "thematic",
    "review",
    "study",
    "case series",
    "case report",
    "double blind",
    "ecological",
    "survey",
}


def compute_filtered_tokens(text:list[str]) -> set[str]:
    """Takes a lowercase string, now removed of its non-alphanumeric characters.
    It returns (as a list comprehension) a parsed and tokenized
    version of the postprint, with stopwords and names removed.
    """
    stop_words = set(stopwords.words("english"))
    name_words = set(names.words())
    word_tokens = word_tokenize("\n".join(text))
    return {
        w
        for w in word_tokens
        if w not in stop_words and name_words
    }


class PDFScrape:
    """The PDFScrape class takes the provided string from a prior list
    comprehension of PDF files in a directory. From each pdf file, it parses the document
    and returns metrics about its composition and relevance.
    """

    def scrape(self, search_text: str) -> ScrapeResult:
        self.search_text = search_text
        self.preprints = []
        with pdfplumber.open(self.search_text) as self.study:
            self.n = len(self.study.pages)
            self.pages_to_check = [page for page in self.study.pages][: self.n]
            for page_number, page in enumerate(self.pages_to_check):
                page = self.study.pages[page_number].extract_text(
                    x_tolerance=3, y_tolerance=3
                )
                print(
                    f"[sciscraper]: Processing Page {page_number} of {self.n-1} | {search_text}...",
                    end="\r",
                )
                self.preprints.append(
                    page
                )  # Each page's string gets appended to preprint []

            self.manuscripts = [
                str(preprint).strip().lower() for preprint in self.preprints
            ]
            # The preprints are stripped of extraneous characters and all made lower case.
            postprints = [
                re.sub(r"\W+", " ", manuscript) for manuscript in self.manuscripts
            ]
            # The ensuing manuscripts are stripped of lingering whitespace and non-alphanumeric characters.
            all_words = compute_filtered_tokens(postprints)

            target_words = TARGET_WORDS.intersection(all_words)
            bycatch_words = BYCATCH_WORDS.intersection(all_words)
            word_score = len(target_words) - len(bycatch_words)
            research_word_overlap = RESEARCH_WORDS.intersection(all_words)

            return ScrapeResult(
                DOI=self.get_doi(),
                wordscore=word_score,
                frequency=FreqDist(all_words).most_common(5),
                study_design=FreqDist(research_word_overlap).most_common(3),
            )

    def get_doi(self) -> str:
        """Approximates a possible DOI, assuming the file is saved in YYMMDD_DOI.pdf format."""
        self.getting_doi = path.basename(self.search_text)
        self.doi = self.getting_doi[7:-4]
        self.doi = self.doi[:7] + "/" + self.doi[7:]
        return self.doi
