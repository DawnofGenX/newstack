{- | Turning @argv@ into a decision. Pure: no I/O, no exit codes. -}
module TextStat.Options
  ( Status (..)
  , Parsed (..)
  , version
  , usage
  , parse
  ) where

import Data.List (isPrefixOf)
import TextStat.Counts (Figures (..), allFigures, noFigures)

-- | How a command line was resolved.
data Status
  = Ok
  | Help
  | Version
  | UsageError String
  deriving (Eq, Show)

-- | What to print, what to read, and whether to run at all.
data Parsed = Parsed
  { parsedFigures :: Figures
  , parsedFiles :: [String]
  , parsedStatus :: Status
  }
  deriving (Eq, Show)

version :: String
version = "0.1.0"

usage :: String -> String
usage program =
  unlines
    [ "Usage: " ++ program ++ " [-l] [-w] [-c] [FILE...]"
    , ""
    , "Print newline, word and byte counts for each FILE, and a total line if"
    , "more than one FILE is given. With no FILE, or when FILE is -, read"
    , "standard input. With no flag, all three figures are printed."
    , ""
    , "  -l, --lines   print the newline count"
    , "  -w, --words   print the word count"
    , "  -c, --bytes   print the byte count"
    , "  -h, --help    print this help and exit"
    , "  -V, --version print the version and exit"
    ]

appendFlag :: Figures -> Char -> Maybe Figures
appendFlag figures flag = case flag of
  'l' -> Just figures {figureLines = True}
  'w' -> Just figures {figureWords = True}
  'c' -> Just figures {figureBytes = True}
  _ -> Nothing

-- | Fold the short flags of one argument, as in @-lw@.
shortFlags :: Figures -> String -> Either String Figures
shortFlags figures = foldl step (Right figures)
  where
    step (Left message) _ = Left message
    step (Right current) flag =
      maybe (Left ("unknown option: -" ++ [flag])) Right (appendFlag current flag)

longFlag :: Figures -> String -> Either String Figures
longFlag figures flag = case flag of
  "--lines" -> Right figures {figureLines = True}
  "--words" -> Right figures {figureWords = True}
  "--bytes" -> Right figures {figureBytes = True}
  other -> Left ("unknown option: " ++ other)

-- | Parse @argv@. The last flag wins as a switch; with no flag at all all three
-- figures are printed, which is what @wc@ does.
parse :: [String] -> Parsed
parse args = go noFigures [] args False
  where
    go figures files [] _ =
      Parsed (if figures == noFigures then allFigures else figures) (reverse files) Ok
    go figures files (arg : rest) onlyFiles
      | onlyFiles = go figures (arg : files) rest True
      | arg == "--" = go figures files rest True
      | arg `elem` ["-h", "--help"] = Parsed figures [] Help
      | arg `elem` ["-V", "--version"] = Parsed figures [] Version
      | "--" `isPrefixOf` arg = withFlags figures files rest (longFlag figures arg)
      | "-" `isPrefixOf` arg && length arg > 1 =
          withFlags figures files rest (shortFlags figures (drop 1 arg))
      | otherwise = go figures (arg : files) rest False

    withFlags figures files rest result = case result of
      Left message -> Parsed figures (reverse files) (UsageError message)
      Right updated -> go updated files rest False
