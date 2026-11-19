module Main (main) where

import System.Environment (getArgs)
import System.Exit (ExitCode (..), exitWith)
import Roman.Numeral (toRoman, fromRoman)

usage :: String
usage =
  "Usage: {{ npm_name }} [OPTION]...\n" ++
  "Roman numeral tools.\n" ++
  "  --encode N   format N as a Roman numeral\n" ++
  "  --decode S   parse a Roman numeral\n" ++
  "  -h, --help   print this help\n" ++
  "  -V, --version print the version\n"

main :: IO ()
main = do
  args <- getArgs
  case args of
    ["-h"] -> putStrLn usage >> exitWith ExitSuccess
    ["--help"] -> putStrLn usage >> exitWith ExitSuccess
    ["-V"] -> putStrLn "0.1.0" >> exitWith ExitSuccess
    ["--version"] -> putStrLn "0.1.0" >> exitWith ExitSuccess
    ["--encode", n] ->
      case reads n of
        [(x, "")] ->
          case toRoman x of
            Right r -> putStrLn r >> exitWith ExitSuccess
            Left e -> putStrLn ("{{ npm_name }}: " ++ e) >> exitWith (ExitFailure 1)
        _ -> putStrLn ("{{ npm_name }}: invalid number: " ++ n) >> exitWith (ExitFailure 1)
    ["--decode", s] ->
      case fromRoman s of
        Right n -> print n >> exitWith ExitSuccess
        Left e -> putStrLn ("{{ npm_name }}: " ++ e) >> exitWith (ExitFailure 1)
    _ -> putStrLn usage >> exitWith (ExitFailure 2)
