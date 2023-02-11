from dataclasses import dataclass


@dataclass
class ScrapeResult:
    DOI: str
    wordscore: int
    frequency: list[tuple[str, int]]
    study_design: list[tuple[str, int]]
