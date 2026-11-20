# Two-register study: features F2, threshold 0.1

Development text only. One procedure, trained on the pool plus each two-register author's prose; every row below is text that procedure never saw.

Held-out prose works: transfer_memminger__prose__virginia_address_1860, transfer_ilive__prose__oration_trinity_hall_1738, transfer_strang__prose__prophetic_controversy, transfer_white_richard_grant__prose__words_and_their_uses; for Rigdon, his letters of 1863-76.

## Per author

`scripture_recall`: own scripture-style text accepted as the author. `other_work_recall`: an unseen prose work accepted as the author (none for Smith or for Thompson, who has one prose work). `register_false_acceptance`: other authors' scripture-style text, and the biblical-style controls, accepted as the author, each text counting once. Chunks within a work are not independent: each author is one case.

| author                   | attributed | scripture_chunks | scripture_recall | other_work_chunks | other_work_recall | register_false_acceptance | margin | worst_other                   | worst_rate |
|--------------------------|------------|------------------|------------------|-------------------|-------------------|---------------------------|--------|-------------------------------|------------|
| Charles B. Thompson      | false      | 21               | 0.00             | null              | null              | 0.01                      | -0.01  | Joseph Smith                  | 0.04       |
| Christopher G. Memminger | true       | 14               | 0.07             | 11                | 1.00              | 0.08                      | -0.01  | 'Eliakim the Scribe' (pseud.) | 0.37       |
| Jacob Ilive              | true       | 22               | 0.00             | 9                 | 1.00              | 0.04                      | -0.04  | Charles B. Thompson           | 0.14       |
| James J. Strang          | false      | 16               | 0.00             | 17                | 0.06              | 0.00                      | -0.00  | John Ballou Newbrough         | 0.01       |
| Joseph Smith             | false      | 54               | 0.74             | null              | null              | 0.28                      | 0.46   | Sidney Rigdon                 | 0.84       |
| Richard Grant White      | false      | 60               | 0.00             | 107               | 0.16              | 0.00                      | 0.00   | Joseph Smith                  | 0.00       |
| Sidney Rigdon            | false      | 37               | 0.65             | 8                 | 0.88              | 0.01                      | 0.64   | Richard Snowden               | 0.06       |

## Head to head on each author's scripture-style text

Row: whose scripture-style text. Column: the rival. D = share accepted as the row author and not the rival, minus share accepted as the rival and not the row author. Positive points to the right author.

| author                   | Ilive | Memminger | Rigdon | Smith | Strang | Thompson | White |
|--------------------------|-------|-----------|--------|-------|--------|----------|-------|
| Charles B. Thompson      | -0.14 | -0.05     | 0.00   | -0.67 | 0.00   | null     | 0.00  |
| Christopher G. Memminger | 0.07  | null      | 0.07   | 0.00  | 0.07   | 0.07     | 0.07  |
| Jacob Ilive              | null  | 0.00      | 0.00   | 0.00  | 0.00   | 0.00     | 0.00  |
| James J. Strang          | -0.06 | 0.00      | 0.00   | -0.12 | null   | 0.00     | 0.00  |
| Joseph Smith             | 0.72  | 0.72      | 0.74   | null  | 0.74   | 0.70     | 0.74  |
| Richard Grant White      | 0.00  | -0.05     | -0.02  | 0.00  | 0.00   | 0.00     | null  |
| Sidney Rigdon            | 0.54  | 0.59      | null   | -0.19 | 0.65   | 0.65     | 0.65  |
