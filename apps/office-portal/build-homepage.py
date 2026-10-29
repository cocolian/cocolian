"""Generate the public landing page. Build dependency: Markdown==3.7."""
from pathlib import Path
from html.parser import HTMLParser
from html import escape
from urllib.parse import urljoin
import markdown
ROOT = Path(__file__).resolve().parent
SOURCE = 'https://github.com/cocolian/online.mirror/blob/main/'
class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.output = []
    def handle_starttag(self, tag, attrs):
        fixed = []
        for name, value in attrs:
            if name in ('href', 'src') and value and not value.startswith(('#', 'https://', 'http://', 'mailto:')):
                base = SOURCE.replace('/blob/', '/tree/') if value.endswith('/') or ('.' not in value.rsplit('/', 1)[-1] and not value.rsplit('/', 1)[-1].isupper()) else SOURCE
                value = urljoin(base, value)
            fixed.append((name, value))
        if tag == 'img': fixed.append(('loading', 'lazy'))
        self.output.append('<' + tag + ''.join(' ' + k + ('="' + escape(v, quote=True) + '"' if v is not None else '') for k, v in fixed) + '>')
    def handle_endtag(self, tag): self.output.append('</' + tag + '>')
    def handle_data(self, data): self.output.append(data)
    def handle_entityref(self, name): self.output.append('&' + name + ';')
    def handle_charref(self, name): self.output.append('&#' + name + ';')
parsed = Links()
parsed.feed(markdown.markdown((ROOT/'project-readme.md').read_text(), extensions=['fenced_code', 'tables', 'sane_lists']))
body = ''.join(parsed.output)
page = '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cocolian Office · 开源云文档中台</title><link rel="stylesheet" href="/project-homepage.css"></head><body><header><a class="brand" href="/">Cocolian Office</a><nav><a href="https://github.com/cocolian/online.mirror">公开源码</a><a class="button" href="/login">试用登录</a></nav></header><main><article>''' + body + '''</article><section id="trial" class="trial"><h2>关注「老熊看架构」，获取在线试用密码</h2><p>使用微信扫描下方二维码，关注「老熊看架构」公众号后获取试用密码，再通过试用登录入口体验在线编辑和文档转换。</p><img class="qrcode" src="/community-qrcode.jpg" width="258" height="258" alt="老熊看架构微信公众号二维码"><p><a class="button" href="/login">进入试用登录</a></p><p class="note">项目源码可按各组件许可证免费使用、部署和接入。</p></section></main><footer>基于 LibreOffice 与 Collabora Online · <a href="https://github.com/cocolian/online.mirror">查看项目 README 与许可证</a></footer></body></html>'''
(ROOT/'project-homepage.html').write_text(page)
