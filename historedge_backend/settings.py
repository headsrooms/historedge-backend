from secrets import token_urlsafe

from starlette.config import Config

# Config will be read from environment variables and/or ".env" files.
from starlette.datastructures import Secret

config = Config(".env")

DEBUG = config("DEBUG", cast=bool, default=False)
TESTING = config("TESTING", cast=bool, default=False)
HTTPS_ONLY = config("HTTPS_ONLY", cast=bool, default=False)
GZIP_COMPRESSION = config("GZIP", cast=bool, default=False)
SECRET = config("SECRET", cast=Secret, default=token_urlsafe(10))

REDIS_HOST = config("REDIS_HOST", cast=str, default="redis")
REDIS_PORT = config("REDIS_PORT", cast=int, default=6379)
DB_URL = config("DB_URL", cast=str, default="sqlite://db.sqlite")
GENERATE_SCHEMAS = config("GENERATE_SCHEMAS", cast=bool, default=True)

# The Sentry DSN is a unique identifier for our app when connecting to Sentry
# See https://docs.sentry.io/platforms/python/#connecting-the-sdk-to-sentry
SENTRY_DSN = config("SENTRY_DSN", cast=str, default="")
RELEASE_VERSION = config("RELEASE_VERSION", cast=str, default="<local dev>")

DB_USER = config("POSTGRES_USER", cast=str)
DB_PASSWORD = config("POSTGRES_PASSWORD", cast=str)
DB_HOST = config("POSTGRES_SERVER", cast=str)
DB_PORT = config("POSTGRES_PORT", cast=str)
DB_NAME = config("POSTGRES_DB", cast=str)

HISTORY_DISTRIBUTOR_CHUNK_LENGTH = config("HISTORY_DISTRIBUTOR_CHUNK_LENGTH", cast=int)

if SENTRY_DSN:  # pragma: nocover
    import sentry_sdk

    sentry_sdk.init(dsn=SENTRY_DSN, release=RELEASE_VERSION)

if DEBUG:
    DB_URL = "sqlite://db.sqlite"
else:
    DB_URL = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

HEADLESS = config("HEADLESS", cast=bool, default=True)
SCRAPER_ITEMS_PER_READ = config("SCRAPER_ITEMS_PER_READ", cast=int, default=5)
SCRAPER_STEALTH = config("SCRAPER_STEALTH", cast=bool, default=False)
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/83.0.4103.97 Safari/537.36'
BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--single-process",
    "--disable-dev-shm-usage",
    "--disable-web-security",
    "--disable-gpu",
    "--mute-audio",
    "--no-zygote",
    "--window-position=0,0",
    "--ignore-certificate-errors-spki-list",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-client-side-phishing-detection",
    "--no-first-run",
    "--safebrowsing-disable-auto-update",
    "--disable-translate",
    "--disable-popup-blocking",
    "--disable-hang-monitor",
    "--disable-sync",
    USER_AGENT,
]