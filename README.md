# Quran Translation Checker (AI agent + evaluation)

## What it does
- Initially I pasted the Malay translation from Quran.com to get the game working quickly, before setting up downloads of the entire Malay text by Basmeih. 
- Risks of errors during copying are acknowledged, so checker.py compares each verse's Malay with its English, surah by surah, and flags verses where the meaning does not match.  

## How it works 
- Tools below were created to address the risks:
- read_surah (tool): reads one surah's verses (English, Malay and optionally Arabic). Read-only. 
- flag_verse (tool): records one verse whose meaning doesn't match, with a reason and a kind. 
- check_surah (the agent loop): Claude reads the surah, compares verses, calls flag_verse for each problem, and stops when it has no more tool calls. 
- The issues are defined as :
    1. paste errors which require human verification and intervention. 
    2. translator "errors" are interpretation work done by the translator. This is due to semantic differences. Both texts look like faithful translations but differ, e.g. an added explanation or a different reading of the word. These are notes not actual errors. 
    
## Guardrails 
- Step limit: at most 6 Claude calls per surah (MAX_STEPS = 6). If it goes over, it stops with "too many steps", so it cannot loop forever or run up the bill. 
- Scope lock: Claude may only read the surah you gave it (run_tool).
- Read-only on the game's data: none of the tools can change the CTM files (the game's data). flag_verse only adds to a list, and the results go to report.txt in this folder. 
- Fixed labels: "kind" must be 'paste_error' or 'translator', enforced by the tool's enum. Claude cannot invent a third label, which keeps score.py reliable. 
- Rules against making things up: judge only the text it read with read_surah, never use its own memory of the Quran, and say so if a tool fails. 
- Cost on every run: tokens and dollar cost are printed for each run. 
- A human decides: the agent only reports. I read report.txt and fix the text myself. This is important due to the nature of sacred text in this project.  

## Evaluation
- I planted 10 errors across 8 surahs and made answer_key.txt to be scored with score.py 
- Results on the test set (10 planted errors, 8 surahs): 

| Run | Caught | False alarms | Cost |
|---|---|---|---|
| Claude Opus | 9/10 | 0 | $0.24 |
| Claude Haiku | 8/10 | 0 | ~1/40 of Opus |
| Opus + Arabic | 9/10 | 1 | $0.36 |
| Opus + Arabic + kind | 9/10 | 0 | $0.50 |


## What I learned
- The agent can spot a difference but cannot tell a paste error from a translator's choice without the source text. 
- On real data (Juz 30, $0.88), it labelled 78:37 and 87:7 as paste errors when both were translator differences. 
- Every run missed 102:2, a stray footnote number "(5)" which is a formatting slip, not a change in meaning. 
-   Simple checks like the one above are better executed by script than using LLM. 

## How to run
1. Install Python 3 and the Anthropic library:
   `pip install anthropic`
2. Set your Claude API key as an environment variable called `ANTHROPIC_API_KEY`.
3. Put the surah files in a `data` folder next to `checker.py`
   (or set `CTM_DATA` to another folder). Format: see Data below.
4. Check one or more surahs:
   `python checker.py 93 94`
   Findings go to `report.txt`; tokens and cost are printed at the end.
5. Settings at the top of `checker.py`:
   - `MODEL`: `claude-opus-5-5` or `claude-haiku-5-5`
   - `WITH_ARABIC`: `True` adds the Arabic to each verse
   - `TEST`: `True` reads a `test_data` folder instead (your copy with planted errors)
6. Score a test run: list the planted errors in `answer_key.txt`
   (one per line: `surah:ayah | type`), run the checker on the test copy, then
   `python score.py`
   It prints caught, missed and false alarms.

## Data
- Verse text is **not included** in this repo. The translations come from
  Quran.com (English; Malay by Abdullah Muhammad Basmeih) and belong to
  their translators.
- The test set used for the results above contains **deliberately planted
  errors**, so it is kept private.
- Each surah is one JSON file named by its number (e.g. `93.json`):

```json
{"name": "Ad-Duha",
 "ayahs": [{"number": 1, "english": "...", "malay": "...", "arabic": "..."}]}
```

- `answer_key.txt` lists the 10 planted errors (surah:ayah and type) so the
  scoring can be checked.