package com.example.textstat;

import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** Exposes the wc-style counts over HTTP. */
@RestController
public class StatsController {

    private final StatsService statsService;

    public StatsController(StatsService statsService) {
        this.statsService = statsService;
    }

    /** GET /stats?text=... returns the wc-style counts of the text as JSON. */
    @GetMapping("/stats")
    public Stats stats(@RequestParam("text") String text) {
        return statsService.count(text);
    }

    /** GET / returns a hello message. */
    @GetMapping("/")
    public Map<String, String> hello() {
        return Map.of("message", "hello");
    }
}
