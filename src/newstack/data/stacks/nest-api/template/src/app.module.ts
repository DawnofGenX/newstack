import { Module } from "@nestjs/common";
import { StatsModule } from "./stats/stats.module.js";

@Module({
  imports: [StatsModule],
})
export class AppModule {}
