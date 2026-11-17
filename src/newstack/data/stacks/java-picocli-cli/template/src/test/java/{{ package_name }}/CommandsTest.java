package {{ package_name }};

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class CommandsTest {

    @Test
    void greetDefault() {
        assertEquals("Hello, world!", Commands.greet(null));
        assertEquals("Hello, world!", Commands.greet("   "));
    }

    @Test
    void greetNamed() {
        assertEquals("Hello, smoke!", Commands.greet("smoke"));
    }

    @Test
    void add() {
        assertEquals(11, Commands.add(4, 7));
    }
}