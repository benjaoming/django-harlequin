import os
import subprocess

from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            choices=tuple(connections),
            help=(
                'Nominates a database to synchronize. Defaults to the "default" '
                "database."
            ),
        )
        parameters = parser.add_argument_group("parameters", prefix_chars="--")
        parameters.add_argument("parameters", nargs="*")

    def handle(self, *args, **options):
        database = options["database"]
        parameters = options["parameters"]

        command = ["harlequin"]
        env = {}

        connection = connections[database]
        if connection.vendor == "postgresql":
            self.extend_command_env_postgres(connection, command, env)
        else:
            raise CommandError(
                f"Connection {database!r} has unsupported vendor {connection.vendor!r}."
            )

        # Pass through extra options
        command.extend(parameters)
        env = {**os.environ, **env} if env else None
        subprocess.run(command, check=True, env=env)

    def extend_command_env_postgres(self, connection, command, env):
        command.extend(["-a", "postgres"])

        options = connection.settings_dict["OPTIONS"]

        host = connection.settings_dict.get("HOST")
        port = connection.settings_dict.get("PORT")
        dbname = connection.settings_dict.get("NAME")
        user = connection.settings_dict.get("USER")
        passwd = connection.settings_dict.get("PASSWORD")
        passfile = options.get("passfile")
        service = options.get("service")
        sslmode = options.get("sslmode")
        sslrootcert = options.get("sslrootcert")
        sslcert = options.get("sslcert")
        sslkey = options.get("sslkey")

        if not dbname and not service:  # pragma: no branch
            # Connect to the default 'postgres' db.
            dbname = "postgres"
        if user:
            command += ["--user", user]
        if host:
            command += ["--host", host]
        if port:
            command += ["--port", str(port)]
        if dbname:
            command += ["--dbname", dbname]

        if passwd:
            env["PGPASSWORD"] = str(passwd)
        if service:  # pragma: no branch
            env["PGSERVICE"] = str(service)
        if sslmode:  # pragma: no branch
            env["PGSSLMODE"] = str(sslmode)
        if sslrootcert:  # pragma: no branch
            env["PGSSLROOTCERT"] = str(sslrootcert)
        if sslcert:  # pragma: no branch
            env["PGSSLCERT"] = str(sslcert)
        if sslkey:  # pragma: no branch
            env["PGSSLKEY"] = str(sslkey)
        if passfile:  # pragma: no branch
            env["PGPASSFILE"] = str(passfile)
