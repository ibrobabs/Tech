import hashlib

from datetime import datetime, time, timedelta
from itertools import chain, cycle, islice





def is_in_play(page):
    """
    Check to see if a page is in the Play section. A page is in the Play
    section if it has 'show_in_play_menu' set to True, or one of its
    ancestors does.
    """
    if not page:
        return False

    if getattr(page.specific, 'show_in_play_menu', False):
        return True

    return any(
        getattr(ancestor.specific, 'show_in_play_menu', False)
        for ancestor in page.get_ancestors()
    )


def play_filter(pages, number=None):
    """
    Given an iterable of Pages, return a specified number that
    are not in the Play section.
    """
    result = []
    for page in pages:
        if (number is not None) and (len(result) > (number - 1)):
            break
        if not is_in_play(page):
            result.append(page)
    return result


# https://docs.python.org/2/library/itertools.html#recipes
def roundrobin(*iterables):
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis
    pending = len(iterables)
    nexts = cycle(iter(it).next for it in iterables)
    while pending:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            pending -= 1
            nexts = cycle(islice(nexts, pending))
