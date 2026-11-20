# Transcription protocol: Sidney Rigdon's revelations (Stephen Post papers, MS 1304)

The manuscript is a fair copy in a clear nineteenth-century hand. Each page has a ruled main text block,
and a left margin where the copyist wrote short subject labels.

## Input
`crops/{book}_{seq}_top.jpg` and `crops/{book}_{seq}_bottom.jpg` are the upper and lower halves of one
page image. The halves overlap by about 12% of the page, so a few lines appear in both.

## Output
One plain-text file per page image: `transcription/{book}_{seq}.txt`, for example `transcription/A_006.txt`.

```
# image: A_006
# page: 4            <- the number written at the top corner of the page, or "none"
# status: text       <- "text", "blank", "index", "cover" or "other"

<the transcription>
```

## Rules
1. **Transcribe the main text block only.** Leave out the left-margin subject labels, page numbers,
   and anything on the facing page that shows at the edge of the image.
2. **Write exactly what is written.** Keep the original spelling, capitalization and punctuation, including
   mistakes. Do not modernize, correct or expand abbreviations. Write the old long-s form of "ss" as "ss".
3. **Do not keep the manuscript's line breaks.** Join the lines of a paragraph into running text. A word
   split across two lines is written as one word. Start a new paragraph where the manuscript does.
4. **Do not repeat the overlap.** Lines that appear in both halves are written once.
5. **Never guess silently.**
   - a word you cannot read at all: `[illegible]`
   - a word you can read but are not sure of: the word followed by `[?]`, for example `prevail[?]`
   - text struck out by the writer: leave it out
   - text inserted above the line: put it where the writer's mark places it
6. **Mark structure on lines of their own, starting with `##`:**
   - a section heading: `## heading: Section 4.` (as written, including any date or place line)
   - a date or place written in the left margin beside a section heading: `## date: 1863 Sept 10th` (this is the
     one margin item to record; write it as written)
   - a signature or closing note: `## signed: Sidney Rigdon` or `## signed: Sidney Rigdon, Phebe Rigdon`
   - a copyist's note about the text (for example "Received June 1864"): `## note: ...`
7. **A page that continues a sentence from the previous page starts mid-sentence.** Do not add anything
   to join them. Do not add commentary, summaries or headings of your own.
8. **Blank pages, covers and index pages** get the header with the right status and no transcription.

## Checking your own work
After transcribing a page, look again at any proper names, numbers and dates, and at the first and last
words of each half, where the overlap makes omissions and repeats most likely.
