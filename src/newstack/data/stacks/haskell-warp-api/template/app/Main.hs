-- | Warp glue: read the request, ask 'route' for the answer, write it back.
-- Every decision about status codes and bodies lives in Contract.
{-# LANGUAGE OverloadedStrings #-}
module Main (main) where

import Contract (Reply (..), route)
import qualified Data.ByteString.Lazy as BL
import qualified Data.Text.Encoding as TE
import Network.HTTP.Types (mkStatus)
import Network.Wai (Application, rawPathInfo, rawQueryString, requestMethod, responseLBS, strictRequestBody)
import Network.Wai.Handler.Warp (defaultSettings, runSettings, setHost, setPort)
import System.Environment (lookupEnv)

main :: IO ()
main = do
  port <- maybe 8080 read <$> lookupEnv "PORT"
  runSettings (setPort port (setHost "127.0.0.1" defaultSettings)) handler

handler :: Application
handler request respond = do
  body <- strictRequestBody request
  let reply =
        route
          (TE.decodeUtf8With lenient (requestMethod request))
          (TE.decodeUtf8With lenient (rawPathInfo request))
          (TE.decodeUtf8With lenient (rawQueryString request))
          (TE.decodeUtf8With lenient (BL.toStrict body))
  respond $
    responseLBS
      (mkStatus (replyStatus reply) "")
      [("content-type", "application/json")]
      (BL.fromStrict (TE.encodeUtf8 (replyBody reply)))
  where
    lenient _ _ = Just '\xfffd'
