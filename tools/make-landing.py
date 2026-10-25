#!/usr/bin/env python3
"""Build a standalone validation (landing) preview from a night's brief.

  tools/make-landing.py --brief briefs/2026-10-25.md --pain p-073 --name Cardbox --date 2026-10-25 --out site/2026-10-25-cardbox/landing

Reads the brief's "## Validation page proposal" section (headline quote, subhead, benefits, price, flow, buttons, ad angle)
and the idea's "Cheapest test" paragraph, fills templates/landing/index.html and writes <out>/index.html.
The page is fully self-contained: no external fonts, scripts, images or requests (CSP default-src 'none'), noindex, and its
buttons only record a click in localStorage and say "Not launched yet". Exits 2 if the brief has no usable proposal.
"""
import argparse, html, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

def inline(s):
    s = html.escape(s.strip(), quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<!\w)\*(?!\s)(.+?)(?<!\s)\*(?!\w)', r'\1', s)
    return re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', s)

def plain(s):
    return re.sub(r'<[^>]+>', '', inline(s))

def section(md, start_re, level='## '):
    m = re.search(start_re, md, re.M)
    if not m: return ''
    rest = md[m.end():]
    end = re.search(r'^' + re.escape(level) + r'(?!#)', rest, re.M)
    return rest[:end.start()] if end else rest

def block(sec, label):
    m = re.search(r'^\*\*' + label + r'[^\n]*\n((?:\s*(?:\d+\.|-)\s.*\n?)+)', sec, re.M | re.I)
    return [re.sub(r'^\s*(?:\d+\.|-)\s+', '', l) for l in m.group(1).splitlines() if l.strip()] if m else []

def field(sec, label):
    m = re.search(r'\*\*' + label + r'[^*]*:\*\*\s*(.+)', sec, re.I)
    return m.group(1).strip() if m else ''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--brief', required=True); ap.add_argument('--pain', required=True); ap.add_argument('--name', required=True)
    ap.add_argument('--date', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--template', default=str(HERE / 'templates' / 'landing' / 'index.html'))
    a = ap.parse_args()
    md = Path(a.brief).read_text()
    prop = section(md, r'^## Validation page proposal \(winner ' + re.escape(a.pain) + r'\b.*$')
    if not prop:
        print(f'no "Validation page proposal" for {a.pain} in {a.brief}', file=sys.stderr); sys.exit(2)
    idea = section(md, r'^## Idea \d+[^\n]*\(' + re.escape(a.pain) + r'\)\s*$')

    hm = re.search(r'\*\*Headline[^\n]*\n>\s*(.+)', prop)
    headline = (hm.group(1) if hm else field(prop, 'Headline')).strip().strip('"“”')
    subhead = field(prop, 'Subhead')
    price = re.sub(r',?\s*\(?estimate\)?\.?$', '', field(prop, 'Price'), flags=re.I).rstrip('. ')
    benefits = []
    for l in block(prop, r'\d* ?benefits'):
        m = re.match(r'\*\*(.+?)\*\*\s*(.*)', l)
        benefits.append((m.group(1).rstrip('.'), m.group(2)) if m else (l, ''))
    steps = block(prop, r'Flow')
    btn = lambda lab: (re.search(lab + r'[^*\n]*\*\*"?(.+?)"?\*\*', prop, re.I) or [None, ''])[1].strip('"“”')
    main_btn, soft_btn, note = btn(r'Main:'), btn(r'Softer link:'), btn(r'Note under the buttons:')
    ad = field(prop, 'Suggested ad angle')
    test = (re.search(r'^### Cheapest test[^\n]*\n(.+?)(?=\n###|\Z)', idea, re.M | re.S) or [None, ''])[1].strip()
    pitch = (re.search(r'^### Name and pitch\n\*\*[^*]+\*\*:?\s*(.+)', idea, re.M) or [None, ''])[1]
    final = pitch.split('. ')[0].rstrip('.') if pitch else subhead
    final = final[:1].upper() + final[1:]
    src = ''
    qm = re.search(re.escape(headline[:60]) + r'.*?\(\[([^\]]+)\]', idea)
    if qm: src = qm.group(1)
    if not (headline and main_btn):
        print('proposal is missing a headline or main button', file=sys.stderr); sys.exit(2)

    chips = []
    for t, body in benefits:
        for part in re.split(r',\s*|\.\s+', t):
            part = part.strip().rstrip('.')
            if part and len(chips) < 5: chips.append(part[:1].upper() + part[1:])
        if re.search(r'export', body, re.I) and 'Free export, anytime' not in chips: chips.append('Free export, anytime')
    pm = re.match(r'\$[\d.]+/(?:month|mo|year)', price)
    promises = ''.join(f'<span>{html.escape(c)}</span>' for c in chips) + (f'<span class="o">{html.escape(pm.group(0))}</span>' if pm else '')
    buttons = f'<button type="button" class="btn main" data-cta="main">{html.escape(main_btn)}</button>'
    if soft_btn: buttons += f'<button type="button" class="btn soft" data-cta="soft">{html.escape(soft_btn)}</button>'
    notes = ''.join(f'<p>{x}</p>' for x in [
        f'<b>Ad angle:</b> {inline(ad)}' if ad else '',
        f'<b>Test:</b> {inline(test)}' if test else '',
        f'<b>Source:</b> brief {html.escape(a.date)}, pain {html.escape(a.pain)}. Prices are estimates. The real test page would add a fake checkout and a waitlist; this preview deliberately has neither.',
    ] if x)
    vals = {
        'name': html.escape(a.name), 'title': html.escape(plain(subhead)[:70]), 'key': re.sub(r'[^a-z0-9-]', '', f'{a.date}-{a.name.lower()}'),
        'eyebrow': 'From a real review' if src else html.escape(a.name), 'headline': f'<span class="q">“</span>{html.escape(headline)}<span class="q">”</span>',
        'who': f'<p class="who">A real user complaint ({html.escape(src)}), quoted as written</p>' if src else '',
        'subhead': inline(subhead), 'price': f'<b>{inline(price.split(" (")[0])}</b>' + (f' · {inline(price[len(price.split(" (")[0]):].strip(" ()"))}' if ' (' in price else '') if price else '',
        'note': inline(note), 'buttons': buttons, 'steps': ''.join(f'<li><span>{inline(s)}</span></li>' for s in steps),
        'promises': promises, 'benefits': ''.join(f'<div class="card"><div class="n">{i}</div><h4>{inline(t)}</h4><p>{inline(b)}</p></div>' for i, (t, b) in enumerate(benefits, 1)),
        'final': inline(final), 'notes': notes, 'date': html.escape(a.date),
    }
    out = Path(a.template).read_text()
    for k, v in vals.items(): out = out.replace('{{' + k + '}}', v)
    left = re.findall(r'\{\{\w+\}\}', out)
    if left: print('unfilled placeholders: ' + ', '.join(left), file=sys.stderr); sys.exit(1)
    if re.search(r'(src|href)=["\']https?:|@import|url\(\s*["\']?https?:', out):
        print('refusing: external reference in landing output', file=sys.stderr); sys.exit(1)
    d = Path(a.out); d.mkdir(parents=True, exist_ok=True); (d / 'index.html').write_text(out)
    print(json.dumps({'out': str(d / 'index.html'), 'headline': headline[:60], 'benefits': len(benefits), 'steps': len(steps), 'main': main_btn}))

if __name__ == '__main__':
    main()
