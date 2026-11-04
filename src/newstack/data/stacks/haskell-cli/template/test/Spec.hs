module Main (main) where

import CountsSpec (countsSpec)
import Harness (summary)
import OptionsSpec (optionsSpec)
import RunnerSpec (runnerSpec)

main :: IO ()
main = do
  counts <- countsSpec
  options <- optionsSpec
  runner <- runnerSpec
  summary (counts ++ options ++ runner)
