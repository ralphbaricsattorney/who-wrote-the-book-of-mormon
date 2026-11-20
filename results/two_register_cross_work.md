# Two-register study, cross-work reference: features F2, threshold 0.1

Development text only. Scripture-style text is ranked against each prose work under the model that held that work out. Each prose work (authors with three or more) is held out of every model and reference, then ranked the same way.

## Per author

`other_work_recall`: each prose work, held out of every model and reference, accepted as the author; works count equally; authors with three or more works only. `scripture_recall`: the author's scripture-style text accepted as the author. `register_false_acceptance`: other authors' scripture-style text and the biblical-style controls accepted as the author, each text counting once.

| author                   | works | other_work_recall | scripture_chunks | scripture_recall | register_false_acceptance | margin | worst_other                   | worst_rate |
|--------------------------|-------|-------------------|------------------|------------------|---------------------------|--------|-------------------------------|------------|
| Christopher G. Memminger | 5     | 0.86              | 14               | 0.14             | 0.08                      | 0.06   | 'Eliakim the Scribe' (pseud.) | 0.32       |
| Jacob Ilive              | 4     | 0.77              | 22               | 0.05             | 0.29                      | -0.25  | 'Eliakim the Scribe' (pseud.) | 0.63       |
| James J. Strang          | 3     | 0.93              | 16               | 0.25             | 0.51                      | -0.26  | Richard Snowden               | 0.96       |
| Richard Grant White      | null  | null              | 60               | 0.00             | 0.01                      | -0.01  | 'Eliakim the Scribe' (pseud.) | 0.05       |

## Each prose work

| author                   | work                                                    | chunks | accepted |
|--------------------------|---------------------------------------------------------|--------|----------|
| Christopher G. Memminger | transfer_memminger__prose__augusta_lecture_1851         | 8      | 0.50     |
| Christopher G. Memminger | transfer_memminger__prose__bank_letters_1850            | 5      | 0.80     |
| Christopher G. Memminger | transfer_memminger__prose__bible_oration_1842           | 7      | 1.00     |
| Christopher G. Memminger | transfer_memminger__prose__cooperation_address_1851     | 7      | 1.00     |
| Christopher G. Memminger | transfer_memminger__prose__virginia_address_1860        | 11     | 1.00     |
| Jacob Ilive              | transfer_ilive__prose__laymans_vindication_1730         | 81     | 0.91     |
| Jacob Ilive              | transfer_ilive__prose__oration_joyners_hall_1733        | 12     | 1.00     |
| Jacob Ilive              | transfer_ilive__prose__oration_trinity_hall_1738        | 9      | 1.00     |
| Jacob Ilive              | transfer_ilive__prose__reasons_house_of_correction_1757 | 17     | 0.18     |
| James J. Strang          | transfer_strang__prose__diary_1831_36                   | 16     | 1.00     |
| James J. Strang          | transfer_strang__prose__michilimackinac                 | 31     | 0.97     |
| James J. Strang          | transfer_strang__prose__prophetic_controversy           | 17     | 0.82     |
