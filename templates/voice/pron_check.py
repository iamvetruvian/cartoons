"""Pronunciation gate: every script word must be HEARD correctly before picture lock.

  templates/voice/py templates/voice/pron_check.py <project>/voice_work/ [--allow w1,w2,...]

<project>/voice_work/ holds script.json (display lines), data/narration.wav (24 kHz)
and data/lines.json (exact per-line windows) as built by the TTS assembly step.
Transcribes with faster-whisper small.en (same model as words.py), aligns the
heard words to the script, and FAILS (exit 1) on any mismatch not in
allowlist.json. Fix loop: add a speak.json respelling or a comma/period to force
a boundary, re-render ONLY the flagged lines, re-assemble, re-run this.

Number phrases canonicalize ("eighteen hundreds" == "1800s" == "one thousand
eight hundred"), so Whisper's digit habits never flag. Hyphenated script words
split ("farm-raised" == "farm raised"). Whisper normalizes sound to likely
words, so this catches what a listener would hear wrong ("lateen hundreds",
"clark" for "clerk") but can also flag its own mishearings: review each flag;
real mispronunciations get fixed, Whisper errors go in allowlist.json
("line:word"). Segments with avg_logprob < -1.0 are listed as low-confidence
audit items even when the words match.
"""
import argparse
import json
import re
import subprocess
import sys
from difflib import SequenceMatcher
from pathlib import Path

norm = lambda w: re.sub(r'[^a-z0-9]+', '', w.lower())

ONES = ('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen '
        'fifteen sixteen seventeen eighteen nineteen').split()
NUMW = {**{w: i for i, w in enumerate(ONES)},
        'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60,
        'seventy': 70, 'eighty': 80, 'ninety': 90,
        'hundred': 100, 'thousand': 1000, 'million': 1000000,
        'hundreds': 100, 'thousands': 1000, 'millions': 1000000}

# same sound, different spelling: never a pronunciation error (extend per project)
HOMO = [{'delhi', 'deli'}, {'fined', 'find'}, {'harbour', 'harbor'}]


def hom(t):
    for c in HOMO:
        if t in c:
            return sorted(c)[0]
    return t


def isnum(t):
    return t.isdigit() or t in NUMW


def canon_run(toks):
    total = current = 0
    for t in toks:
        if t.isdigit():
            current += int(t)
        elif t in ('hundred', 'hundreds'):
            current = (current or 1) * 100
        elif t in ('thousand', 'thousands'):
            total += (current or 1) * 1000
            current = 0
        elif t in ('million', 'millions'):
            total += (current or 1) * 1000000
            current = 0
        else:
            current += NUMW[t]
    return f'NUM{total + current}'


def canonical(items):
    """items: [(normtok, meta)] -> (ctoks, groups); number runs collapse to NUM<n>."""
    ctoks, groups = [], []
    i = 0
    while i < len(items):
        if isnum(items[i][0]):
            j = i
            while j < len(items) and isnum(items[j][0]):
                j += 1
            ctoks.append(canon_run([t for t, _ in items[i:j]]))
            groups.append(list(range(i, j)))
            i = j
        else:
            ctoks.append(items[i][0])
            groups.append([i])
            i += 1
    return ctoks, groups


ORD_IRR = {'first': 'one', 'second': 'two', 'third': 'three', 'fifth': 'five', 'eighth': 'eight',
           'ninth': 'nine', 'twelfth': 'twelve'}


def deordinal(t):
    """fifteenth -> fifteen (so number runs canonicalize identically on both sides)."""
    if t in ORD_IRR:
        return ORD_IRR[t]
    if t.endswith('ieth') and t[:-4] + 'y' in NUMW:
        return t[:-4] + 'y'
    if t.endswith('th') and t[:-2] in NUMW:
        return t[:-2]
    return t


def clean_heard(tok):
    t = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", tok.lower()).replace(',', '')
    m = re.fullmatch(r"(\d+)('?s)?", t)
    if m:
        return m.group(1)
    m = re.fullmatch(r"(\d+)(st|nd|rd|th)s?", t)
    if m:
        return m.group(1)
    return t


def heard_words(audio_path):
    from faster_whisper import WhisperModel
    import numpy as np
    try:
        model = WhisperModel('small.en', device='cuda', compute_type='float16')
    except Exception as e:
        print(f'Whisper GPU unavailable ({type(e).__name__}); CPU instead', flush=True)
        model = WhisperModel('small.en', device='cpu', compute_type='int8')
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(audio_path), '-ac', '1', '-ar',
                          '16000', '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    segs, _ = model.transcribe(np.frombuffer(raw, dtype=np.float32), word_timestamps=True)
    heard, lowconf = [], []
    for s in segs:
        if (s.avg_logprob or 0) < -1.0:
            lowconf.append({'s': round(s.start, 2), 'e': round(s.end, 2),
                            'p': round(s.avg_logprob, 2), 'text': s.text.strip()})
        for w in s.words or []:
            t = clean_heard(w.word.strip())
            if norm(t):
                heard.append((t, w.start + 0.04, w.end))
    return heard, lowconf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('workdir')
    ap.add_argument('--allow', default='', help='extra allowlist entries line:word,...')
    ap.add_argument('--dump', nargs=2, type=float, default=None, metavar=('FROM', 'TO'),
                    help='print raw heard tokens in [FROM, TO) seconds and exit (diagnosis)')
    a = ap.parse_args()
    W = Path(a.workdir)
    S = json.loads((W / 'script.json').read_text())
    L = json.loads((W / 'data/lines.json').read_text())['lines']
    allow = set(json.loads((W / 'allowlist.json').read_text())) if (W / 'allowlist.json').exists() else set()
    allow |= {x for x in a.allow.split(',') if x}

    script = [(w, i) for i, ln in enumerate(S['lines']) for w in ln['text'].split() if norm(w)]
    heard, lowconf = heard_words(W / 'data/narration.wav')
    if a.dump:
        for t, s, e in heard:
            if a.dump[0] <= s < a.dump[1]:
                print(f'{s:6.2f}-{e:6.2f}  {t}', flush=True)
        return 0
    Aitems, Bitems = [], []
    for si, (w, _) in enumerate(script):
        for p in [p for p in w.split('-') if norm(p)] or [w]:
            Aitems.append((hom(deordinal(norm(p))), si))
    for hi, (t, s, e) in enumerate(heard):
        Bitems.append((hom(deordinal(norm(t))), hi))
    A, GA = canonical(Aitems)
    B, GB = canonical(Bitems)
    sm = SequenceMatcher(None, A, B, autojunk=False)
    htime = {}
    for tag, a0, a1, b0, b1 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(a1 - a0):
                h0, h1 = heard[GB[b0 + k][0]], heard[GB[b0 + k][-1]]
                htime[a0 + k] = (h0[1], h1[2])
    bounds = [(l['start'], l['end']) for l in L]

    def line_of(ai):
        return script[Aitems[GA[ai][0]][1]][1]

    def stamp(ai):
        if ai in htime:
            return htime[ai]
        lo = next((htime[k][1] for k in range(ai - 1, -1, -1) if k in htime), None)
        hi = next((htime[k][0] for k in range(ai + 1, len(A)) if k in htime), None)
        l0, l1 = bounds[line_of(ai)]
        return (lo if lo is not None else l0), (hi if hi is not None else l1)

    def origs(ai0, ai1):
        out = []
        for ai in range(ai0, max(ai1, ai0 + 1)):
            if ai >= len(A):
                break
            w = script[Aitems[GA[ai][0]][1]][0]
            if not out or out[-1] != w:
                out.append(w)
        return out

    flags = []
    for tag, a0, a1, b0, b1 in sm.get_opcodes():
        if tag == 'equal':
            continue
        ow = origs(a0, a1)
        if f"{line_of(min(a0, len(A) - 1))}:{norm(ow[0])}" in allow:
            continue
        s, e = stamp(min(a0, len(A) - 1))
        got = ' '.join(heard[h][0] for b in range(b0, b1) for h in GB[b]) or '-'
        flags.append({'line': line_of(min(a0, len(A) - 1)), 'script': ' '.join(ow),
                      'heard': got, 's': round(s, 2), 'e': round(e, 2)})
    (W / 'data/pron_report.json').write_text(json.dumps(
        {'flags': flags, 'lowconf': lowconf, 'heard_n': len(heard), 'script_n': len(script)}, indent=1))
    print(f'checked {len(script)} script words against {len(heard)} heard words', flush=True)
    for f in flags:
        print(f"FLAG  L{f['line']} {f['s']:6.2f}-{f['e']:6.2f}  script:[{f['script']}] heard:[{f['heard']}]",
              flush=True)
    for c in lowconf:
        print(f"LOWCONF {c['s']:6.2f}-{c['e']:6.2f} p={c['p']} [{c['text'][:60]}]", flush=True)
    if flags:
        print(f'PRON CHECK: FAIL ({len(flags)} flags) -> fix speak mapping/punctuation, re-render flagged lines',
              flush=True)
        return 1
    print('PRON CHECK: PASS (all script words heard correctly)', flush=True)
    if lowconf:
        print(f'note: {len(lowconf)} low-confidence segments listed above for a human spot-check',
              flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
