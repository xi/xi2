xi2 is a plain text language that compiles to MIDI.

# Usage

Notes are expressed as numbers. By default, an offset of 60 is applied, so `0`
is 60 in MIDI, which is c3.

Beats are separated by comma:

    0: 0,2,4,5,7,9,11,12,

You can leave a beat empty or use `-` to hold the previous note:

    0: 0, ,0,0,7,-,-,-,

Beats can be subdivided using parens. Notes that are grouped this way are
evenly spaced, so e.g. grouping 3 notes gives you triplets:

    0: (0,0),(4,4,4),(7,7,7,7),12,

Notes can also be played at the same time (chords) using curly braces:

    0: {0,4,7},{0,4,9},{0,5,9},{2,7,11},

Each track has its own line. Sections are separated by a blank line. Whitespace
inside lines is ignored, so you can align the tracks:

    0: 12,      (16, 21), -,       (23,19,14),
    8: {0,4,7}, {0,4,9},  {0,5,9}, {2,7,11},

    0: (16,19), (16,21), (-,17),  (19,23),
    8: {0,4,7}, {0,4,9}, {0,5,9}, {2,7,11},

Macros allow you to reuse patterns without having to write them again and
again. xi2 supports both single-line and multi-line patterns:

    [C]: {0,4,7}
    [G]: {7,11,14}

    [intro]:
    0: [C],[C],[G],[C],
    [end]

    [intro]
    [intro]

Instead of notes you can also include strings for lyrics. Be aware that
whitespace will be ignored, so you should use `_` instead:

    0: (9   ,,),(2    ,-,5   ),4  ,0   ,
    l: (Pop_,,),(goes_,-,the_),Wea,sel.,

# similar projects

-   [drumscript](https://github.com/tepreece/drumscript/)
-   [lilypond](https://lilypond.org/doc/v2.24/Documentation/learning/simple-notation)
