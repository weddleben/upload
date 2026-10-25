import secrets

from app import app


@app.before_request
def fail_closed_if_unconfigured():
    """If no master password is configured, the server is misconfigured.

    Instead of accidentally running wide open, every request fails with
    a 500 that tells the user the server has a problem.
    """
    if not app.config.get("UPLOAD_MASTER_PASSWORD"):
        return (
            "server misconfigured: no upload password set "
            "(set UPLOAD_MASTER_PASSWORD in your .env)",
            500,
        )


def check_upload_password(provided: str) -> bool:
    """Constant-time comparison of the password sent with an upload
    against the master password from the environment / .env file.

    Password only — there is no username, no session, no cookie.
    """
    master = app.config.get("UPLOAD_MASTER_PASSWORD") or ""
    return secrets.compare_digest(provided.encode("utf-8"), master.encode("utf-8"))
