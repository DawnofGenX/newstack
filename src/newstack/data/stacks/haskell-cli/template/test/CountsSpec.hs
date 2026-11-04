module CountsSpec (countsSpec) where

import qualified Data.ByteString as B
import qualified Data.ByteString.Char8 as BC
import Harness (check, checkEqual)
import TextStat.Counts

sample :: Counts
sample = ofBytes (BC.pack "alpha beta\ngamma delta\n")

countsSpec :: IO [Bool]
countsSpec =
  sequence
    [ checkEqual "lines" 2 (countLines sample)
    , checkEqual "words" 4 (countWords sample)
    , checkEqual "bytes" 23 (countBytes sample)
    , checkEqual
        "no trailing newline is not a line"
        (Counts 0 3 16)
        (ofBytes (BC.pack "alpha beta gamma"))
    , checkEqual "empty input" empty (ofBytes BC.empty)
    , checkEqual
        "utf-8 is counted in bytes, not characters"
        (Counts 1 2 14)
        -- "héllo wörld" in UTF-8: the two non-ASCII characters are two bytes each
        (ofBytes (B.pack [104, 195, 169, 108, 108, 111, 32, 119, 195, 182, 114, 108, 100, 10]))
    , checkEqual
        "tabs, vertical tabs and form feeds separate words"
        (Counts 1 3 6)
        (ofBytes (BC.pack "a\tb\vc\n"))
    , checkEqual "add" (Counts 4 8 46) (addCounts sample sample)
    , checkEqual "columns honour the figures" [] (columns noFigures sample)
    , checkEqual "columns in wc order" [2, 4] (columns (Figures True True False) sample)
    , checkEqual "widthOf is the widest figure" 2 (widthOf [sample, Counts 10 0 0] allFigures)
    , checkEqual "formatRow pads on the left" " 2  4 23 sample.txt" (formatRow allFigures sample "sample.txt" 2)
    ]
