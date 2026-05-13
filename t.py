import random
from wonderwords import RandomWord

_rw = RandomWord()

# pre-filter the lists once at startup, not on every call
ADJECTIVES = _rw.filter(
    include_parts_of_speech=["adjectives"],
    word_max_length=14,
    exclude_with_spaces=True,
)
NOUNS = _rw.filter(
    include_parts_of_speech=["nouns"],
    word_max_length=14,
    exclude_with_spaces=True,
)

# shuffle so we exhaust randomly
random.shuffle(ADJECTIVES)
random.shuffle(NOUNS)

_adj_pool = list(ADJECTIVES)
_noun_pool = list(NOUNS)

def generate_username() -> str:
    # refill if exhausted
    if not _adj_pool:
        _adj_pool.extend(ADJECTIVES)
        random.shuffle(_adj_pool)
    if not _noun_pool:
        _noun_pool.extend(NOUNS)
        random.shuffle(_noun_pool)

    adj = _adj_pool
    noun = _noun_pool
    number = str(random.randint(1, 99)).zfill(2)  # noqa: S311
    username = f"{adj}_{noun}_{number}"

    # safety net just in case
    if len(username) > 32:
        return generate_username()
    return username