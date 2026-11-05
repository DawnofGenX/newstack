package {{ package_name }}

import cask.model.{QueryParams, Request, Response}

/** Cask is the HTTP layer; every routing decision lives in `Contract.route`. */
object Server extends cask.MainRoutes:
  override def host: String = "127.0.0.1"

  override def port: Int =
    sys.env.get("PORT").flatMap(_.toIntOption).getOrElse(8080)

  override def verbose: Boolean = false

  @cask.route(
    "/",
    methods = Seq("get", "post", "put", "patch", "delete", "head", "options"),
    subpath = true
  )
  def any(request: Request, params: QueryParams): Response[String] =
    val QueryParams(_) = params
    val exchange = request.exchange
    val reply = Contract.route(
      exchange.getRequestMethod.toString,
      exchange.getRequestURI,
      Option(exchange.getQueryString).getOrElse(""),
      request.text()
    )
    Response(
      reply.body,
      statusCode = reply.status,
      headers = Seq("content-type" -> "application/json")
    )

  initialize()
