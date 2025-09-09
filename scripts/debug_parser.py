from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from infra import parser

CASES = [
    ("The.Matrix.1999.1080p.mkv", ("The Matrix", 1999)),
    ("Inception (2010) [BluRay].mkv", ("Inception", 2010)),
    ("Blade Runner 1982 Final Cut.mkv", ("Blade Runner", 1982)),
    ("Mad.Max.Fury.Road.2015.mkv", ("Mad Max Fury Road", 2015)),
    ("Avatar-2009-Extended.mkv", ("Avatar", 2009)),
    ("Alien 1979 4K.mkv", ("Alien", 1979)),
    ("A.Beautiful.Mind.2001.m4v", ("A Beautiful Mind", 2001)),
    ("Annihilation.2018.WEBRip.mp4", ("Annihilation", 2018)),
    ("Interstellar 2014.mkv", ("Interstellar", 2014)),
    ("The.Godfather.Part.II.1974.mkv", ("The Godfather Part II", 1974)),
    ("Dune (2021).mkv", ("Dune", 2021)),
    ("No.Country.for.Old.Men.2007.1080p.mkv", ("No Country For Old Men", 2007)),
]

correct = 0
for fn, expected in CASES:
    got = parser.parse_filename(fn)
    ok = got == expected
    print("OK" if ok else "XX", fn, "=>", got, "expected", expected)
    if ok:
        correct += 1
print("accuracy", correct/len(CASES))
