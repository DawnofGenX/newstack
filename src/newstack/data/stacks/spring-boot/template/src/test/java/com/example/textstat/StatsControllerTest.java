package com.example.textstat;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(StatsController.class)
@Import(StatsService.class)
class StatsControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @DisplayName("GET /stats returns wc-style counts as JSON")
    void statsEndpoint() throws Exception {
        mockMvc.perform(get("/stats").param("text", "one two\nthree\n"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.lines").value(2))
            .andExpect(jsonPath("$.words").value(3))
            .andExpect(jsonPath("$.bytes").value(14));
    }

    @Test
    @DisplayName("GET / returns a hello message")
    void helloEndpoint() throws Exception {
        mockMvc.perform(get("/"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.message").value("hello"));
    }
}
