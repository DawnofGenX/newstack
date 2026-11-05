package {{ package_name }}

import java.nio.charset.StandardCharsets
import upickle.default.*

/** A status and a JSON document: the whole HTTP surface without a socket. */
final case class Reply(status: Int, body: String)

object Contract:
  private def countsJson(text: String, counts: Counts): String =
    ujson
      .Obj(
        "text" -> text,
        "lines" -> counts.lines,
        "words" -> counts.words,
        "bytes" -> counts.bytes
      )
      .render()

  private def error(status: Int, code: String, detail: Option[String]): Reply =
    val fields = scala.collection.mutable.LinkedHashMap[String, ujson.Value](
      "error" -> ujson.Str(code)
    )
    detail.foreach(d => fields += "detail" -> ujson.Str(d))
    Reply(status, ujson.Obj.from(fields.toSeq).render())

  private def queryParam(query: String, name: String): Option[String] =
    query
      .split("&")
      .toList
      .filter(_.nonEmpty)
      .flatMap { pair =>
        pair.split("=", 2).toList match
          case key :: value :: Nil if decode(key) == name => Some(decode(value))
          case key :: Nil if decode(key) == name          => Some("")
          case _                                          => None
      }
      .headOption

  private def decode(raw: String): String =
    java.net.URLDecoder.decode(raw.replace("+", "%20"), StandardCharsets.UTF_8)

  private def textBody(body: String): Either[String, Option[String]] =
    try
      ujson.read(body) match
        case obj: ujson.Obj =>
          obj.value.get("text") match
            case Some(ujson.Str(text)) => Right(Some(text))
            case Some(_)               => Right(None)
            case None                  => Right(None)
        case _ => Left("the request body must be a JSON object")
    catch case _: Throwable => Left("the request body must be a JSON object")

  def route(method: String, path: String, query: String, body: String): Reply =
    (method.toUpperCase, path) match
      case ("GET", "/health") => Reply(200, """{"status":"ok"}""")
      case ("GET", "/stats")  =>
        queryParam(query, "text") match
          case Some(text) => Reply(200, countsJson(text, Counts.of(text)))
          case None       =>
            error(
              422,
              "missing_text",
              Some("the `text` query parameter is required")
            )
      case ("POST", "/stats") =>
        textBody(body) match
          case Right(Some(text)) =>
            Reply(200, countsJson(text, Counts.of(text)))
          case Right(None) =>
            error(422, "missing_text", Some("`text` must be a string"))
          case Left(detail) => error(422, "invalid_json", Some(detail))
      case (_, "/health" | "/stats") =>
        error(405, "method_not_allowed", None)
      case _ =>
        error(404, "not_found", Some(s"no route for $method $path"))
