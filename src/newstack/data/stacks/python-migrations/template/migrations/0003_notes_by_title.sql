-- Two statements, one of which is a trigger: its body is full of semicolons that
-- a naive splitter would treat as statement boundaries.
CREATE INDEX notes_by_title ON notes (title);

CREATE TRIGGER notes_touch AFTER UPDATE OF title ON notes
BEGIN
    UPDATE notes SET created_at = datetime('now') WHERE id = NEW.id;
END;
