pub mod contract;
pub mod counts;
pub mod routes;

use actix_web::{web, App, HttpServer};

pub fn app_cfg(cfg: &mut web::ServiceConfig) {
    // `web::route()` = any-method (there is no `web::any()` in actix-web 4).
    // The handler is method-agnostic: contract::dispatch produces the JSON
    // 405/422 bodies itself, so actix's plain-text defaults never surface.
    cfg.route("/health", web::route().to(routes::handler))
        .route("/stats", web::route().to(routes::handler))
        .default_service(web::to(routes::not_found));
}

pub async fn run(addr: &str) -> std::io::Result<()> {
    HttpServer::new(|| App::new().configure(app_cfg))
        .bind(addr)?
        .run()
        .await
}
