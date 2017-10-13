import os

import guild.cmd_support
import guild.package

def create_package(args, ctx):
    project_dir = args.project_location or "."
    package_file = os.path.join(project_dir, "PACKAGE")
    if not os.path.exists(package_file):
        guild.cli.error(
            "a PACKAGE file does not exist in %s\n%s"
            % (guild.cmd_support.project_location_desc(project_dir),
               guild.cmd_support.try_project_location_help(project_dir, ctx)))
    guild.package.create_package(
        package_file,
        dist_dir=args.dist_dir,
        upload=args.upload,
        sign=args.sign,
        identity=args.identity,
        user=args.user,
        password=args.password,
        comment=args.comment)
