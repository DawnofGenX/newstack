package textstat;

/** What a POST body turned out to be. */
enum TextKind {
	Invalid;
	Missing;
	Text(value:String);
}
