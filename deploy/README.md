# GitHub Actions deployment

Pull requests run tests on Python 3.12. Pushes to main run tests, then SSH into
the existing server checkout, pull main with `--ff-only`, install dependencies
in `/var/www/upload/venv`, rerun tests, gracefully reload `upload.service`, and
check localhost. Deployments are serialized and refuse a dirty checkout.
Superseded workflows skip deployment rather than pull an untested newer commit.

The server uses an `upload-deploy` account. Its authorized key is restricted to
the root-owned `/usr/local/bin/deploy-upload` command, with forwarding disabled.
The account can sudo only `/usr/bin/systemctl reload upload.service`.
Install `deploy/deploy-upload` root-owned, mode 755, at that location.
The service needs an `ExecReload=/bin/kill -HUP $MAINPID` directive.

Configure these repository Actions secrets:

- `DEPLOY_SSH_KEY`: the dedicated deployment private key; never commit it.
- `DEPLOY_KNOWN_HOSTS`: the verified server SSH host-key entry for
  `pointlessapi.com`. Obtain it through the existing trusted SSH connection,
  not an unverified scan in the workflow.

Keep `.env` untracked and uploads in `/var/lib/upload/files`. Only the deployment
account should own the checkout and its venv; the `upload` service account needs
read access to code and `.env`, and write access to uploaded files.

This is in-place deployment: dependency installation or a failed test can leave
the checkout ahead of the running app. There is no automatic rollback. Changes to
Gunicorn itself or the systemd unit need a separate service restart or daemon
reload. Normal app deployments gracefully reload Gunicorn workers.
