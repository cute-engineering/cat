from cutekit import ensure

ensure((0, 7, 0))

import sys
import os
from pathlib import Path
import markdown
import dataclasses as dt
from dataclasses_json import DataClassJsonMixin

from cutekit import cli, const, shell, jexpr

CAT = "ᓚ₍ ^. .^₎"
DEFAULT_STYLE_PATH = Path(__file__).parent / "default.css"

SITE_DIR = Path(const.META_DIR) / "site"
SITE_BUILD_DIR = Path(const.BUILD_DIR) / "site"


# MARK: Model ------------------------------------------------------------------


def readFile(path: Path) -> str:
    with path.open("r", encoding="utf8") as f:
        return f.read()


def writeFile(path: Path, content: str):
    with path.open("w", encoding="utf8") as f:
        f.write(content)


def fixupLinks(html: str, path: Path) -> str:
    rootPath = os.path.relpath(".", path.parent)
    return (
        html.replace('.md"', '.html"')
        .replace(".md#", ".html#")
        .replace('"/', f'"{rootPath}/')
    )


class BuildArgs:
    theme: str = cli.arg(None, "theme", "Theme to use", default="default")


@dt.dataclass
class Site(DataClassJsonMixin):
    title: str = dt.field()
    header: str | None = dt.field(default=None)
    favicon: str = dt.field(default="🐱")
    navbar: str = dt.field(default="")
    footer: str = dt.field(default="")

    path: str = dt.field(default="")

    @staticmethod
    def load() -> "Site":
        siteFile = SITE_DIR / "site.json"
        siteJson = jexpr.include(siteFile)
        site = Site.from_dict(siteJson)
        site.path = siteFile
        return site

    def renderFavicon(self) -> str:
        svg = f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>{self.favicon}</text></svg>"
        urlEscape = str.maketrans({"#": "%23", "<": "%3C", ">": "%3E"})
        svgEscaped = svg.translate(urlEscape)
        return f"data:image/svg+xml,{svgEscaped}"

    def renderHeader(self) -> str:
        return f'<a href="/"><h1>{self.header or self.title}</h1></a>'

    def renderAll(self, out: Path, args: BuildArgs) -> None:
        style = ""
        style += readFile(Path(__file__).parent / f"{args.theme}.css")

        styleFile = SITE_DIR / "style.css"
        if styleFile.exists():
            style += "\n\n\n"
            style += readFile(styleFile)

        md = markdown.Markdown(extensions=["meta", "extra"])
        for file in SITE_DIR.rglob("*"):
            if file.is_dir() or file.suffix == ".json":
                continue

            relDir = file.relative_to(SITE_DIR)

            output = out / relDir
            if not file.suffix == ".md":
                output.parent.mkdir(parents=True, exist_ok=True)
                shell.cp(file, output)
                continue

            output = output.with_suffix(".html")

            print(f"Rendering {file} -> {output}")

            output.parent.mkdir(parents=True, exist_ok=True)

            mdContent = readFile(file)
            htmlContent = md.convert(mdContent)

            title = md.Meta.get("title", [""])[0]
            if title:
                title = f"{title} - {self.title}"
            else:
                title = self.title

            htmlContent = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="icon" href="{self.renderFavicon()}">
    <style>{style}</style>
</head>
<body>
    <header>
        {self.renderHeader()}
        <nav>{markdown.markdown(self.navbar)}</nav>
    </header>
    <main>
    {htmlContent}
    </main>
    <footer>
        {markdown.markdown(self.footer)}
    </footer>
</body>
</html>
"""

            writeFile(output, fixupLinks(htmlContent, relDir))


# MARK: Public interface -------------------------------------------------------


@cli.command(None, "cat", "Tiny site generator")
def _():
    pass


@cli.command("b", "cat/build", "Build the site")
def _(args: BuildArgs) -> None:
    shell.rmrf(SITE_BUILD_DIR)
    shell.mkdir(SITE_BUILD_DIR)
    site = Site.load()
    site.renderAll(SITE_BUILD_DIR, args)

    print(f"{CAT} Site built at {SITE_BUILD_DIR}")


@cli.command("c", "cat/clean", "Clean the site")
def _():
    shell.rmrf(SITE_BUILD_DIR)

    print(f"{CAT} Site cleaned")


@cli.command("s", "cat/serve", "Serve the site")
def _(args: BuildArgs):
    shell.rmrf(SITE_BUILD_DIR)
    SITE_BUILD_DIR.mkdir(parents=True)
    site = Site.load()
    site.renderAll(SITE_BUILD_DIR, args)

    print(f"{CAT} Serving site")
    shell.exec(sys.executable, "-m", "http.server", "-d", str(SITE_BUILD_DIR))


@cli.command("e", "cat/init", "Initialize the site")
def _():
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    writeFile(
        SITE_DIR / "site.json",
        """
{
    "favicon": "🐱",
    "title": "Cat",
    "header": "<span style=\\"white-space: nowrap;\\">ᓚ₍ ^. .^₎</span>",
    "navbar": "[Home](/)",
    "footer": "Built with [ᓚ₍ ^. .^₎](https://github.com/cute-engineering/cat)"
}
    """,
    )

    writeFile(
        SITE_DIR / "index.md",
        """
This is the home page of the site. You can edit this file to change the content of the home page.
""",
    )

    print(f"{CAT} Site initialized at {SITE_DIR}")
