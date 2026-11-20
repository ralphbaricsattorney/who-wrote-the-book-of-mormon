"""The function-word list. F2 uses MODERN (223 words, listed in the article); F1 adds ARCHAIC.

W        closed-class English words: articles, pronouns, prepositions, conjunctions, auxiliaries, common adverbs
ARCHAIC  the part of W marked as King James English; kept in feature set F1, masked in F2
"""

ARCHAIC = frozenset("""
thee thou thy thine ye hath hast doth dost art wilt shalt wast didst hadst canst couldst wouldst shouldst
unto thereof therein thereby thereon therewith wherefore whereby wherein whereof whereupon whither whence
hither thither behold lo yea nay verily insomuch forasmuch ere nigh
""".split())

MODERN = frozenset("""
a an the this that these those each every either neither any some all both such no another other others same own
several few many much more most less least enough
i me my mine myself we us our ours ourselves you your yours yourself yourselves he him his himself she her hers
herself it its itself they them their theirs themselves who whom whose which what whoever whatever one ones
anyone anything everyone everything someone something nobody nothing none
of in to for with on at by from up about into over after under above below between among through during before
behind beside besides beyond against along around across toward towards upon within without out off down near
since until till except amid amongst concerning respecting throughout onto
and but or nor so yet because although though if unless while whilst whereas whether than as lest when whenever
where wherever why how however therefore thus hence moreover nevertheless notwithstanding otherwise also too
am is are was were be been being have has had having do does did doing done will would shall should may might
must can could ought cannot not never
very quite rather almost only just even still already always often sometimes ever again once twice here there
now then soon away back forth together well indeed perhaps else further
""".split())

W = MODERN | ARCHAIC
