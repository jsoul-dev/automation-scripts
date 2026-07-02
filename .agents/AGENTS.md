# Rules for `jsoul-dev/automation-scripts`

All agents working within this repository MUST adhere to the following rules:

1. **Conventional Commits**: Every git commit MUST follow the industry-standard "Conventional Commits" format (`type(scope): description`).
   - Use types like `feat`, `fix`, `docs`, `chore`, `refactor`, `ci`, `config`.
   - The `(scope)` MUST be the name of the script/folder being modified (e.g., `feat(idle-locker)`, `docs(tbh-decorator)`). If the change affects the root repository, use `(repo)` (e.g., `docs(repo)`).

2. **Semantic Version Bumping**: If you modify a script file that contains a version string (e.g., `global Version := "1.0.0"` in `.ahk` files, or `__version__ = "1.0.0"` in `.py` files), you MUST bump the version number before committing. Use standard Semantic Versioning (SemVer) rules (MAJOR.MINOR.PATCH).
   - **IMPORTANT**: When you bump a version in a script, you MUST also bump the `Current Version: **X.Y.Z**` string inside that script's `README.md` file!

3. **Automated Deployment**: When deploying changes or pushing to GitHub, remember that this repository utilizes an automated CI/CD pipeline to publish script updates directly to GitHub Releases.
