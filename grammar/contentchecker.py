from pydantic import BaseModel
from enum import Enum


def load_werkwoorden(path="data/generated_werkwoorden.txt"):
    werkwoorden = []
    with open(path, "r") as f:
        for line in f:
            werkwoord_vormen = [word.strip().lower() for word in line.strip().split()]
            werkwoorden.append(werkwoord_vormen)

            if len(werkwoord_vormen) != 10:
                print(f"Warning: Expected 10 forms for verb, got {len(werkwoord_vormen)}: {werkwoord_vormen}")

    return werkwoorden

werkwoorden = load_werkwoorden()

def get_verb(verb_infinitive: str) -> list[str]:
    for werkwoord_vormen in werkwoorden:
        if werkwoord_vormen[0] == verb_infinitive:
            return werkwoord_vormen
    return []

class WordType(str, Enum):
    noun = "Noun"
    verb = "Verb"
    adjective = "Adjective"


class SentenceRequirement(BaseModel):
    type: WordType
    options: list[str]

def clean_word(word: str) -> str:
    word = word.strip().lower()
    word = word.removesuffix(".")
    word = word.removesuffix("?")
    word = word.removesuffix(",")
    word = word.removesuffix(":")
    word = word.removesuffix(";")
    word = word.removesuffix("!")

    return word

def clean_sentence(sentence: list[str]) -> list[str]:
    return [clean_word(word) for word in sentence if word.strip()]

def check_content(sentence: list[str], requirements: list[SentenceRequirement]) -> bool:
    sentence = clean_sentence(sentence)
    for requirement in requirements:
        if not any(word in requirement.options for word in sentence if word):

            print(f"Warning: Expected {len(requirement.options)} {requirement.type.value}s, got {len(sentence)}: {sentence}")
            return False
        print(f"Requirement met for {requirement.type.value}: {requirement.options}")
    return True