{- | The only module that touches the real file system, the real terminal and
the real exit status. -}
module Main (main) where

import Control.Exception (SomeException, try)
import qualified Data.ByteString as B
import System.Environment (getArgs)
import System.Exit (ExitCode (..), exitWith)
import System.IO (hFlush, hPutStrLn, stderr, stdout)
import TextStat.Runner (Io (..), run)

systemIo :: Io
systemIo =
  Io
    { ioReadFile = \path -> do
        result <- try (B.readFile path) :: IO (Either SomeException B.ByteString)
        pure $ case result of
          Left _ -> Left ("error: cannot open '" ++ path ++ "'")
          Right bytes -> Right bytes
    , ioReadStdin = B.getContents
    , ioOut = putStrLn
    , ioErr = hPutStrLn stderr
    }

main :: IO ()
main = do
  args <- getArgs
  code <- run args systemIo
  hFlush stdout
  hFlush stderr
  exitWith (if code == 0 then ExitSuccess else ExitFailure code)
