#!/usr/bin/env python3
"""Build site/index.html from extracted slide JSON + CSS/JS assets."""
import json, os, html as H

BASE = '/home/user/portfolio-presentation'
DATA = json.load(open(f'{BASE}/extracted/extracted-slides.json'))

def css():
    out = ''
    for f in ['tokens.css','base.css','components.css','templates.css']:
        out += open(f'{BASE}/site/styles/{f}').read() + '\n'
    return out

def js():
    out = ''
    for f in ['deck.js','lazy-media.js']:
        out += open(f'{BASE}/site/js/{f}').read() + '\n'
    return out

def h(t): return H.escape(str(t)) if t else ''

def img(image, lazy=True):
    p = image['path']
    attr = f'data-src="{h(p)}"' if lazy else f'src="{h(p)}"'
    return f'<figure class="media-frame"><img {attr} alt="" loading="lazy"></figure>'

def split_lb(text):
    for sep in ['\n', ' | ']:
        if sep in text:
            i = text.index(sep)
            return text[:i].strip(), text[i+len(sep):].strip()
    return text.strip(), ''

def is_page_num(t, n):
    return t.strip() in (str(n), f'{n:02d}')

def pills_html(items):
    return '<div class="pill-row">' + ''.join(f'<span class="pill pill--goal reveal">{h(i)}</span>' for i in items) + '</div>'


# ── Slide-to-template mapping ──
TMAP = {
    1:'cover', 2:'hero', 85:'hero',
    3:'cards', 6:'cards', 7:'cards', 9:'cards', 12:'cards',
    13:'cards', 14:'cards', 15:'cards',
    4:'stats', 8:'timeline',
    10:'trans', 11:'trans', 32:'trans', 33:'trans',
    34:'caseintro', 41:'caseintro', 47:'caseintro', 53:'caseintro',
    58:'caseintro', 64:'caseintro', 70:'caseintro', 75:'caseintro', 80:'caseintro',
    37:'fromto', 44:'fromto', 50:'fromto', 56:'fromto',
    86:'closing',
}
GALLERIES = {5,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,40,52,62,63,68,69,74,79,84}

def get_template(s):
    n = s['number']
    if n in TMAP: return TMAP[n]
    if n in GALLERIES: return 'gallery'
    return 'casebody'

def theme(tpl):
    if tpl in ('cover',): return 'light'
    if tpl in ('cards','stats','timeline') : return 'paper'
    return 'dark'

# ── Template: cover (slide 1) ──
def render_cover(s):
    c = [x['content'] for x in s['content']]
    # c: [PORTFOLIO, Joe Thomas, role, disciplines1, disciplines2, contact]
    eyebrow = h(c[0]) if len(c)>0 else ''
    name = h(c[1]) if len(c)>1 else ''
    role = h(c[2]) if len(c)>2 else ''
    discs = []
    if len(c)>3: discs += [d.strip() for d in c[3].split('·')]
    if len(c)>4: discs += [d.strip() for d in c[4].split('·')]
    contact = h(c[5]) if len(c)>5 else ''
    disc_html = ''.join(f'<div class="reveal">{h(d)}</div>' for d in discs if d)
    return f'''<section class="slide t-cover" data-slide="1" data-theme="light">
  <div class="t-cover__top">
    <div class="t-cover__eyebrow reveal">{eyebrow}</div>
    <h1 class="t-cover__hero reveal">{name}</h1>
    <p class="t-cover__role reveal">{role}</p>
    <div class="t-cover__accent-bar"></div>
  </div>
  <div class="t-cover__bottom">
    <div class="t-cover__disciplines">{disc_html}</div>
    <div class="t-cover__contact reveal">{contact}</div>
  </div>
  <footer class="footer-bar"><span>Joseph S. Thomas <span class="footer-bar__dot"></span> Franklin, TN</span><span class="footer-bar__num">01 / 86</span></footer>
</section>'''


# ── Template: hero intro (slides 2, 85) ──
def render_hero(s):
    n = s['number']
    c = [x['content'] for x in s['content']]
    imgs = s['images']
    img_html = img(imgs[0], lazy=(n!=1)) if imgs else ''
    # Find bio (longest text block)
    bio = max(c, key=len) if c else ''
    name = c[0] if c else ''
    # Categorize all content
    greeting = ''
    role_text = ''
    contact_items = []
    other_text = []
    for x in c:
        if is_page_num(x.strip(), n): continue
        if x == name or x == bio: continue
        if x.startswith("HELLO") or x.startswith("YOU MADE"): greeting = x
        elif 'Content Strategy' in x and len(x) < 60: role_text = x
        elif len(x) < 40: contact_items.append(x)
        else: other_text.append(x)
    contact_html = ' <span class="footer-bar__dot"></span> '.join(h(x) for x in contact_items[:4])
    other_html = ''.join(f'<p class="reveal" style="color:var(--ink-inv-mute);font-size:var(--t-body)">{h(x)}</p>' for x in other_text if x != bio)
    return f'''<section class="slide t-hero-intro" data-slide="{n}" data-theme="dark">
  <div class="t-hero-intro__text">
    <div class="t-hero-intro__name reveal">{h(name)}</div>
    {f'<h2 class="t-hero-intro__greeting reveal">{h(greeting)}</h2>' if greeting else ''}
    {f'<p class="t-hero-intro__role reveal">{h(role_text)}</p>' if role_text else ''}
    <div class="t-hero-intro__bio reveal">{h(bio)}</div>
    {other_html}
    <div class="t-hero-intro__contact reveal">{contact_html}</div>
  </div>
  {f'<div class="t-hero-intro__portrait">{img_html}</div>' if img_html else ''}
  <footer class="footer-bar"><span class="footer-bar__num">{n:02d} / 86</span></footer>
</section>'''

# ── Template: narrative cards (slides 3,6,7,9,12-15) ──
def render_cards(s):
    n = s['number']
    c = [x['content'] for x in s['content']]
    imgs = s['images']
    # First item = eyebrow, second = subtitle
    eyebrow = h(c[0]) if c else ''
    subtitle = h(c[1]) if len(c)>1 else ''
    # Parse numbered cards: look for short numeric strings followed by label + desc
    cards = []
    i = 2
    while i < len(c):
        txt = c[i].strip()
        if is_page_num(txt, n):
            i += 1; continue
        # Check if this is a number (1-2 chars, digits)
        if len(txt) <= 3 and (txt.isdigit() or txt in ('BEYOND',)):
            num = txt
            label = h(c[i+1]) if i+1 < len(c) else ''
            desc = h(c[i+2]) if i+2 < len(c) else ''
            cards.append(f'<article class="num-card reveal"><span class="num-card__n">{h(num)}</span><h3 class="num-card__label">{label}</h3><p class="num-card__desc">{desc}</p></article>')
            i += 3
        else:
            # Non-numbered block — could be a section label or long text
            label, body = split_lb(txt)
            if body:
                cards.append(f'<article class="num-card reveal"><h3 class="num-card__label">{h(label)}</h3><p class="num-card__desc">{h(body)}</p></article>')
            else:
                cards.append(f'<article class="num-card reveal"><h3 class="num-card__label">{h(txt)}</h3></article>')
            i += 1
    cnt = len(cards)
    cols = 3 if cnt >= 6 else 2 if cnt >= 4 else 1
    img_html = ''.join(img(im) for im in imgs)
    return f'''<section class="slide t-narrative" data-slide="{n}" data-theme="paper">
  <div class="t-narrative__intro">
    <div class="section-label reveal">{eyebrow}</div>
    <h2 class="t-narrative__title reveal">{subtitle}</h2>
    {f'<div style="display:flex;flex-direction:column;gap:var(--gap-sm)">{img_html}</div>' if img_html else ''}
  </div>
  <div class="t-narrative__cards" data-count="{cnt}">{chr(10).join(cards)}</div>
  <footer class="footer-bar"><span class="footer-bar__num">{n:02d} / 86</span></footer>
</section>'''


# ── Template: stat grid (slide 4) ──
def render_stats(s):
    n = s['number']
    c = [x['content'] for x in s['content']]
    eyebrow = h(c[0]) if c else ''
    subtitle = h(c[1]) if len(c)>1 else ''
    cards = []
    i = 2
    while i < len(c):
        txt = c[i].strip()
        if is_page_num(txt, n): i+=1; continue
        # Stat cards: short big number + next item is caption
        if len(txt) <= 8 and i+1 < len(c) and not is_page_num(c[i+1].strip(), n):
            big = txt; cap = c[i+1]
            cards.append(f'<article class="stat-card reveal"><span class="stat-card__big">{h(big)}</span><p class="stat-card__cap">{h(cap)}</p></article>')
            i += 2
        else:
            i += 1
    cnt = len(cards)
    return f'''<section class="slide t-stats" data-slide="{n}" data-theme="paper">
  <div class="t-stats__head">
    <div class="section-label reveal">{eyebrow}</div>
    <h2 class="t-narrative__title reveal">{subtitle}</h2>
  </div>
  <div class="t-stats__grid" data-count="{cnt}">{chr(10).join(cards)}</div>
  <footer class="footer-bar"><span class="footer-bar__num">{n:02d} / 86</span></footer>
</section>'''

# ── Template: timeline (slide 8) ──
def render_timeline(s):
    n = s['number']
    c = [x['content'] for x in s['content']]
    eyebrow = h(c[0]) if c else ''
    subtitle = h(c[1]) if len(c)>1 else ''
    items = []
    i = 2
    while i < len(c):
        txt = c[i].strip()
        if is_page_num(txt, n): i+=1; continue
        # Timeline pattern: years, company, role, description
        if '–' in txt or '–' in txt or 'career' in txt.lower():
            years = txt
            company = c[i+1] if i+1<len(c) else ''
            role_t = c[i+2] if i+2<len(c) else ''
            desc = c[i+3] if i+3<len(c) else ''
            items.append(f'''<div class="t-timeline__item reveal">
  <span class="num-oval">{len(items)+1:02d}</span>
  <div class="t-timeline__body">
    <span class="t-timeline__years">{h(years)}</span>
    <div><div class="t-timeline__company">{h(company)}</div><div class="t-timeline__role">{h(role_t)}</div></div>
    <p class="t-timeline__note">{h(desc)}</p>
  </div>
</div>''')
            i += 4
        else:
            i += 1
    return f'''<section class="slide t-timeline" data-slide="{n}" data-theme="paper">
  <div class="t-timeline__head">
    <div class="section-label reveal">{eyebrow}</div>
    <h2 class="t-narrative__title reveal">{subtitle}</h2>
  </div>
  <div class="t-timeline__rail">{chr(10).join(items)}</div>
  <footer class="footer-bar"><span class="footer-bar__num">{n:02d} / 86</span></footer>
</section>'''


# ── Template: case intro (slides 34,41,47,53,58,64,70,75,80) ──
def render_caseintro(s):
    n = s['number']
    c = [x['content'] for x in s['content']]
    imgs = s['images']
    label = h(c[0]) if c else 'CASE STUDY'
    client = h(c[1]) if len(c)>1 else ''
    tagline = h(c[2]) if len(c)>2 else ''
    desc = h(c[3]) if len(c)>3 else ''
    services = c[4] if len(c)>4 else ''
    svc_pills = pills_html([x.strip() for x in services.split('·') if x.strip()]) if services else ''
    img_html = f'<div class="t-case-intro__image">{img(imgs[0])}</div>' if imgs else ''
    return f'''<section class="slide t-case-intro" data-slide="{n}" data-theme="dark">
  <div class="t-case-intro__meta">
    <div class="t-case-intro__label reveal">{label}</div>
    <h2 class="t-case-intro__client reveal">{client}</h2>
    <p class="t-case-intro__tagline reveal">{tagline}</p>
    <p class="reveal" style="color:var(--ink-inv-mute);font-size:var(--t-small);max-width:45ch">{desc}</p>
    {svc_pills}
  </div>
  {img_html}
  <footer class="footer-bar"><span class="footer-bar__num">{n:02d} / 86</span></footer>
</section>'''

# ── Template: case body (default for case study content slides) ──
def render_casebody(s):
    n = s['number']
    c = [x['content'] for x in s['content']]
    imgs = s['images']
    # Try to split first block into label + body
    blocks = []
    goals = []
    i = 0
    while i < len(c):
        txt = c[i]
        if is_page_num(txt.strip(), n): i+=1; continue
        if txt.strip() == 'GOALS':
            # Render the GOALS label + collect goal pills
            blocks.append(('text', 'GOALS', ''))
            i += 1
            while i < len(c) and len(c[i]) < 50 and not is_page_num(c[i].strip(), n):
                goals.append(c[i])
                i += 1
            continue
        label, body = split_lb(txt)
        if body and len(label) < 40:
            blocks.append(('labeled', label, body))
        elif len(txt) > 80:
            blocks.append(('body', '', txt))
        elif len(txt) < 6 and txt.strip() in ('+','%','M','K','x','PAGE'):
            blocks.append(('stat_sym', txt, ''))
        else:
            blocks.append(('text', txt, ''))
        i += 1
    # Build HTML
    text_parts = []
    for kind, a, b in blocks:
        if kind == 'labeled':
            text_parts.append(f'<div class="section-label reveal">{h(a)}</div>')
            text_parts.append(f'<p class="reveal" style="line-height:1.65;max-width:60ch;white-space:pre-line">{h(b)}</p>')
        elif kind == 'body':
            text_parts.append(f'<p class="reveal" style="line-height:1.65;max-width:60ch;white-space:pre-line">{h(b or a)}</p>')
        elif kind == 'stat_sym':
            text_parts.append(f'<span class="reveal" style="font-family:var(--font-display);font-size:var(--t-stat-md);color:var(--blue-400);font-weight:700">{h(a)}</span>')
        elif kind == 'text':
            text_parts.append(f'<p class="reveal" style="font-size:var(--t-small);color:var(--ink-inv-mute)">{h(a)}</p>')
    if goals:
        text_parts.append(pills_html(goals))
    text_html = '\n'.join(text_parts)
    img_html = ''.join(img(im) for im in imgs)
    has_imgs = bool(imgs)
    tpl_class = 't-approach' if has_imgs else 't-situation'
    return f'''<section class="slide {tpl_class}" data-slide="{n}" data-theme="dark">
  <div class="{tpl_class}__text" style="{'max-width:55ch' if has_imgs else 'max-width:70ch'}">{text_html}</div>
  {f'<div style="display:grid;gap:var(--gap-md);grid-template-columns:repeat(auto-fit,minmax(200px,1fr));align-self:center">{img_html}</div>' if has_imgs else ''}
  <footer class="footer-bar"><span class="footer-bar__num">{n:02d} / 86</span></footer>
</section>'''


# ── Template: from/to transformation (slides 37,44,50,56) ──
def render_fromto(s):
    n = s['number']
    c = [x['content'] for x in s['content']]
    imgs = s['images']
    heading = h(c[0]) if c else ''
    from_text = h(c[1]) if len(c)>1 else ''
    to_text = h(c[2]) if len(c)>2 else ''
    from_label = h(c[3]) if len(c)>3 else 'FROM'
    to_label = h(c[4]) if len(c)>4 else 'TO'
    img_html = ''.join(img(im) for im in imgs)
    return f'''<section class="slide" data-slide="{n}" data-theme="dark" style="padding:var(--pad-slide);display:flex;flex-direction:column;gap:var(--gap-lg);justify-content:center">
  <h2 class="reveal" style="font-family:var(--font-display);font-size:var(--t-h2);font-style:italic;color:var(--blue-400);max-width:50ch">{heading}</h2>
  <div class="ft-grid reveal">
    <div class="ft-panel ft-panel--from"><div class="ft-panel__label">{from_label}</div><p style="font-size:var(--t-small);line-height:1.5">{from_text}</p></div>
    <span class="ft-arrow">→</span>
    <div class="ft-panel ft-panel--to"><div class="ft-panel__label">{to_label}</div><p style="font-size:var(--t-small);line-height:1.5">{to_text}</p></div>
  </div>
  {f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:var(--gap-sm)">{img_html}</div>' if img_html else ''}
  <footer class="footer-bar"><span class="footer-bar__num">{n:02d} / 86</span></footer>
</section>'''

# ── Template: gallery (image-heavy slides) ──
def render_gallery(s):
    n = s['number']
    c = [x['content'] for x in s['content']]
    imgs = s['images']
    # Find heading/caption (skip page numbers)
    texts = [x for x in c if not is_page_num(x.strip(), n)]
    heading = ''
    caption = ''
    title_text = s.get('title', '')
    if title_text and not is_page_num(title_text.strip(), n):
        heading = title_text
    if not heading and texts:
        heading = texts[0]
        caption = texts[1] if len(texts)>1 else ''
    elif texts:
        caption = texts[0]
    # Render ALL non-heading text blocks so nothing is dropped
    all_text_html = ''
    for t in texts:
        if t == heading or t == caption:
            continue
        if t.startswith('OUTPUT:'):
            all_text_html += f'<p class="reveal" style="font-size:var(--t-meta);color:var(--blue-400);text-transform:uppercase;letter-spacing:0.15em">{h(t)}</p>'
        elif len(t) > 80:
            all_text_html += f'<p class="reveal" style="font-size:var(--t-small);color:var(--ink-inv-mute);max-width:65ch;line-height:1.55">{h(t)}</p>'
        else:
            all_text_html += f'<p class="reveal" style="font-size:var(--t-small);color:var(--ink-inv-mute)">{h(t)}</p>'
    cnt = len(imgs)
    img_html = ''.join(img(im) for im in imgs)
    head_html = ''
    if heading:
        label, body = split_lb(heading) if '\n' in heading else (heading, '')
        head_html = f'<div class="t-gallery__head"><h2 class="t-gallery__heading reveal">{h(label)}</h2></div>'
    if caption:
        head_html += f'<p class="t-gallery__caption reveal">{h(caption)}</p>'
    return f'''<section class="slide t-gallery" data-slide="{n}" data-theme="dark">
  {head_html}
  {all_text_html}
  <div class="t-gallery__grid" data-count="{cnt}">{img_html}</div>
  <footer class="footer-bar"><span class="footer-bar__num">{n:02d} / 86</span></footer>
</section>'''

# ── Template: transition (slides 10,11,32,33) ──
def render_trans(s):
    n = s['number']
    c = [x['content'] for x in s['content']]
    title_text = s.get('title', '')
    texts = [x for x in c if not is_page_num(x.strip(), n)]
    part = ''
    title = ''
    body = ''
    if title_text and len(title_text) > 10:
        body = title_text
    for t in texts:
        if t.startswith('PART'): part = t
        elif len(t) < 30 and not part: title = t
        elif len(t) < 30: title = t
        else: body = t
    return f'''<section class="slide t-transition" data-slide="{n}" data-theme="dark">
  {f'<div class="t-transition__part reveal">{h(part)}</div>' if part else ''}
  {f'<h2 class="t-transition__title reveal">{h(title)}</h2>' if title else ''}
  {f'<p class="t-transition__body reveal">{h(body)}</p>' if body else ''}
  <footer class="footer-bar"><span class="footer-bar__num">{n:02d} / 86</span></footer>
</section>'''

# ── Template: closing (slide 86) ──
def render_closing(s):
    n = s['number']
    c = [x['content'] for x in s['content']]
    text = c[0] if c else 'Thank You.'
    return f'''<section class="slide t-closing" data-slide="{n}" data-theme="dark">
  <h2 class="t-closing__title reveal">{h(text)}</h2>
  <footer class="footer-bar"><span class="footer-bar__num">{n:02d} / 86</span></footer>
</section>'''


# ── Dispatcher ──
RENDERERS = {
    'cover': render_cover, 'hero': render_hero, 'cards': render_cards,
    'stats': render_stats, 'timeline': render_timeline,
    'caseintro': render_caseintro, 'casebody': render_casebody,
    'fromto': render_fromto, 'gallery': render_gallery,
    'trans': render_trans, 'closing': render_closing,
}

def render_slide(s):
    tpl = get_template(s)
    fn = RENDERERS.get(tpl, render_casebody)
    try:
        return fn(s)
    except Exception as e:
        n = s['number']
        return f'<section class="slide t-transition" data-slide="{n}" data-theme="dark"><p style="color:red">Slide {n}: render error: {h(str(e))}</p></section>'

# ── Main: assemble index.html ──
def build():
    all_css = css()
    all_js = js()
    slides_html = '\n\n'.join(render_slide(s) for s in DATA)

    reveal_js = '''
    // Scroll-triggered reveal animations
    const revealObs = new IntersectionObserver((entries) => {
      entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
    }, { threshold: 0.15 });
    document.querySelectorAll('.slide').forEach(s => revealObs.observe(s));
    '''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Joe Thomas — Portfolio</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
/* === REVEAL ANIMATIONS === */
.reveal {{ opacity: 0; transform: translateY(24px); transition: opacity 0.7s cubic-bezier(0.2,0.8,0.2,1), transform 0.7s cubic-bezier(0.2,0.8,0.2,1); }}
.slide.visible .reveal {{ opacity: 1; transform: translateY(0); }}
.slide.visible .reveal:nth-child(2) {{ transition-delay: 0.08s; }}
.slide.visible .reveal:nth-child(3) {{ transition-delay: 0.16s; }}
.slide.visible .reveal:nth-child(4) {{ transition-delay: 0.24s; }}
.slide.visible .reveal:nth-child(5) {{ transition-delay: 0.32s; }}
.slide.visible .reveal:nth-child(6) {{ transition-delay: 0.4s; }}
.slide.visible .reveal:nth-child(7) {{ transition-delay: 0.48s; }}
.slide.visible .reveal:nth-child(8) {{ transition-delay: 0.56s; }}

/* Slide-from-left variant */
.reveal-left {{ opacity: 0; transform: translateX(-40px); transition: opacity 0.7s cubic-bezier(0.2,0.8,0.2,1), transform 0.7s cubic-bezier(0.2,0.8,0.2,1); }}
.slide.visible .reveal-left {{ opacity: 1; transform: translateX(0); }}

/* Scale-in variant for cards */
.reveal-scale {{ opacity: 0; transform: scale(0.92); transition: opacity 0.6s cubic-bezier(0.2,0.8,0.2,1), transform 0.6s cubic-bezier(0.2,0.8,0.2,1); }}
.slide.visible .reveal-scale {{ opacity: 1; transform: scale(1); }}

/* Stagger for grid children (stat cards, num cards, gallery images) */
.slide.visible .num-card:nth-child(1),
.slide.visible .stat-card:nth-child(1),
.slide.visible .media-frame:nth-child(1) {{ transition-delay: 0.1s; }}
.slide.visible .num-card:nth-child(2),
.slide.visible .stat-card:nth-child(2),
.slide.visible .media-frame:nth-child(2) {{ transition-delay: 0.18s; }}
.slide.visible .num-card:nth-child(3),
.slide.visible .stat-card:nth-child(3),
.slide.visible .media-frame:nth-child(3) {{ transition-delay: 0.26s; }}
.slide.visible .num-card:nth-child(4),
.slide.visible .stat-card:nth-child(4),
.slide.visible .media-frame:nth-child(4) {{ transition-delay: 0.34s; }}
.slide.visible .num-card:nth-child(5),
.slide.visible .stat-card:nth-child(5),
.slide.visible .media-frame:nth-child(5) {{ transition-delay: 0.42s; }}
.slide.visible .num-card:nth-child(6),
.slide.visible .stat-card:nth-child(6),
.slide.visible .media-frame:nth-child(6) {{ transition-delay: 0.5s; }}
.num-card, .stat-card {{ opacity: 0; transform: translateY(20px) scale(0.96); transition: opacity 0.6s cubic-bezier(0.2,0.8,0.2,1), transform 0.6s cubic-bezier(0.2,0.8,0.2,1); }}
.slide.visible .num-card, .slide.visible .stat-card {{ opacity: 1; transform: translateY(0) scale(1); }}
.media-frame {{ opacity: 0; transform: scale(0.94); transition: opacity 0.5s cubic-bezier(0.2,0.8,0.2,1), transform 0.5s cubic-bezier(0.2,0.8,0.2,1); }}
.slide.visible .media-frame {{ opacity: 1; transform: scale(1); }}

/* Accent bar animation */
@keyframes barGrow {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
.slide.visible .t-cover__accent-bar {{ animation: barGrow 0.8s cubic-bezier(0.2,0.8,0.2,1) 0.6s both; transform-origin: left; }}
.slide.visible .accent-stripe {{ animation: barGrow 0.6s cubic-bezier(0.2,0.8,0.2,1) 0.4s both; transform-origin: left; }}

/* Section label line animation */
.section-label::before {{ transform: scaleX(0); transform-origin: left; transition: transform 0.5s cubic-bezier(0.2,0.8,0.2,1) 0.3s; }}
.slide.visible .section-label::before {{ transform: scaleX(1); }}

/* Pill hover lift */
.pill:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}

/* FROM/TO panel entrance */
.ft-panel--from {{ opacity: 0; transform: translateX(-30px); transition: opacity 0.6s ease 0.2s, transform 0.6s ease 0.2s; }}
.ft-panel--to {{ opacity: 0; transform: translateX(30px); transition: opacity 0.6s ease 0.4s, transform 0.6s ease 0.4s; }}
.ft-arrow {{ opacity: 0; transition: opacity 0.4s ease 0.5s; }}
.slide.visible .ft-panel--from, .slide.visible .ft-panel--to {{ opacity: 1; transform: translateX(0); }}
.slide.visible .ft-arrow {{ opacity: 0.8; }}

/* Transition slide — hero text entrance */
.t-transition__title {{ opacity: 0; transform: translateY(40px); transition: opacity 1s cubic-bezier(0.2,0.8,0.2,1) 0.2s, transform 1s cubic-bezier(0.2,0.8,0.2,1) 0.2s; }}
.slide.visible .t-transition__title {{ opacity: 1; transform: translateY(0); }}

/* Closing slide — scale in */
.t-closing__title {{ opacity: 0; transform: scale(0.85); transition: opacity 1.2s cubic-bezier(0.2,0.8,0.2,1), transform 1.2s cubic-bezier(0.2,0.8,0.2,1); }}
.slide.visible .t-closing__title {{ opacity: 1; transform: scale(1); }}

/* === PROGRESS BAR === */
.deck-progress {{ position: fixed; top: 0; left: 0; width: 100%; height: 3px; z-index: 100; pointer-events: none; }}
.deck-progress__bar {{ height: 100%; width: 0; background: linear-gradient(90deg, var(--blue-500), var(--blue-400)); transition: width 0.4s cubic-bezier(0.2,0.8,0.2,1); box-shadow: 0 0 8px rgba(74,144,226,0.5); }}
.deck-counter {{ position: fixed; bottom: 1rem; right: 1.5rem; font-family: var(--font-display); font-style: italic; font-size: 0.85rem; color: var(--ink-inv-soft); z-index: 100; pointer-events: none; letter-spacing: 0.05em; }}
{all_css}
</style>
</head>
<body>

<div class="deck-progress"><div class="deck-progress__bar"></div></div>
<div class="deck-counter"></div>

{slides_html}

<script>
{all_js}
{reveal_js}
</script>
</body>
</html>'''

    out = f'{BASE}/site/index.html'
    with open(out, 'w') as f:
        f.write(html)
    print(f'Built {out} ({len(DATA)} slides, {len(html)//1024} KB)')

if __name__ == '__main__':
    build()
