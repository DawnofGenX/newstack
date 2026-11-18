package {{ package_name }};

import org.junit.jupiter.api.Test;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class CsvMapperTest {
    @Test
    void parsesValidRows() {
        String csv = "name,age,email\nAda,30,ada@example.com\nBob,25,bob@example.com\n";
        List<Person> people = CsvMapper.parse(csv);
        assertEquals(2, people.size());
        assertEquals(new Person("Ada", 30, "ada@example.com"), people.get(0));
    }

    @Test
    void badColumnCountThrows() {
        String csv = "name,age,email\nAda,30\n";
        assertThrows(IllegalArgumentException.class, () -> CsvMapper.parse(csv));
    }

    @Test
    void missingHeaderThrows() {
        String csv = "\nAda,30,ada@example.com\n";
        assertThrows(IllegalArgumentException.class, () -> CsvMapper.parse(csv));
    }

    @Test
    void wrongTypeThrows() {
        String csv = "name,age,email\nAda,not-a-number,ada@example.com\n";
        assertThrows(IllegalArgumentException.class, () -> CsvMapper.parse(csv));
    }

    @Test
    void missingRequiredHeaderThrows() {
        String csv = "name,age\nAda,30\n";
        assertThrows(IllegalArgumentException.class, () -> CsvMapper.parse(csv));
    }
}
