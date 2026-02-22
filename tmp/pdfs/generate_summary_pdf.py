from pathlib import Path

OUT = Path('output/pdf/app-summary-one-page.pdf')
OUT.parent.mkdir(parents=True, exist_ok=True)

lines = [
    (16, 'AgeCalc App Summary (One Page)'),
    (10, ''),
    (12, 'What It Is'),
    (10, 'AgeCalc is a Flask web app for age-related calculators, mini-games, and blog pages.'),
    (10, 'It serves server-rendered pages with Jinja templates plus client-side JavaScript tools.'),
    (10, ''),
    (12, 'Who It Is For'),
    (10, 'Primary persona: Not found in repo (no explicit persona document).'),
    (10, 'Inferred from templates/content: Korean-language users who need practical age calculations.'),
    (10, ''),
    (12, 'What It Does (Key Features)'),
    (10, '- Calculates international age from date input (solar and lunar input support).'),
    (10, '- Provides pet age conversion pages for dogs and cats.'),
    (10, '- Provides baby month-age and parent-child age relation calculators.'),
    (10, '- Includes mini-games (snake, tic-tac-toe, rock-paper-scissors, number guess).'),
    (10, '- Exposes blog list/detail pages with pagination for published posts.'),
    (10, '- Tracks snake scores via a JSON file and returns daily ranking metadata.'),
    (10, '- Adds security headers/CSP and includes analytics/ads integrations in templates.'),
    (10, ''),
    (12, 'How It Works (Repo-Evidenced Architecture)'),
    (10, '- HTTP flow: Browser -> Flask routes in app.py -> Jinja templates/static JS/CSS -> response.'),
    (10, '- Age logic: /age route -> AgeController -> AgeCalculator; lunar input converts via KoreanLunarCalendar.'),
    (10, '- Data layer: SQLAlchemy engine/session in db.py; DATABASE_URL sets DB, default is SQLite data/app.db.'),
    (10, '- Blog domain: models/blog_models.py defines FeedSource, FeedItem, GeneratedPost, PostSource tables.'),
    (10, '- Background ingestion: scripts/rss_blog_scheduler.py fetches RSS/Atom and creates draft/published posts.'),
    (10, '- Snake score service: /snake-score uses file-backed storage (data/snake_scores.json) with thread lock.'),
    (10, ''),
    (12, 'How To Run (Minimal Getting Started)'),
    (10, '1. python3 -m venv .venv && source .venv/bin/activate'),
    (10, '2. pip install -r requirements.txt'),
    (10, '3. Optional DB override: export DATABASE_URL="mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/agecalc?charset=utf8mb4"'),
    (10, '4. python app.py, then open http://localhost:8000'),
    (10, ''),
    (9, 'Source basis: readme.md, app.py, db.py, controllers/age_controller.py, models/blog_models.py, scripts/rss_blog_scheduler.py'),
]


def pdf_escape(s: str) -> str:
    return s.replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')


y = 770
leading = 13
ops = ['BT', '/F1 10 Tf', '1 0 0 1 54 0 Tm']
for size, text in lines:
    if text == '':
        y -= leading
        continue
    ops.append(f'/F1 {size} Tf')
    ops.append(f'1 0 0 1 54 {y} Tm')
    ops.append(f'({pdf_escape(text)}) Tj')
    y -= leading
ops.append('ET')
content = '\n'.join(ops).encode('latin-1', errors='replace')

objects = []

def add_obj(payload: bytes):
    objects.append(payload)

add_obj(b'<< /Type /Catalog /Pages 2 0 R >>')
add_obj(b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>')
add_obj(b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>')
add_obj(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>')
add_obj(f'<< /Length {len(content)} >>\nstream\n'.encode('latin-1') + content + b'\nendstream')

pdf = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
offsets = [0]
for i, obj in enumerate(objects, start=1):
    offsets.append(len(pdf))
    pdf.extend(f'{i} 0 obj\n'.encode('latin-1'))
    pdf.extend(obj)
    pdf.extend(b'\nendobj\n')

xref_pos = len(pdf)
pdf.extend(f'xref\n0 {len(objects)+1}\n'.encode('latin-1'))
pdf.extend(b'0000000000 65535 f \n')
for off in offsets[1:]:
    pdf.extend(f'{off:010d} 00000 n \n'.encode('latin-1'))
pdf.extend(f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n'.encode('latin-1'))

OUT.write_bytes(pdf)
print(str(OUT.resolve()))
