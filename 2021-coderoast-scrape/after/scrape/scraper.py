from dataclasses import dataclass


@dataclass
class ScrapeResult:
    doi: str
    wordscore: int
    frequency: list[tuple[str, int]]
    study_design: list[tuple[str, int]]
