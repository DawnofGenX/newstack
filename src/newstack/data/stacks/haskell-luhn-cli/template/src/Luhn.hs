-- HASKELL_LUHN_CLI_MARKER_2c9f4a
module Luhn
  ( luhnValid
  , luhnGenerate
  ) where

import Data.Char (isDigit, digitToInt, intToDigit)

allDigits :: String -> Bool
allDigits s = not (null s) && all isDigit s

luhnValue :: [Int] -> Int
luhnValue ds =
  let rev = reverse ds
      contrib (i, d) =
        if even i
        then d
        else let x = d * 2 in if x > 9 then x - 9 else x
  in sum (map contrib (zip [0 :: Int ..] rev))

luhnValid :: String -> Bool
luhnValid s =
  allDigits s && luhnValue (map digitToInt s) `mod` 10 == 0

luhnGenerate :: String -> Maybe String
luhnGenerate prefix
  | not (allDigits prefix) = Nothing
  | otherwise =
      let ds = map digitToInt prefix
          partial = luhnValue (ds ++ [0])
          check = (10 - (partial `mod` 10)) `mod` 10
      in Just (prefix ++ [intToDigit check])