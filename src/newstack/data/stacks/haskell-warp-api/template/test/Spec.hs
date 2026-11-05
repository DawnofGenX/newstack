-- | The counting rules and the whole route table, checked without a socket.
-- A plain exitcode-stdio suite: no test framework, no extra dependency.
{-# LANGUAGE OverloadedStrings #-}
module Main (main) where

import Contract (Reply (..), parseText, route)
import Control.Monad (forM_, unless)
import Counts (Counts (..), countText, countsJson)
import Data.Text (Text)
import System.Exit (exitFailure)

main :: IO ()
main = do
  let checks =
        [ ("counts hello world", countText "hello world\n" == Counts 1 2 12)
        , ("counts empty", countText "" == Counts 0 0 0)
        , ("counts blank lines", countText "\n\nx\n" == Counts 3 1 4)
        , ("counts spaces only", countText "  \t " == Counts 0 0 4)
        , ("counts no newline", countText "abc" == Counts 0 1 3)
        , ("counts utf-8 bytes", countText "héllo wörld\n" == Counts 1 2 14)
        , ("counts emoji bytes", countText "🙂\n" == Counts 1 1 5)
        , ("health", replyOf (route "GET" "/health" "" "") == (200, "{\"status\":\"ok\"}"))
        , ("get stats", replyOf (route "GET" "/stats" "text=hello%20world%0A" "") == (200, countsJson "hello world\n" (countText "hello world\n")))
        , ("get stats tolerates the leading question mark", replyOf (route "GET" "/stats" "?text=abc%0A" "") == (200, countsJson "abc\n" (countText "abc\n")))
        , ("get stats plus is a space", bodyOf (route "GET" "/stats" "text=a+b%09c" "") == Just (countsJson "a b\tc" (countText "a b\tc")))
        , ("get without text", statusOf (route "GET" "/stats" "" "") == 422)
        , ("post stats", replyOf (route "POST" "/stats" "" "{\"text\": \"a b\\nc\\n\"}") == (200, countsJson "a b\nc\n" (countText "a b\nc\n")))
        , ("post keeps the text exactly as sent", bodyOf (route "POST" "/stats" "" "{\"text\": \"  padded  \\n\"}") == Just (countsJson "  padded  \n" (countText "  padded  \n")))
        , ("post without text", statusOf (route "POST" "/stats" "" "{}") == 422)
        , ("post with numeric text", statusOf (route "POST" "/stats" "" "{\"text\": 42}") == 422)
        , ("post with a broken body", statusOf (route "POST" "/stats" "" "nope") == 422)
        , ("post with an array body", statusOf (route "POST" "/stats" "" "[1,2]") == 422)
        , ("wrong method on health", statusOf (route "DELETE" "/health" "" "") == 405)
        , ("wrong method on stats", statusOf (route "PUT" "/stats" "" "") == 405)
        , ("unknown route", replyOf (route "GET" "/nope" "" "") == (404, "{\"error\":\"not_found\",\"detail\":\"no route for GET /nope\"}"))
        , ("parseText rejects a number field", parseText "{\"text\": 42}" == Right Nothing)
        , ("parseText reads an escaped string", parseText "{\"text\": \"a\\u00e9\"}" == Right (Just "a\xe9"))
        , ("parseText rejects trailing junk", parseText "{\"text\": \"a\"} x" == Left ())
        , ("parseText rejects a non-object", parseText "[1,2]" == Left ())
        ]
  let failures = [name | (name, ok) <- checks, not ok]
  forM_ checks $ \(name, ok) -> putStrLn ((if ok then "ok   " else "FAIL ") ++ name)
  unless (null failures) $ do
    putStrLn ("\n" ++ show (length failures) ++ " failing: " ++ unwords failures)
    exitFailure
  putStrLn ("\n" ++ show (length checks) ++ " checks passed")

statusOf :: Reply -> Int
statusOf = replyStatus

replyOf :: Reply -> (Int, Text)
replyOf reply = (replyStatus reply, replyBody reply)

bodyOf :: Reply -> Maybe Text
bodyOf reply = if replyStatus reply == 200 then Just (replyBody reply) else Nothing
