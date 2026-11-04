{- | Wiring the pure pieces to the real world through a small 'Io' record, so
the whole CLI can be tested without touching a file system or a terminal. -}
module TextStat.Runner
  ( Io (..)
  , program
  , run
  ) where

import qualified Data.ByteString as B
import TextStat.Counts
import TextStat.Options

-- | Everything the runner is allowed to do to the outside world.
data Io = Io
  { ioReadFile :: FilePath -> IO (Either String B.ByteString)
  , ioReadStdin :: IO B.ByteString
  , ioOut :: String -> IO ()
  , ioErr :: String -> IO ()
  }

program :: String
program = "{{ npm_name }}"

-- | Run one command line and return the process exit code: 0 success (and for
-- @--help@ / @--version@), 1 a file could not be read, 2 a usage error.
run :: [String] -> Io -> IO Int
run args io = case parsedStatus parsed of
  Help -> ioOut io (usage program) >> pure 0
  Version -> ioOut io version >> pure 0
  UsageError message -> do
    ioErr io (program ++ ": " ++ message)
    ioErr io ("Try '" ++ program ++ " --help' for more information.")
    pure 2
  Ok -> runOk io (parsedFigures parsed) (operands (parsedFiles parsed))
  where
    parsed = parse args
    operands [] = ["-"]
    operands files = files

runOk :: Io -> Figures -> [String] -> IO Int
runOk io figures paths = do
  results <- mapM readOne paths
  let failures = [message | Left message <- results]
  mapM_ (ioErr io) failures
  let rows = [(counts, label) | Right (counts, label) <- results]
  let total = foldl addCounts empty (map fst rows)
  let shown = if length paths > 1 then rows ++ [(total, "total")] else rows
  let width = widthOf (map fst shown) figures
  mapM_ (\(counts, label) -> ioOut io (formatRow figures counts label width)) shown
  pure (if null failures then 0 else 1)
  where
    readOne "-" = do
      contents <- ioReadStdin io
      pure (Right (ofBytes contents, "-"))
    readOne path = do
      contents <- ioReadFile io path
      pure (fmap (\bytes -> (ofBytes bytes, path)) contents)
