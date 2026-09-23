import json
import os
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

USER = 'Hammad7128'

def api(path):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'profile-stats'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    with urlopen(Request('https://api.github.com' + path, headers=headers), timeout=30) as response:
        return json.load(response)

def card(title, subtitle, body):
    date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="500" height="280" viewBox="0 0 500 280" role="img" aria-label="{escape(title)}">
    <rect width="500" height="280" rx="16" fill="#101010"/>
    <rect x="1" y="1" width="498" height="278" rx="15" fill="none" stroke="#292929"/>
    <g font-family="Arial, sans-serif"><text x="26" y="40" fill="#dedede" font-size="22" font-weight="700">{escape(title)}</text>
    <text x="26" y="64" fill="#a0a0a0" font-size="12">{escape(subtitle)}</text>
    {body}<text x="26" y="259" fill="#a0a0a0" font-size="11">Public GitHub data · Updated {date} UTC</text></g></svg>'''

def main():
    user = api('/users/' + USER)
    repos = []
    page = 1
    while True:
        batch = api(f'/users/{USER}/repos?type=owner&per_page=100&page={page}')
        repos.extend(r for r in batch if not r.get('private'))
        if len(batch) < 100:
            break
        page += 1
    own = [r for r in repos if not r['fork']]
    values = [('Public repositories', len(repos)), ('Stars earned', sum(r['stargazers_count'] for r in own)), ('Forks of my projects', sum(r['forks_count'] for r in own)), ('Followers', user['followers'])]
    body = ''
    for i, (label, value) in enumerate(values):
        y = 104 + i * 36
        body += f'<circle cx="29" cy="{y-5}" r="3" fill="#0f8065"/><text x="43" y="{y}" fill="#c7c7c7" font-size="15">{label}</text><text x="467" y="{y}" text-anchor="end" fill="#dedede" font-size="20" font-weight="700">{value}</text>'
    stats = card('GitHub overview', '@' + USER + ' · Stars and forks exclude forked repositories', body)
    languages = Counter()
    for repo in own:
        languages.update(api('/repos/' + repo['full_name'] + '/languages'))
    top = languages.most_common(5)
    total = sum(languages.values())
    body = ''
    for i, (language, size) in enumerate(top):
        y = 90 + i * 30
        percent = size / total * 100
        body += f'<text x="26" y="{y}" fill="#c7c7c7" font-size="13">{escape(language)}</text><text x="474" y="{y}" text-anchor="end" fill="#dedede" font-size="13">{percent:.1f}%</text><rect x="26" y="{y+6}" width="448" height="5" rx="2" fill="#252525"/><rect x="26" y="{y+6}" width="{448*percent/100:.2f}" height="5" rx="2" fill="#0f8065"/>'
    if not top:
        body = '<text x="26" y="120" fill="#c7c7c7" font-size="15">No language data yet.</text>'
    langs = card('Most used languages', 'Share of code bytes · Public, non-fork repositories', body)
    output = Path('assets')
    output.mkdir(exist_ok=True)
    for name, content in [('github-stats.svg', stats), ('github-languages.svg', langs)]:
        (output / name).write_text(content, encoding='utf-8')

if __name__ == '__main__':
    main()
