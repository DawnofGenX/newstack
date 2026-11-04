module OptionsSpec (optionsSpec) where

import Harness (check, checkEqual)
import TextStat.Counts (Figures (..), allFigures)
import TextStat.Options

statusOf :: [String] -> Status
statusOf = parsedStatus . parse

optionsSpec :: IO [Bool]
optionsSpec =
  sequence
    [ checkEqual "no arguments means all figures" allFigures (parsedFigures (parse []))
    , checkEqual "no arguments reads stdin" [] (parsedFiles (parse []))
    , checkEqual "a bare path is a file" ["a.txt"] (parsedFiles (parse ["a.txt"]))
    , checkEqual "flags come before files" ["a.txt", "b.txt"] (parsedFiles (parse ["-w", "a.txt", "b.txt"]))
    , checkEqual "-l selects lines only" (Figures True False False) (parsedFigures (parse ["-l", "x"]))
    , checkEqual "short flags cluster" allFigures (parsedFigures (parse ["-lwc", "x"]))
    , checkEqual "long flags work too" (Figures False False True) (parsedFigures (parse ["--bytes", "x"]))
    , checkEqual "the last flag does not cancel earlier ones" allFigures (parsedFigures (parse ["-l", "-w", "-c", "x"]))
    , checkEqual "--help wins" Help (statusOf ["-l", "--help"])
    , checkEqual "--version is its own status" Version (statusOf ["--version"])
    , check "--bogus is a usage error" (isUsageError (statusOf ["--bogus"]))
    , check "-x is a usage error" (isUsageError (statusOf ["-lx"]))
    , check "the error names the option" (hasMessage "unknown option: -x" (statusOf ["-lx"]))
    , check "the error keeps the files parsed so far" (["a.txt"] `keptBy` parse ["a.txt", "--bogus"])
    , checkEqual "-- ends the flags" ["--weird"] (parsedFiles (parse ["--", "--weird"]))
    , checkEqual "- is the stdin operand" ["-"] (parsedFiles (parse ["-"]))
    , check "usage names the program" (not (null (usage "demo")))
    , checkEqual "version string" "0.1.0" version
    ]
  where
    isUsageError (UsageError _) = True
    isUsageError _ = False
    hasMessage expected (UsageError message) = message == expected
    hasMessage _ _ = False
    keptBy files parsed = case parsedStatus parsed of
      UsageError _ -> parsedFiles parsed == files
      _ -> False
