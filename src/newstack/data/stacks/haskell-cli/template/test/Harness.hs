{- | A hand-written test harness: no Hackage dependency, no test framework to
learn. Each check prints a line and the spec exits non-zero if any check fails. -}
module Harness
  ( check
  , checkEqual
  , summary
  ) where

import System.Exit (exitFailure, exitSuccess)

check :: String -> Bool -> IO Bool
check name passed = do
  putStrLn ((if passed then "ok   " else "FAIL ") ++ name)
  pure passed

checkEqual :: (Eq a, Show a) => String -> a -> a -> IO Bool
checkEqual name expected actual = do
  let passed = expected == actual
  if passed
    then putStrLn ("ok   " ++ name)
    else do
      putStrLn ("FAIL " ++ name)
      putStrLn ("     expected: " ++ show expected)
      putStrLn ("     actual:   " ++ show actual)
  pure passed

summary :: [Bool] -> IO ()
summary results = do
  let total = length results
  let failed = length (filter not results)
  putStrLn ""
  putStrLn
    ( show total
        ++ " checks, "
        ++ show (total - failed)
        ++ " passed, "
        ++ show failed
        ++ " failed"
    )
  if failed == 0 then exitSuccess else exitFailure
