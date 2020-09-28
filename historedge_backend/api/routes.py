from starlette.routing import Route

from historedge_backend.api.endpoints.bookmarks import bookmark_page, get_bookmarks
from historedge_backend.api.endpoints.history import register_history
from historedge_backend.api.endpoints.page_visits import (
    get_page_visits,
    distribute_page_visits_to_scraper,
)
from historedge_backend.api.endpoints.pages import visit_page, get_pages
from historedge_backend.api.endpoints.users import create_user

routes = [
    # users
    Route("/users/", create_user, methods=["POST"]),
    # pages
    Route("/pages/", visit_page, methods=["POST"]),
    Route("/pages/", get_pages, methods=["GET"]),
    # page_visits
    Route("/page-visits/", get_page_visits, methods=["GET"]),
    Route("/page-visits/", distribute_page_visits_to_scraper, methods=["POST"]),
    # history
    Route("/history/", register_history, methods=["POST"]),
    # bookmarks
    Route("/bookmarks/", bookmark_page, methods=["POST"]),
    Route("/bookmarks/", get_bookmarks, methods=["GET"]),
]
