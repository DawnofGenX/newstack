package {{ package_name }};

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

public class NotesStore {
    private final String url;

    public NotesStore(String jdbcUrl) {
        this.url = jdbcUrl;
        init();
    }

    private Connection connect() throws SQLException {
        return DriverManager.getConnection(url);
    }

    private void init() {
        try (Connection connection = connect();
             Statement statement = connection.createStatement()) {
            statement.execute("CREATE TABLE IF NOT EXISTS notes (title TEXT PRIMARY KEY, body TEXT NOT NULL)");
        } catch (SQLException error) {
            throw new IllegalStateException("unable to initialise notes table", error);
        }
    }

    public void add(String title, String body) {
        String sql = "INSERT INTO notes (title, body) VALUES (?, ?) "
                + "ON CONFLICT(title) DO UPDATE SET body = excluded.body";
        try (Connection connection = connect();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, title);
            statement.setString(2, body);
            statement.executeUpdate();
        } catch (SQLException error) {
            throw new IllegalStateException("unable to store note", error);
        }
    }

    public List<Note> list() {
        List<Note> notes = new ArrayList<>();
        try (Connection connection = connect();
             PreparedStatement statement = connection.prepareStatement("SELECT title, body FROM notes ORDER BY title");
             ResultSet resultSet = statement.executeQuery()) {
            while (resultSet.next()) {
                notes.add(new Note(resultSet.getString("title"), resultSet.getString("body")));
            }
        } catch (SQLException error) {
            throw new IllegalStateException("unable to list notes", error);
        }
        return notes;
    }

    public boolean delete(String title) {
        try (Connection connection = connect();
             PreparedStatement statement = connection.prepareStatement("DELETE FROM notes WHERE title = ?")) {
            statement.setString(1, title);
            return statement.executeUpdate() > 0;
        } catch (SQLException error) {
            throw new IllegalStateException("unable to delete note", error);
        }
    }
}