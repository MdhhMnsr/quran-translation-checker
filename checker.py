import json
import os
import sys
from pathlib import Path
import anthropic

client = anthropic.Anthropic()
HERE = Path(__file__).parent
CTM = Path(os.environ.get("CTM_DATA", HERE / "data"))
TEST = False
MODEL = "claude-opus-5-5"
WITH_ARABIC = True
PRICES = {"claude-opus-5-5": (4,20), "claude-haiku-5-5": (0.10,0.50)}
DATA = HERE / "test_data" if TEST else CTM 
MAX_STEPS = 6 
tokens = {"in": 0, "out": 0}

#Tool 1: read a surah (read-only) 
def read_surah(number):
    data = json.loads((DATA / f"{number}.json").read_text(encoding="utf-8"))
    verses = []
    for a in data ["ayahs"]:
        verse = {"ayah": a["number"],
                       "english": a["english"],
                       "malay": a.get("malay","")}
        if WITH_ARABIC:
            verse["arabic"] = a["arabic"]
        verses.append(verse)
    return {"surah": number, "name" :data["name"], "verses": verses}

#Tool 2: record a problem (writes only to the findings list, never to CTM)
findings = []

def flag_verse(surah, ayah, kind,  problem):
    findings.append({"surah": surah, "ayah": ayah, "kind": kind,  "problem": problem})
    return "Recorded."

tools = [
    {"name": "read_surah",
     "description": "Read a surah from the CTM game: its name and, for every verse,"
                    "the English meaning and the Malay meaning.",
    "input_schema": {"type":"object",
                     "properties":{"number": {"type":"integer", "description":"Surah number,1 to 114"} },
                     "required":["number"]}},
    {"name": "flag_verse",
     "description": "Record one verse whose Malay meaning does not match its English meaning.",
     "input_schema": {"type":"object",
                      "properties":{"surah": {"type":"integer"},
                                    "ayah": {"type":"integer"},
                                    "kind": {"type":"string",
                                             "enum": ["paste_error", "translator"],
                                             "description" : "Which kind of problem this is"},
                                    "problem": {"type": "string", "description": "Short reason in English"}},
                       "required": ["surah", "ayah", "kind", "problem"]}},             
]        

RULES = ("You check the Malay meanings in a Quran game. Call read_surah for a surah "
         "you are given, then compare each verse's Malay with its English. "
         "They are two different published translations, so different wording, word order "
         "or style is normal and is NOT an error. Only flag a verse when the meaning clearly "

         "differs: the wrong verse pasted, meaning missing or added, a changed name or "
         "attribute, a dropped 'not', or a different person (he / you / they). "
         "Call flag_verse once for each problem. Only judge text you read with read_surah; "
         "never rely on your memory of the Quran. If a tool fails, say you could not check. "

         "End with one line: how many verses you checked and how many you flagged. ")

ARABIC_RULES = ("The Arabic original is included for each verse. When the Malay and "
                "English differ, compare both with the Arabic and say in the flag which "
                "one is closer, quoting the Arabic word. ")

KIND_RULES = ("Flag every verse where the meanings differ, and choose a kind. "
              "Use paste_error when the text in the game is wrong: the wrong verse, "
              "a missing or cut-off part, or a word that changes the meaning and is not "
              "a translator's explanation. Use translator when each text looks like a "
              "faithful translation but they differ, for example an added explanation "
              "or a different reading of a word. ")
RULES = RULES + KIND_RULES

if WITH_ARABIC:
    RULES = RULES + ARABIC_RULES

def run_tool(name, args, allowed):
    if name == "read_surah":
        if args["number"] !=allowed:
            return f"Not allowed: you may only read surah {allowed}."
        return json.dumps(read_surah(args["number"]), ensure_ascii=False)
    if name ==  "flag_verse":
        return flag_verse(args["surah"], args["ayah"], args["kind"], args["problem"])
    return f"Unknown tool: {name}."

def check_surah(number):
    messages = [{"role": "user", "content": f"Check surah {number}."}]
    for step in range(MAX_STEPS):
        response = client.messages.create(
            model=MODEL,
            system=RULES,
            max_tokens=16000,
            tools=tools,
            messages=messages,
        )
        tokens["in"] +=response.usage.input_tokens
        tokens["out"] +=response.usage.output_tokens
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            for block in response.content:
                if block.type == "text":
                    print(block.text)
            return

        results = []
        for block in response.content: 
            if block.type == "tool_use": 
                results.append({"type": "tool_result",
                                "tool_use_id": block.id,
                                "content": run_tool(block.name, block.input, number)}) 
        messages.append({"role": "user", "content": results })
    print(f"Stopped surah {number}: too many steps.") 

numbers = [int(n) for n in sys.argv [1:]] or [1]
for n in numbers:
    print(f"\n=== Surah {n} ===")
    before = len(findings)
    check_surah(n)
    print(f"Recorded flags: {len(findings) - before}")

report = HERE / "report.txt" 
with open(report, 'w', encoding="utf-8") as f:
    for x in findings: 
        f.write(f"{x['surah']}:{x['ayah']} [{x['kind']}] {x['problem']}\n")

price_in, price_out = PRICES[MODEL]
cost = tokens["in"] * price_in / 1_000_000 + tokens["out"] * price_out / 1_000_000
print(f"Model: {MODEL}")
print(f"\n{len(findings)} verse(s) flagged. Report: {report}")
print(f"Tokens in/out: {tokens['in']}/{tokens['out']}  Cost: ${cost:.4f}")

