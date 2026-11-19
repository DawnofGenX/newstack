module Roman.Numeral (toRoman, fromRoman) where

toRoman :: Int -> Either String String
toRoman n
  | n < 1 || n > 3999 = Left "out of range: expected 1..3999"
  | otherwise = Right (rep 1000 "M" n' ++ group 100 "C" "D" "M" h ++ group 10 "X" "L" "C" t ++ group 1 "I" "V" "X" o)
  where
    n' = n
    (h, t, o) = (n `div` 100 `mod` 10, n `div` 10 `mod` 10, n `mod` 10)
    rep k s x = replicate (x `div` k) (head s)
    group unit one five ten digit =
      case digit of
        0 -> ""
        1 -> one
        2 -> one ++ one
        3 -> one ++ one ++ one
        4 -> one ++ five
        5 -> five
        6 -> five ++ one
        7 -> five ++ one ++ one
        8 -> five ++ one ++ one ++ one
        9 -> one ++ ten
        _ -> ""

romanValue :: Char -> Int
romanValue 'I' = 1
romanValue 'V' = 5
romanValue 'X' = 10
romanValue 'L' = 50
romanValue 'C' = 100
romanValue 'D' = 500
romanValue 'M' = 1000
romanValue _ = 0

isRoman :: Char -> Bool
isRoman c = c `elem` "IVXLCDM"

parseRoman :: String -> Int
parseRoman [] = 0
parseRoman [x] = romanValue x
parseRoman (a:b:rest)
  | romanValue a < romanValue b = romanValue b - romanValue a + parseRoman rest
  | otherwise = romanValue a + parseRoman (b : rest)

fromRoman :: String -> Either String Int
fromRoman [] = Left "empty numeral"
fromRoman s
  | any (not . isRoman) s = Left "invalid character"
  | otherwise =
      let n = parseRoman s
      in case toRoman n of
           Right s' | s' == s -> Right n
           _ -> Left "invalid roman numeral"
