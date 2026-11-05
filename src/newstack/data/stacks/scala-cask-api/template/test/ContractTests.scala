import utest.*

import {{ package_name }}.{Contract, Counts}

object ContractTests extends TestSuite:
  val tests = Tests {
    test("counts an empty string as nothing") {
      assert(Counts.of("") == Counts(0, 0, 0))
    }
    test("counts one line") {
      assert(Counts.of("hello world\n") == Counts(1, 2, 12))
    }
    test("counts blank lines as lines") {
      assert(Counts.of("\n\nx\n") == Counts(3, 1, 4))
    }
    test("does not count whitespace as words") {
      assert(Counts.of("  \t ") == Counts(0, 0, 4))
    }
    test("counts utf-8 bytes, not characters") {
      assert(Counts.of("héllo wörld\n") == Counts(1, 2, 14))
    }
    test("counts an emoji as four bytes") {
      assert(Counts.of("🙂\n") == Counts(1, 1, 5))
    }
    test("health") {
      val reply = Contract.route("GET", "/health", "", "")
      assert(reply.status == 200, reply.body == """{"status":"ok"}""")
    }
    test("get stats") {
      val reply = Contract.route("GET", "/stats", "text=hello+world%0A", "")
      assert(
        reply.status == 200,
        reply.body.contains(""""lines":1"""),
        reply.body.contains(""""words":2"""),
        reply.body.contains(""""bytes":12"""),
        reply.body.contains(""""text":"hello world\n"""")
      )
    }
    test("get stats without text") {
      val reply = Contract.route("GET", "/stats", "", "")
      assert(reply.status == 422, reply.body.contains("""missing_text"""))
    }
    test("post stats") {
      val reply =
        Contract.route("POST", "/stats", "", """{"text":"a b\nc\n"}""")
      assert(reply.status == 200, reply.body.contains(""""words":3"""))
    }
    test("post a non string text") {
      val reply = Contract.route("POST", "/stats", "", """{"text":42}""")
      assert(reply.status == 422, reply.body.contains("""missing_text"""))
    }
    test("post broken json") {
      val reply = Contract.route("POST", "/stats", "", "not json")
      assert(reply.status == 422, reply.body.contains("""invalid_json"""))
    }
    test("unknown route") {
      val reply = Contract.route("GET", "/nope", "", "")
      assert(
        reply.status == 404,
        reply.body.contains("""not_found"""),
        reply.body.contains("no route for GET /nope")
      )
    }
    test("known path, wrong method") {
      val reply = Contract.route("DELETE", "/health", "", "")
      assert(reply.status == 405, reply.body.contains("""method_not_allowed"""))
      val other = Contract.route("PUT", "/stats", "", "")
      assert(other.status == 405)
    }
  }
