-- | The whole route table as a pure function plus the small JSON reader and
-- writer it needs, so the test suite can pin every status code without a socket.
{-# LANGUAGE OverloadedStrings #-}
module Contract
  ( Reply (..)
  , route
  , parseText
  ) where

import Counts (countText, countsJson, quoteJson)
import Data.Char (chr, digitToInt, isDigit, isHexDigit)
import Data.List (foldl')
import Data.Text (Text)
import qualified Data.Text as T

data Reply = Reply
  { replyStatus :: Int
  , replyBody :: Text
  }
  deriving (Eq, Show)

route :: Text -> Text -> Text -> Text -> Reply
route method path query body
  | method == "GET" && path == "/health" = ok "{\"status\":\"ok\"}"
  | method == "GET" && path == "/stats" = case queryParam "text" (dropQuestion query) of
      Nothing -> errorReply 422 "missing_text"
      Just text -> statsReply text
  | method == "POST" && path == "/stats" = case parseText body of
      Left () -> errorReply 422 "invalid_json"
      Right Nothing -> errorReply 422 "missing_text"
      Right (Just text) -> statsReply text
  | path == "/health" || path == "/stats" = errorReply 405 "method_not_allowed"
  | otherwise =
      Reply
        404
        ( T.concat
            [ "{\"error\":\"not_found\",\"detail\":"
            , quoteJson (T.concat ["no route for ", method, " ", path])
            , "}"
            ]
        )

statsReply :: Text -> Reply
statsReply text = ok (countsJson text (countText text))

ok :: Text -> Reply
ok = Reply 200

errorReply :: Int -> Text -> Reply
errorReply status code = Reply status (T.concat ["{\"error\":\"", code, "\"}"])

-- | Warp hands us the query string with its leading @?@ still attached.
dropQuestion :: Text -> Text
dropQuestion = T.dropWhile (== '?')

queryParam :: Text -> Text -> Maybe Text
queryParam name query =
  case [value | pair <- T.splitOn "&" query, not (T.null pair), (key, value) <- [splitPair pair], key == name] of
    (value : _) -> Just (unquote value)
    [] -> Nothing
  where
    splitPair pair = case T.breakOn "=" pair of
      (key, rest) -> (key, T.drop 1 rest)

unquote :: Text -> Text
unquote = percentDecode . T.replace "+" " "

percentDecode :: Text -> Text
percentDecode text = case T.breakOn "%" text of
  (plain, rest)
    | T.null rest -> plain
    | otherwise -> case T.unpack (T.take 3 rest) of
        ('%' : high : low : _)
          | isHexDigit high && isHexDigit low ->
              T.append plain (T.cons (chr (digitToInt high * 16 + digitToInt low)) (percentDecode (T.drop 3 rest)))
        _ -> T.append plain (T.cons '%' (percentDecode (T.drop 1 rest)))

-- | A JSON object with a string @text@ member, a JSON object without one, or
-- something that is not a JSON object at all.
parseText :: Text -> Either () (Maybe Text)
parseText body = case parseValue (T.stripStart body) of
  Just (JObject members, rest)
    | T.null (T.strip rest) -> Right (lookup "text" members >>= asString)
  _ -> Left ()

asString :: JValue -> Maybe Text
asString (JString text) = Just text
asString _ = Nothing

data JValue
  = JObject [(Text, JValue)]
  | JArray [JValue]
  | JString Text
  | JNumber Text
  | JBool Bool
  | JNull
  deriving (Eq, Show)

parseValue :: Text -> Maybe (JValue, Text)
parseValue input = case T.uncons (T.stripStart input) of
  Nothing -> Nothing
  Just (c, rest) -> case c of
    '{' -> parseObject (T.stripStart rest)
    '[' -> parseArray (T.stripStart rest)
    '"' -> do
      (text, after) <- parseString rest
      Just (JString text, after)
    't' -> literal "true" (JBool True) rest
    'f' -> literal "false" (JBool False) rest
    'n' -> literal "null" JNull rest
    _ | c == '-' || isDigit c -> parseNumber (T.cons c rest)
    _ -> Nothing
  where
    literal word value rest
      | word `T.isPrefixOf` rest = Just (value, T.drop (T.length word) rest)
      | otherwise = Nothing

parseObject :: Text -> Maybe (JValue, Text)
parseObject input = case T.uncons input of
  Just ('}', rest) -> Just (JObject [], rest)
  _ -> go [] input
  where
    go members text = do
      (key, afterKey) <- expect '"' text >>= \(r) -> parseString r
      afterColon <- expect ':' (T.stripStart afterKey)
      (value, afterValue) <- parseValue (T.stripStart afterColon)
      let members' = (key, value) : members
      case T.uncons (T.stripStart afterValue) of
        Just (',', next) -> go members' (T.stripStart next)
        Just ('}', next) -> Just (JObject (reverse members'), next)
        _ -> Nothing

parseArray :: Text -> Maybe (JValue, Text)
parseArray input = case T.uncons input of
  Just (']', rest) -> Just (JArray [], rest)
  _ -> go [] input
  where
    go items text = do
      (value, afterValue) <- parseValue (T.stripStart text)
      let items' = value : items
      case T.uncons (T.stripStart afterValue) of
        Just (',', next) -> go items' (T.stripStart next)
        Just (']', next) -> Just (JArray (reverse items'), next)
        _ -> Nothing

parseString :: Text -> Maybe (Text, Text)
parseString input = go [] (T.unpack input)
  where
    go _ [] = Nothing
    go acc ('"' : rest) = Just (T.pack (reverse acc), T.pack rest)
    go acc ('\\' : c : rest) = case c of
      '"' -> go ('"' : acc) rest
      '\\' -> go ('\\' : acc) rest
      '/' -> go ('/' : acc) rest
      'b' -> go ('\b' : acc) rest
      'f' -> go ('\f' : acc) rest
      'n' -> go ('\n' : acc) rest
      'r' -> go ('\r' : acc) rest
      't' -> go ('\t' : acc) rest
      'u' -> case splitAt 4 rest of
        (hex, after) | length hex == 4 && all isHexDigit hex ->
          go (chr (foldl' (\n d -> n * 16 + digitToInt d) 0 hex) : acc) after
        _ -> Nothing
      _ -> Nothing
    go acc (c : rest) = go (c : acc) rest

parseNumber :: Text -> Maybe (JValue, Text)
parseNumber input =
  let (digits, rest) = T.span isNumberChar input
   in if T.null digits then Nothing else Just (JNumber digits, rest)
  where
    isNumberChar c = isDigit c || c `elem` ("+-.eE" :: String)

expect :: Char -> Text -> Maybe Text
expect char text = case T.uncons text of
  Just (c, rest) | c == char -> Just rest
  _ -> Nothing
