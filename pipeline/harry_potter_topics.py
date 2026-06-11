"""Harry Potter Shorts — rotating through different themes.

- **Theme cycle** (daily calendar): Hogwarts → Characters → Spells & Magic → Houses → Dark Arts → Behind the Scenes
  Same theme all day; next calendar day advances to the next theme block.
- **Topic pick**: random among topics in today's theme that are not yet marked used.
  When a theme's pool is exhausted, its used-list resets and topics can appear again.

State file: `output/history/hp_topic_rotation.json` (cache this path in CI like story history).
"""
from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = REPO_ROOT / "output" / "history" / "hp_topic_rotation.json"

# Order of themes by calendar day (cycles forever).
THEME_ORDER: list[str] = [
    "hogwarts",
    "characters",
    "spells_magic",
    "houses",
    "dark_arts",
    "behind_scenes",
]

HP_POOLS: dict[str, list[str]] = {
    "hogwarts": [
        "The hidden chambers of Hogwarts nobody talks about",
        "Why Hogwarts sorting ceremony uses the Sorting Hat",
        "The secret passages of Hogwarts castle",
        "How Hogwarts got its magical protections",
        "The story of the Room of Requirement",
        "Why Dumbledore placed Horcruxes around Hogwarts",
        "The history of the Forbidden Forest creatures",
        "Why the bridge at Hogwarts collapses",
        "The mystery of Platform 9¾",
        "How the Hogwarts Express actually works",
        "The story of the Whomping Willow",
        "Why the Marauder's Map shows everything",
        "The history of Hogsmeade village",
        "The secret of the Astronomy Tower",
        "Why Quidditch is so dangerous",
        "The mystery of the statue of the one-eyed witch",
        "How the Sorting Hat decides your house",
        "The truth about the Fat Friar ghost",
        "Why the lake near Hogwarts is dangerous",
        "The story of the secret Gryffindor tower entrance",
    ],
    "characters": [
        "The real story of Severus Snape — hero or villain",
        "Why Dumbledore trusted Snape his whole life",
        "The untold story of Harry Potter's parents",
        "Who was Neville Longbottom before the prophecy",
        "The story of Remus Lupin's transformation",
        "Why Draco Malfoy's father was so dangerous",
        "The real truth about Tom Riddle's childhood",
        "Who was Gellert Grindelwald",
        "The story of Sirius Black's wrongful imprisonment",
        "Why Hermione was the real hero of the series",
        "The untold story of Luna Lovegood's mother",
        "Who was James Potter really",
        "The story of Ron Weasley's insecurities",
        "Why Lavender Brown wasn't the villain",
        "The truth about Peter Pettigrew's betrayal",
        "Who was Cedric Diggory beyond the tournament",
        "The story of Ginny Weasley's possession",
        "Why Dumbledore allowed Harry to suffer",
        "The real character of Albus Dumbledore",
        "Who was Nearly Headless Nick before death",
    ],
    "spells_magic": [
        "How does Expecto Patronum actually work",
        "The most dangerous spell in Harry Potter",
        "Why Levicorpus is considered dark magic",
        "The story of the Cruciatus Curse",
        "How does the killing curse work on Horcruxes",
        "The real power of Avada Kedavra",
        "Why some spells backfire on their casters",
        "The magic behind Polyjuice Potion",
        "How does Veritaserum reveal the truth",
        "The forbidden spells of Harry Potter",
        "Why Occlumency is so hard to master",
        "The truth about Legilimency",
        "How does Accio actually find objects",
        "The magic of the Patronus charm explained",
        "Why wand vibrations matter in spellcasting",
        "The story of the Unforgivable Curses",
        "How does Apparition magic work",
        "The mystery of blood magic in Harry Potter",
        "Why Transfiguration is the hardest magic",
        "The magic behind love protection spells",
    ],
    "houses": [
        "Why Gryffindor isn't always the bravest house",
        "The real traits of Hufflepuff beyond loyalty",
        "Why Ravenclaw values more than just intelligence",
        "What makes someone truly Slytherin",
        "The history of Godric Gryffindor",
        "Who was Helga Hufflepuff",
        "The story of Rowena Ravenclaw",
        "Why Salazar Slytherin left Hogwarts",
        "The houses' secret rivalries explained",
        "Why the Sorting Hat struggles with some students",
        "The story of inter-house relationships",
        "Why house points matter beyond competition",
        "The mystery of Hatstall students",
        "The truth about house ghosts",
        "Why Slytherin has bad reputation",
        "The history of Gryffindor common room",
        "The secrets of Hufflepuff dormitory",
        "Why Ravenclaw tower is impossible to find",
        "The story of Slytherin dungeons",
        "The real meaning of house pride in wizarding world",
    ],
    "dark_arts": [
        "The story of the Horcruxes explained",
        "Why Voldemort couldn't love anyone",
        "The real power of the Elder Wand",
        "How Horcruxes actually made Voldemort weaker",
        "The truth about Voldemort's origin",
        "Why the Deathly Hallows are so powerful",
        "The story of the Resurrection Stone",
        "How the Invisibility Cloak changed everything",
        "Why the Elder Wand never stayed loyal",
        "The mystery of Voldemort's body",
        "The truth about Nagini the snake",
        "Why Voldemort split his soul seven times",
        "The story of the Diadem Horcrux",
        "How did Voldemort return to power",
        "The real danger of Horcrux hunting",
        "Why Dumbledore collected Horcruxes",
        "The mystery of the vanishing cabinet",
        "The truth about Death Eaters' loyalty",
        "Why Voldemort feared death more than anything",
        "The story of the Department of Mysteries",
    ],
    "behind_scenes": [
        "The inspiration behind the sorting ceremony",
        "Why JK Rowling hid Easter eggs throughout the series",
        "The real reason Harry chose Ginny",
        "How the time turner changed the whole series",
        "The mystery of the prophecy nobody knows about",
        "Why Dumbledore's decisions were controversial",
        "The story of Neville's redemption arc",
        "The truth about the love potion subplot",
        "Why the books changed from children to dark",
        "The real ending Rowling considered",
        "The deleted scenes of Harry Potter",
        "Why certain characters died unnecessarily",
        "The mystery plot holes fans caught",
        "The truth about Harry's destiny",
        "Why the epilogue was controversial",
        "The real meaning of the scar",
        "The story behind Dumbledore's scars",
        "Why Horcruxes were the solution",
        "The truth about the prophecy",
        "The mystery of Dumbledore's past",
    ],
}


def _load_state() -> dict[str, dict]:
    if not STATE_PATH.is_file():
        return {}
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_state(data: dict[str, dict]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def theme_for_today() -> str:
    """Which Harry Potter theme today (cycles through THEME_ORDER)."""
    d = datetime.now().date()
    idx = d.toordinal() % len(THEME_ORDER)
    return THEME_ORDER[idx]


def pick_hp_topic(channel_id: str) -> tuple[str, str]:
    """Return (topic_hint, theme_key) for Groq. Does not persist yet."""
    theme = theme_for_today()
    pool = HP_POOLS.get(theme, [])
    if not pool:
        raise RuntimeError(f"No Harry Potter topics for theme {theme!r}")

    state = _load_state()
    ch = state.setdefault(channel_id, {"used": {}})

    used_list = ch["used"].setdefault(theme, [])
    used_set = set(used_list)
    available = [t for t in pool if t not in used_set]

    if not available:
        ch["used"][theme] = []
        available = list(pool)

    topic = random.choice(available)
    return topic, theme


def commit_hp_topic(channel_id: str, theme: str, topic: str) -> None:
    """Call after a full successful run so this topic is not chosen again until pool resets."""
    state = _load_state()
    ch = state.setdefault(channel_id, {"used": {}})
    used = ch["used"].setdefault(theme, [])
    if topic not in used:
        used.append(topic)
    _save_state(state)
