from itertools import chain, repeat, tee, izip


def window_iter_fill(gen, size=2, fill=None):
    """
        Credits to senderle:
        http://stackoverflow.com/questions/6998245/
        iterate-over-a-window-of-adjacent-elements-in-python
    """
    gens = (chain(repeat(fill, size - i - 1), gen, repeat(fill, i))
            for i, gen in enumerate(tee(gen, size)))
    return izip(*gens)
