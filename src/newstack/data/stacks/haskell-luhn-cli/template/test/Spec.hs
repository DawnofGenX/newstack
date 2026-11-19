module Main (main) where

import Harness (summary)
import LuhnSpec (luhnSpec)

main :: IO ()
main = do
  results <- luhnSpec
  summary results