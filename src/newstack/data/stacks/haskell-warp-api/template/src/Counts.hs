-- | The counting rules, shared by the service and its tests: a line is a
-- @\\n@, a word is a maximal run of non-space characters, and bytes is the
-- UTF-8 length (so "héllo" is five characters and six bytes).
{-# LANGUAGE OverloadedStrings #-}
module Counts
  ( Counts (..)
  , countText
  , countsJson
  , quoteJson
  ) where

import qualified Data.ByteString as BS
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Text.Encoding as TE
import Numeric (showHex)

data Counts = Counts
  { countLines :: Int
  , countWords :: Int
  , countBytes :: Int
  }
  deriving (Eq, Show)

countText :: Text -> Counts
countText text =
  Counts
    { countLines = T.count (T.singleton '\n') text
    , countWords = length (T.words text)
    , countBytes = BS.length (TE.encodeUtf8 text)
    }

countsJson :: Text -> Counts -> Text
countsJson text counts =
  T.concat
    [ "{\"text\":"
    , quoteJson text
    , ",\"lines\":"
    , T.pack (show (countLines counts))
    , ",\"words\":"
    , T.pack (show (countWords counts))
    , ",\"bytes\":"
    , T.pack (show (countBytes counts))
    , "}"
    ]

quoteJson :: Text -> Text
quoteJson text = T.concat ["\"", T.concatMap escapeChar text, "\""]

escapeChar :: Char -> Text
escapeChar '"' = "\\\""
escapeChar '\\' = "\\\\"
escapeChar '\n' = "\\n"
escapeChar '\r' = "\\r"
escapeChar '\t' = "\\t"
escapeChar c
  | fromEnum c < 0x20 = T.pack ("\\u" ++ pad (showHex (fromEnum c) ""))
  | otherwise = T.singleton c
  where
    pad hex = replicate (4 - length hex) '0' ++ hex
