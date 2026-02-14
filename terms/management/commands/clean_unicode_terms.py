from django.core.management.base import BaseCommand
from terms.models import Term
import re


def _decode_unicode_escapes(text: str) -> str:
    """Convert literal \\uXXXX escape sequences to real characters."""
    if not text or "\\u" not in text:
        return text
    def replace_escape(m):
        try:
            return chr(int(m.group(1), 16))
        except Exception:
            return m.group(0)
    return re.sub(r'\\u([0-9a-fA-F]{4})', replace_escape, text)


class Command(BaseCommand):
    help = 'Fix terms that contain literal unicode escape sequences (e.g. "\\u0026").'

    def handle(self, *args, **options):
        qs = Term.objects.filter(name__contains='\\u')
        if not qs.exists():
            self.stdout.write('No terms with unicode-escaped sequences found.')
            return

        for term in qs:
            old = term.name
            new = _decode_unicode_escapes(old)
            if new != old:
                self.stdout.write(f'Updating name: "{old}" -> "{new}"')
                term.name = new
                term.save(update_fields=['name'])

        # also check explanations
        qs2 = Term.objects.filter(explanation__contains='\\u')
        for term in qs2:
            old = term.explanation
            new = _decode_unicode_escapes(old)
            if new != old:
                self.stdout.write(f'Updating explanation for {term.name}')
                term.explanation = new
                term.save(update_fields=['explanation'])

        self.stdout.write('Done.')

        self.stdout.write('Done.')
