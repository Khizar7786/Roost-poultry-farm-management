"""
UC-09 Chatbot Interaction. A real deployment would swap this keyword
matcher for an NLP/LLM service, but the use case's contract stays the
same: farmer asks a natural-language question, gets a concise answer or
is told the query couldn't be understood (alt. flow: apologize + offer to
connect to a human / support ticket).

Two kinds of entries live here:
1. App-feature entries — how to use Roost itself.
2. Poultry husbandry entries — general broiler-farming knowledge
   (vaccination schedule, feed program, common diseases, deworming).
   These are standard, widely-published extension/hatchery guidance, not
   a substitute for a vet — each answer says so where it matters (dosing,
   diagnosis, antibiotics), since specifics genuinely vary by product,
   bird weight, and regional disease pressure.

Matching strategy (see `_matches` below): single-word keywords use
per-token *stem* matching so "vaccinate"/"vaccination"/"vaccine" and
"worm"/"worms"/"deworming" all match a single keyword ("vaccinat",
"worm") without needing every conjugation spelled out. Short, common
words (used for greetings) instead require an *exact* token match —
otherwise short stems like "hi" match inside unrelated words (e.g.
"chick" contains "hi"), which is its own class of bug.

Order matters: specific entries (coccidiosis, worms, respiratory,
biosecurity) are listed before the general "disease" catch-all, so a
specific question gets the specific answer instead of being swallowed
by a broader entry earlier in the list.
"""

import re

EXAMPLE_TOPICS = [
    "chick counting",
    "mortality alerts",
    "price forecasts",
    "feed programs",
    "vaccination schedules",
    "common diseases",
    "adding staff",
]

GREETINGS = {
    "keywords": ["hi", "hello", "hey", "hiya", "salam", "assalam", "good morning", "good afternoon", "good evening"],
    "answer": "Hey! I can help with questions about " + ", ".join(EXAMPLE_TOPICS[:-1]) + f", and {EXAMPLE_TOPICS[-1]}. "
              "What would you like to know?",
}

HELP_REQUESTS = {
    "keywords": ["help", "options", "menu", "commands"],
    "answer": "I can answer questions about: " + ", ".join(EXAMPLE_TOPICS) + ". Just ask in your own words — "
              "e.g. \"when should I vaccinate my chicks?\" or \"how does chick counting work?\"",
}

THANKS = {
    "keywords": ["thank", "thanks", "thx", "appreciate"],
    "answer": "Happy to help! Let me know if anything else comes up.",
}

FAREWELLS = {
    "keywords": ["bye", "goodbye", "see you", "later"],
    "answer": "Take care! I'm here anytime you need a hand.",
}

# These match on exact token identity (see _matches) — kept separate
# from KNOWLEDGE_BASE, whose keywords use looser stem matching instead.
SMALLTALK = [GREETINGS, HELP_REQUESTS, THANKS, FAREWELLS]

KNOWLEDGE_BASE = [
    # --- App features -----------------------------------------------------
    {
        "keywords": ["chick count", "counting", "how many chicks"],
        "answer": "Chick counting works by uploading or capturing a photo of the flock — our AI model "
                  "detects and counts individual chicks and shows the result within a few seconds. "
                  "You'll need to pick a batch first, so create one on the Batches page if you haven't yet.",
    },
    {
        "keywords": ["mortality", "dead bird", "died", "dead chick"],
        "answer": "Mortality events are detected automatically from camera footage, or you can log them "
                  "manually under a batch. Confirmed events are subtracted from that batch's live count "
                  "and a high-priority alert is raised.",
    },
    {
        "keywords": ["huddling", "cold stress"],
        "answer": "Huddling — chicks clustering tightly together — usually points to cold stress if it's "
                  "widespread and early in the brooding period (check your heat source), or to illness if "
                  "it's isolated to a few birds. Either way it's worth a closer look; combine it with other "
                  "signs (activity level, feed intake) before deciding which.",
    },
    {
        "keywords": ["price forecast", "market", "price predict", "sell price"],
        "answer": "Market price forecasts come from a trained model that predicts the Lahore farm-gate "
                  "broiler price a few days ahead. Just click Generate on the Price Forecast page — no "
                  "sales history required, the model uses its own market dataset.",
    },
    {
        "keywords": ["feed stock", "inventory", "reorder", "feed log"],
        "answer": "Feed stock levels are shown on your dashboard, and you'll see a reorder warning once "
                  "any feed type drops below its threshold. Employees can log daily consumption against "
                  "a batch to keep stock levels accurate.",
    },
    {
        "keywords": ["employee", "staff", "add user"],
        "answer": "Farm owners can add employee accounts from the Staff page. Employees can capture "
                  "images, log feed and vaccinations, and view alerts, but can't see sales or financial "
                  "reports.",
    },
    {
        "keywords": ["batch", "flock"],
        "answer": "Batches track a flock from arrival to sale. Create one on the Batches page (owners "
                  "only) — you'll need at least one batch before you can run chick counting.",
    },

    # --- Poultry husbandry knowledge (specific first, general last) -------
    {
        "keywords": ["coccidiosis", "bloody dropping", "coccidia", "cocci"],
        "answer": "Coccidiosis is caused by Eimeria parasites and spreads fast in damp litter — watch "
                  "for bloody or watery droppings, lethargy, and reduced feed intake, usually between "
                  "3-6 weeks of age. Standard treatment is an anticoccidial in the drinking water (e.g. "
                  "amprolium or toltrazuril, per the product label). Prevention matters more than cure: "
                  "keep litter dry, avoid overcrowding, and use coccidiosis-preventive starter feed if "
                  "it's available in your area.",
    },
    {
        "keywords": ["worm", "deworm", "parasite"],
        "answer": "Gut worms (roundworms, tapeworms) show up as poor weight gain, pale combs, and "
                  "sometimes visible worms in droppings — more common in litter or free-range systems. "
                  "Common broad-spectrum dewormers used in poultry include piperazine, levamisole, and "
                  "albendazole, typically dosed via drinking water every 4-6 weeks in at-risk flocks — "
                  "always follow the specific product's label for exact dosing per bird weight, since "
                  "concentrations differ between brands. Clean, dry litter and rotating range areas "
                  "reduce reinfection.",
    },
    {
        "keywords": ["respiratory", "crd", "mycoplasma", "cough", "sneeze"],
        "answer": "Coughing, sneezing, and nasal discharge point to a respiratory issue — commonly CRD "
                  "(Mycoplasma), Infectious Bronchitis, or Newcastle Disease. Improve ventilation and "
                  "reduce ammonia buildup first, and get a vet involved for antibiotics (e.g. tylosin or "
                  "enrofloxacin are commonly used for CRD) since the right choice depends on the actual "
                  "cause — treating the wrong one wastes time your flock doesn't have.",
    },
    {
        "keywords": ["biosecurity", "hygiene", "disinfect"],
        "answer": "The basics that prevent most broiler disease outbreaks: disinfect the shed and "
                  "equipment between batches, limit visitor/vehicle access, keep litter dry, control "
                  "rodents and wild birds, and quarantine any sick birds immediately instead of waiting "
                  "to see if they recover. Most of these matter more than any single medicine.",
    },
    {
        "keywords": ["vaccinat", "vaccine", "immuniz"],
        "answer": "Typical broiler vaccination schedule: Marek's disease is usually given at the "
                  "hatchery on day 1. Around day 5-7, Newcastle Disease + Infectious Bronchitis (combo, "
                  "eye-drop or drinking water). Around day 14, Gumboro/IBD (drinking water), often with "
                  "a booster around day 18-21 in high-risk areas. Exact timing varies by region, hatchery, "
                  "and local disease pressure, so confirm the schedule with your hatchery or vet. Log each "
                  "one on the Vaccinations page once it's scheduled and administered.",
    },
    {
        "keywords": ["starter feed", "grower feed", "finisher feed", "feed program", "feed schedule",
                     "what to feed", "feed by day", "feed by age"],
        "answer": "Standard 3-phase broiler feed program: Starter feed (day 0-10, ~22-23% protein, fine "
                  "crumbs) → Grower feed (day 11-24, ~20-21% protein, pellets) → Finisher feed (day 25 "
                  "to market, ~18-19% protein, larger pellets). Feed should be available free-choice "
                  "throughout, with clean water always accessible. Track consumption on the Feed page.",
    },
    {
        "keywords": ["feed"],
        "answer": "Broilers are typically fed in 3 phases: Starter (day 0-10), Grower (day 11-24), and "
                  "Finisher (day 25 to market) — protein content steps down from about 23% to 18% across "
                  "the three. Ask me \"feed schedule\" for the full breakdown, or check the Feed page to "
                  "track your stock and consumption.",
    },
    {
        "keywords": ["disease", "sick", "illness", "chicken health", "unwell"],
        "answer": "Common broiler diseases: Coccidiosis (bloody droppings, lethargy), Newcastle Disease "
                  "and Infectious Bronchitis (respiratory/nervous signs, viral — prevention via "
                  "vaccination is key, no cure), Gumboro/IBD (weakens young chicks' immune system), "
                  "CRD/Mycoplasma (respiratory, needs vet-guided antibiotics), and gut worms (poor "
                  "weight gain, pale combs). Isolate sick birds immediately and involve a vet for "
                  "diagnosis — ask me about a specific one (\"worms\", \"coccidiosis\", \"respiratory\") "
                  "for more detail.",
    },
]

FALLBACK_ANSWER = (
    "I'm not sure how to help with that yet. I can answer questions about " + ", ".join(EXAMPLE_TOPICS) + " — "
    "try rephrasing, or would you like me to connect you with a member of our support team instead?"
)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def _matches(query_text: str, tokens: list[str], keyword: str, *, exact: bool) -> bool:
    if " " in keyword:
        return keyword in query_text
    if exact:
        return keyword in tokens
    return any(keyword in tok for tok in tokens)  # stem match: "worm" matches "worms", "deworming"


def answer_query(query: str) -> dict:
    normalized = query.lower().strip()
    tokens = _tokenize(normalized)

    for entry in SMALLTALK:
        if any(_matches(normalized, tokens, kw, exact=True) for kw in entry["keywords"]):
            return {"answer": entry["answer"], "understood": True}

    for entry in KNOWLEDGE_BASE:
        if any(_matches(normalized, tokens, kw, exact=False) for kw in entry["keywords"]):
            return {"answer": entry["answer"], "understood": True}

    return {"answer": FALLBACK_ANSWER, "understood": False}
