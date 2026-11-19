module LuhnSpec (luhnSpec) where

import Harness (check, checkEqual)
import Luhn (luhnValid, luhnGenerate)

luhnSpec :: IO [Bool]
luhnSpec = do
  r1 <- check "valid 79927398713" (luhnValid "79927398713")
  r2 <- check "invalid 79927398710" (not (luhnValid "79927398710"))
  r3 <- checkEqual "generate" (Just "79927398713") (luhnGenerate "7992739871")
  r4 <- check "rejects letters" (not (luhnValid "12a4"))
  r5 <- check "empty invalid" (not (luhnValid ""))
  pure [r1, r2, r3, r4, r5]