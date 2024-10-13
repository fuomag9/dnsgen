# coding=utf-8

import itertools
import pathlib
import re

import tldextract

NUM_COUNT = 3
WORDS = None


def create_registrar():
    """
    Create function registration decorator
    """
    registry = []

    def registrar(func):
        registry.append(func)
        return func

    registrar.members = registry
    return registrar


PERMUTATOR = create_registrar()
FAST_PERMUTATOR = create_registrar()


def partiate_domain(domain):
    """
    Split domain based on subdomain levels.
    """
    ext = tldextract.extract(domain.lower())
    return ext.subdomain.split(".") + [ext.registered_domain]


@PERMUTATOR
def insert_word_every_index(parts):
    """
    Create new subdomain levels by inserting words between existing levels
    """
    return [
        ".".join(parts[:-1][:i] + [word] + parts[:-1][i:] + [parts[-1]])
        for word in WORDS for i in range(len(parts))
    ]


@FAST_PERMUTATOR
@PERMUTATOR
def adjust_numbers(parts, operation):
    """
    Adjust numbers found in subdomain parts by increasing or decreasing them
    """
    domains = []
    parts_joined = ".".join(parts[:-1])
    digits = re.findall(r"\d{1,3}", parts_joined)

    for d in digits:
        for m in range(NUM_COUNT):
            new_digit = int(d) + (m + 1) * operation
            if new_digit < 0:
                break
            replacement = str(new_digit).zfill(len(d))
            domains.append(f"{parts_joined.replace(d, replacement)}.{parts[-1]}")

    return domains


@FAST_PERMUTATOR
def increase_num_found(parts):
    return adjust_numbers(parts, operation=1)


@FAST_PERMUTATOR
def decrease_num_found(parts):
    return adjust_numbers(parts, operation=-1)


@PERMUTATOR
def prepend_word_every_index(parts):
    """
    Prepend `WORD` and `WORD-` to each subdomain level.
    """
    domains = []
    for w in WORDS:
        for i in range(len(parts[:-1])):
            for prefix in [w, f"{w}-"]:
                tmp_parts = parts[:-1]
                tmp_parts[i] = f"{prefix}{tmp_parts[i]}"
                domains.append(".".join(tmp_parts + [parts[-1]]))
    return domains


@PERMUTATOR
def append_word_every_index(parts):
    """
    Append `WORD` and `WORD-` to each subdomain level.
    """
    domains = []
    for w in WORDS:
        for i in range(len(parts[:-1])):
            for suffix in [w, f"-{w}"]:
                tmp_parts = parts[:-1]
                tmp_parts[i] = f"{tmp_parts[i]}{suffix}"
                domains.append(".".join(tmp_parts + [parts[-1]]))
    return domains


@FAST_PERMUTATOR
@PERMUTATOR
def replace_word_with_word(parts):
    """
    Replace long words found in existing subdomains with others from the dictionary.
    """
    domains = []
    subdomain = ".".join(parts[:-1])

    for w in WORDS:
        if w in subdomain:
            for w_alt in WORDS:
                if w != w_alt:
                    domains.append(subdomain.replace(w, w_alt) + f".{parts[-1]}")

    return domains


def extract_custom_words(domains, wordlen):
    """
    Extend the dictionary based on target domain naming conventions.
    """
    valid_tokens = set()
    for domain in domains:
        tokens = set(itertools.chain.from_iterable(
            word.lower().split("-") for word in partiate_domain(domain)[:-1]
        ))
        valid_tokens.update(t for t in tokens if len(t) >= wordlen)
    return valid_tokens


def init_words(domains, wordlist, wordlen, fast):
    """
    Initialize the wordlist.
    """
    global WORDS
    if wordlist is None:
        wordlist = pathlib.Path(__file__).parent / "words.txt"

    WORDS = set(open(wordlist).read().splitlines())

    if fast:
        WORDS = list(WORDS)[:10]

    WORDS.update(extract_custom_words(domains, wordlen))
    WORDS = list(WORDS)


def generate(domains, wordlist=None, wordlen=5, fast=False, skip_init=False):
    """
    Generate permutations from provided domains.
    """
    if not skip_init:
        init_words(domains, wordlist, wordlen, fast)

    for domain in set(domains):
        parts = partiate_domain(domain)
        for perm in FAST_PERMUTATOR.members if fast else PERMUTATOR.members:
            yield from perm(parts)