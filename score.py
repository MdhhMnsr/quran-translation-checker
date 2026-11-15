from  pathlib import Path

HERE = Path(__file__).parent

def verses(file, kind=None):
    found = set()
    for line in (HERE / file).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            if kind is None or f"[{kind}]" in line: 
                found.add(line.split()[0])
    return found

planted = verses("answer_key.txt")
flagged = verses("report.txt", "paste_error")

caught = planted & flagged
missed = planted - flagged
false_alarms = flagged - planted

print(f"Caught = {len(caught)} of {len(planted)} ({len(caught)/len(planted):.0%})")
print("Missed:" , sorted(missed))
print("False alarms:" , sorted(false_alarms))

notes = verses("report.txt", "translator")
print("Translator notes:", sorted(notes))
