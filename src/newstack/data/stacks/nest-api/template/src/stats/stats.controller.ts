import { Controller, Get, Query } from "@nestjs/common";
import { StatsService, TextStats } from "./stats.service.js";
import { TextQueryPipe } from "./text-query.pipe.js";

@Controller()
export class StatsController {
  constructor(private readonly stats: StatsService) {}

  @Get()
  greeting(): { message: string } {
    return { message: "Hello from {{ npm_name }}" };
  }

  @Get("stats")
  getStats(@Query("text", new TextQueryPipe()) text: string): TextStats {
    return this.stats.count(text);
  }
}
