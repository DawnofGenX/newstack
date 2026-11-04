import { INestApplication } from "@nestjs/common";
import { Test } from "@nestjs/testing";
import request from "supertest";
import { AppModule } from "../src/app.module.js";

describe("App (e2e)", () => {
  let app: INestApplication;

  beforeAll(async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleRef.createNestApplication();
    await app.init();
  });

  afterAll(async () => {
    await app.close();
  });

  it("greets on /", async () => {
    const response = await request(app.getHttpServer()).get("/");
    expect(response.status).toBe(200);
    expect(response.body).toEqual({ message: "Hello from {{ npm_name }}" });
  });

  it("counts text on /stats", async () => {
    const response = await request(app.getHttpServer())
      .get("/stats")
      .query({ text: "hello world" });
    expect(response.status).toBe(200);
    expect(response.body).toEqual({ lines: 0, words: 2, bytes: 11 });
  });

  it("counts newlines and UTF-8 bytes on /stats", async () => {
    const response = await request(app.getHttpServer())
      .get("/stats")
      .query({ text: "a\nb" });
    expect(response.status).toBe(200);
    expect(response.body).toEqual({ lines: 1, words: 2, bytes: 3 });
  });

  it("rejects /stats without text with 400", async () => {
    const response = await request(app.getHttpServer()).get("/stats");
    expect(response.status).toBe(400);
    expect(response.body).toEqual({
      message: "text is required",
      error: "Bad Request",
      statusCode: 400,
    });
  });
});
