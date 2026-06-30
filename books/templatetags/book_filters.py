from django import template

register = template.Library()

@register.filter
def batch(iterable, n):
    lst = list(iterable)
    return [lst[i:i+n] for i in range(0, len(lst), n)]

@register.filter
def spine_width(book):
    """Fixed pixel width based on page count (14–42 px). No flex-grow."""
    if book.page_count:
        p = book.page_count
        if p < 100: return 14
        if p < 200: return 18
        if p < 350: return 24
        if p < 550: return 32
        return 42
    return 14 + (book.pk * 5 + len(book.title or '') * 3) % 20

@register.filter
def spine_height(book):
    """Pseudo-random height 136–170 px for a staggered shelf look."""
    return 136 + (book.pk * 7 + len(book.title or '') * 3) % 34
