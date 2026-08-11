import sys
from html.parser import HTMLParser

class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.void = {'br','img','input','meta','link','hr','area','base','col','embed','source','track','wbr'}
    def handle_starttag(self, tag, attrs):
        if tag not in self.void:
            self.stack.append(tag)
    def handle_endtag(self, tag):
        if tag in self.stack:
            while self.stack[-1] != tag:
                print('  unclosed:', self.stack.pop())
            self.stack.pop()
        else:
            print('  extra closing tag with no match:', tag)

for path in sys.argv[1:]:
    print('===', path, '===')
    p = P()
    p.feed(open(path, encoding='utf-8').read())
    if p.stack:
        print('  UNBALANCED, remaining open:', p.stack)
    else:
        print('  OK - balanced')
