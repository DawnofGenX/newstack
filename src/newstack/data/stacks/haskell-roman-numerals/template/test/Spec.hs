module Main (main) where

import Harness (checkEqual, summary)
import Roman.Numeral

main :: IO ()
main = do
  results <- sequence
    [ checkEqual "encode 1" (Right "I") (toRoman 1)
    , checkEqual "encode 1990" (Right "MCMXC") (toRoman 1990)
    , checkEqual "encode 3999" (Right "MMMCMXCIX") (toRoman 3999)
    , checkEqual "decode MCMXC" (Right 1990) (fromRoman "MCMXC")
    , checkEqual "decode IV" (Right 4) (fromRoman "IV")
    , checkEqual "range low fails" (Left "out of range: expected 1..3999") (toRoman 0)
    , checkEqual "invalid numeral fails" (Left "invalid roman numeral") (fromRoman "IIII")
    , checkEqual "bad char fails" (Left "invalid character") (fromRoman "IXXZ")
    ]
  summary results
