from mep.books.migration_group_work_utils import similar_titles


def test_similar_titles():

    # single title
    assert similar_titles(['Helene'])

    # exact same
    assert similar_titles(['Helene', 'Helene'])

    # variance in definite article
    assert similar_titles(['New Yorker', 'The New Yorker'])

    # variance in upper/lower case
    assert similar_titles(['New Yorker', 'a new yorker'])

    # slugify flattens accents
    assert similar_titles(['Françoise', 'Francoise'])

    # variation in initials
    assert similar_titles(['Short Stories of H.G. Wells',
                           'Short Stories of H. G. Wells'])

    # em dash and regular dash
    assert similar_titles(['Collected Poems, 1909–1935',
                           'Collected Poems, 1909-1935'])

    # not close enough
    assert not similar_titles(['Collected Poems, 1909–1935',
                               'Collected Poems'])
