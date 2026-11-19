module Main (main) where

import System.Environment (getArgs)
import System.Exit (ExitCode (..), exitWith)
import Luhn (luhnValid, luhnGenerate)

main :: IO ()
main = do
  args <- getArgs
  case args of
    ["--help"] -> do
      putStrLn "Usage: luhn validate NUMBER"
      putStrLn "       luhn generate PREFIX"
      exitWith ExitSuccess
    ["validate", n] -> do
      if luhnValid n
        then do putStrLn "valid"; exitWith ExitSuccess
        else do putStrLn "invalid"; exitWith (ExitFailure 1)
    ["generate", p] -> do
      case luhnGenerate p of
        Just full -> do putStrLn full; exitWith ExitSuccess
        Nothing -> do putStrLn "invalid prefix"; exitWith (ExitFailure 1)
    _ -> do
      putStrLn "Usage: luhn validate NUMBER"
      putStrLn "       luhn generate PREFIX"
      exitWith (ExitFailure 2)