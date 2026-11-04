module RunnerSpec (runnerSpec, fakeIo) where

import Data.IORef (IORef, newIORef, readIORef, writeIORef)
import qualified Data.ByteString.Char8 as BC
import Harness (check, checkEqual)
import TextStat.Runner (Io (..), program, run)

-- | An 'Io' that records everything and never touches the file system.
data Capture = Capture
  { stdoutLines :: IORef [String]
  , stderrLines :: IORef [String]
  }

fakeIo :: [(FilePath, String)] -> String -> IO (Io, Capture)
fakeIo files stdinText = do
  outRef <- newIORef []
  errRef <- newIORef []
  let io =
        Io
          { ioReadFile = \path ->
              pure $ case lookup path files of
                Just contents -> Right (BC.pack contents)
                Nothing -> Left ("error: cannot open '" ++ path ++ "'")
          , ioReadStdin = pure (BC.pack stdinText)
          , ioOut = \line -> writeIORef outRef . (++ [line]) =<< readIORef outRef
          , ioErr = \line -> writeIORef errRef . (++ [line]) =<< readIORef errRef
          }
  pure (io, Capture outRef errRef)

runnerSpec :: IO [Bool]
runnerSpec = do
  (okIo, ok) <- fakeIo [("a.txt", "alpha beta\ngamma\n")] ""
  okCode <- run ["a.txt"] okIo
  okOut <- readIORef (stdoutLines ok)

  (stdinIo, stdinCapture) <- fakeIo [] "hi there\n"
  stdinCode <- run [] stdinIo
  stdinOut <- readIORef (stdoutLines stdinCapture)

  (totalIo, totalCapture) <- fakeIo [("a.txt", "alpha beta\ngamma\n"), ("b.txt", "x\n")] ""
  totalCode <- run ["a.txt", "b.txt"] totalIo
  totalOut <- readIORef (stdoutLines totalCapture)

  (missingIo, missingCapture) <- fakeIo [("a.txt", "one\n")] ""
  missingCode <- run ["a.txt", "nope.txt"] missingIo
  missingOut <- readIORef (stdoutLines missingCapture)
  missingErr <- readIORef (stderrLines missingCapture)

  (helpIo, helpCapture) <- fakeIo [] ""
  helpCode <- run ["--help"] helpIo
  helpOut <- readIORef (stdoutLines helpCapture)

  (bogusIo, bogusCapture) <- fakeIo [] ""
  bogusCode <- run ["--bogus"] bogusIo
  bogusErr <- readIORef (stderrLines bogusCapture)

  (versionIo, versionCapture) <- fakeIo [] ""
  versionCode <- run ["--version"] versionIo
  versionOut <- readIORef (stdoutLines versionCapture)

  (flagIo, flagCapture) <- fakeIo [("a.txt", "alpha beta\ngamma\n")] ""
  _ <- run ["-w", "a.txt"] flagIo
  flagOut <- readIORef (stdoutLines flagCapture)

  sequence
    [ checkEqual "one file exits 0" 0 okCode
    , checkEqual "one file prints one row" [" 2  3 17 a.txt"] okOut
    , checkEqual "stdin exits 0" 0 stdinCode
    , checkEqual "stdin is labelled -" ["1 2 9 -"] stdinOut
    , checkEqual "two files exit 0" 0 totalCode
    , checkEqual "two files get a total row" [" 2  3 17 a.txt", " 1  1  2 b.txt", " 3  4 19 total"] totalOut
    , checkEqual "an unreadable file exits 1" 1 missingCode
    , checkEqual "an unreadable file is reported on stderr" ["error: cannot open 'nope.txt'"] missingErr
    , checkEqual "readable files are still printed" ["1 1 4 a.txt", "1 1 4 total"] missingOut
    , checkEqual "--help exits 0" 0 helpCode
    , check "help mentions the usage line" (any ("Usage: " `prefixOf`) helpOut)
    , checkEqual "--bogus exits 2" 2 bogusCode
    , checkEqual "usage errors name the option" [program ++ ": unknown option: --bogus"] (take 1 bogusErr)
    , checkEqual "usage errors explain where to look" ["Try '" ++ program ++ " --help' for more information."] (drop 1 bogusErr)
    , checkEqual "--version exits 0" 0 versionCode
    , checkEqual "version prints the number" ["0.1.0"] versionOut
    , checkEqual "-w prints only words" ["3 a.txt"] flagOut
    ]
  where
    prefixOf prefix value = takeDoesPrefix prefix value
    takeDoesPrefix prefix value = take (length prefix) value == prefix
