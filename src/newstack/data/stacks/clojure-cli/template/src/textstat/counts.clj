(ns textstat.counts)

;; Which figures to print. `wc` prints all three when given no flag.
(def all-figures {:lines true :words true :bytes true})
(def no-figures  {:lines false :words false :bytes false})

(def empty-counts {:lines 0 :words 0 :bytes 0})

;; The same whitespace set `wc` uses: space, tab, newline, vertical tab,
;; form feed and carriage return.
(defn space? [b]
  (or (= b 32) (= b 9) (= b 10) (= b 11) (= b 12) (= b 13)))

;; A tally: newline bytes, maximal runs of non-whitespace, raw bytes.
(defn add [a b]
  {:lines (+ (:lines a) (:lines b))
   :words (+ (:words a) (:words b))
   :bytes (+ (:bytes a) (:bytes b))})

;; Count raw bytes so the numbers match `wc -l -w -c` on the same file.
;; A line is a `\n` byte, so a last line without a trailing newline is not
;; counted; a word is a maximal run of non-whitespace bytes; bytes are bytes,
;; not characters.
(defn of-bytes [data]
  (loop [i 0 lines 0 words 0 in-word false]
    (if (= i (alength data))
      {:lines lines :words words :bytes (alength data)}
      (let [b (bit-and (aget data i) 0xff)]
        (recur (inc i)
               (if (= b 10) (inc lines) lines)
               (if (space? b) words (if in-word words (inc words)))
               (if (space? b) false true))))))

;; The printed columns, in `wc` order, for the figures that were asked for.
(defn columns [figures counts]
  (vec (remove nil?
        [(when (:lines figures) (:lines counts))
         (when (:words figures) (:words counts))
         (when (:bytes figures) (:bytes counts))])))

;; The column width `wc` uses: the widest figure printed anywhere in the output.
(defn width [rows figures]
  (apply max 0 (map #(count (str %)) (mapcat #(columns figures %) rows))))

;; Right-align every column to `width`, the way `wc` lines up its output.
(defn format-row [figures counts label width]
  (let [cells (columns figures counts)
        padded (mapv #(str (apply str (replicate (max 0 (- width (count (str %)))) " ")) %) cells)]
    (str (apply str (interpose " " padded)) " " label)))
