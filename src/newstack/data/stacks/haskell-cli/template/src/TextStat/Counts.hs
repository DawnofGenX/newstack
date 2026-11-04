{- | `wc`-style counting: pure, no I/O. -}
module TextStat.Counts
  ( Figures (..)
  , allFigures
  , noFigures
  , Counts (..)
  , empty
  , addCounts
  , ofBytes
  , columns
  , widthOf
  , formatRow
  ) where

import qualified Data.ByteString as B
import Data.List (intercalate)
import Data.Word (Word8)

-- | Which figures to print. @wc@ prints all three when given no flag.
data Figures = Figures
  { figureLines :: Bool
  , figureWords :: Bool
  , figureBytes :: Bool
  }
  deriving (Eq, Show)

allFigures :: Figures
allFigures = Figures True True True

noFigures :: Figures
noFigures = Figures False False False

-- | A tally: newline bytes, maximal runs of non-whitespace, raw bytes.
data Counts = Counts
  { countLines :: Integer
  , countWords :: Integer
  , countBytes :: Integer
  }
  deriving (Eq, Show)

empty :: Counts
empty = Counts 0 0 0

addCounts :: Counts -> Counts -> Counts
addCounts (Counts l w b) (Counts l' w' b') = Counts (l + l') (w + w') (b + b')

-- | The same whitespace set @wc@ uses: space, tab, newline, vertical tab,
-- form feed and carriage return.
isSpace :: Word8 -> Bool
isSpace w = w == 32 || w == 9 || w == 10 || w == 11 || w == 12 || w == 13

-- | Count raw bytes so the numbers match @wc -l -w -c@ on the same file.
-- A line is a newline byte, so a last line without a trailing newline is not
-- counted; a word is a maximal run of non-whitespace bytes.
ofBytes :: B.ByteString -> Counts
ofBytes bs =
  let (l, w, _) = B.foldl' step (0, 0, False) bs
   in Counts l w (fromIntegral (B.length bs))
  where
    step :: (Integer, Integer, Bool) -> Word8 -> (Integer, Integer, Bool)
    step (l, w, inWord) byte
      | isSpace byte = (l + if byte == 10 then 1 else 0, w, False)
      | inWord = (l, w, True)
      | otherwise = (l, w + 1, True)

-- | The printed columns, in @wc@ order, for the figures that were asked for.
columns :: Figures -> Counts -> [Integer]
columns figures counts =
  concat
    [ [countLines counts | figureLines figures]
    , [countWords counts | figureWords figures]
    , [countBytes counts | figureBytes figures]
    ]

-- | The column width @wc@ uses: the widest figure anywhere in the output.
widthOf :: [Counts] -> Figures -> Int
widthOf rows figures =
  maximum (0 : [length (show cell) | row <- rows, cell <- columns figures row])

-- | Right-align every column to @width@, the way @wc@ lines up its output.
formatRow :: Figures -> Counts -> String -> Int -> String
formatRow figures counts label width =
  intercalate " " (map pad cells ++ [label])
  where
    cells = columns figures counts
    pad cell = replicate (width - length (show cell)) ' ' ++ show cell
