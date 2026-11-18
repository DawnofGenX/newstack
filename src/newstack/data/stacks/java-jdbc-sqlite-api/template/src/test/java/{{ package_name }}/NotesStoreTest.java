package {{ package_name }};

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Path;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class NotesStoreTest {
    @TempDir
    Path tempDir;

    @Test
    void storesListsAndDeletesNotes() {
        NotesStore store = new NotesStore("jdbc:sqlite:" + tempDir.resolve("notes.db"));
        store.add("first", "hello");
        store.add("second", "world");
        store.add("first", "updated");

        List<Note> notes = store.list();
        assertEquals(2, notes.size());
        assertEquals("first", notes.get(0).title());
        assertEquals("updated", notes.get(0).body());

        assertTrue(store.delete("first"));
        assertFalse(store.delete("missing"));
        assertEquals(1, store.list().size());
    }
}