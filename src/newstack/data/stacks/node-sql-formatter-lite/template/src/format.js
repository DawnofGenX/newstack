const KEYWORDS = ["select","from","where","and","or","insert","into","values","update","set","delete","order","by","group","having","join","left","right","inner","outer","on","as","limit","offset","create","table","primary","key","not","null","default","distinct","count","sum","avg","min","max"];

export function formatSql(input) {
  let s = String(input).trim();
  // normalize whitespace
  s = s.replace(/\s+/g, " ");
  // uppercase keywords (word boundaries)
  const re = new RegExp("\\b(" + KEYWORDS.join("|") + ")\\b", "gi");
  s = s.replace(re, (m) => m.toUpperCase());
  if (!s.endsWith(";")) s += ";";
  return s;
}