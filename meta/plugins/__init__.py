from cutekit import ensure

ensure((0, 7, 0))

import http.server
import os
from pathlib import Path
import markdown
import dataclasses as dt
from dataclasses_json import DataClassJsonMixin

from cutekit import cli, const, shell, jexpr

CAT = "ᓚ₍ ^. .^₎"
DEFAULT_STYLE_PATH = __file__.replace("__init__.py", "default.css")

SITE_DIR = os.path.join(const.META_DIR, "site")
SITE_BUILD_DIR = os.path.join(const.BUILD_DIR, "site")


# MARK: Model ------------------------------------------------------------------


def readFile(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


def writeFile(path: str, content: str):
    with open(path, "w") as f:
        f.write(content)


def fixupLinks(html: str, path: str) -> str:
    rootPath = os.path.relpath(".", os.path.dirname(path))
    return (
        html.replace('.md"', '.html"')
        .replace(".md#", ".html#")
        .replace('"/', f'"{rootPath}/')
    )


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
        siteFile = os.path.join(SITE_DIR, "site.json")
        siteJson = jexpr.include(Path(siteFile))
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

    def renderAll(self, out: str):
        styleFile = os.path.join(SITE_DIR, "style.css")
        if not os.path.exists(styleFile):
            styleFile = DEFAULT_STYLE_PATH

        style = readFile(styleFile)

        md = markdown.Markdown(extensions=["meta"])
        files = shell.find(SITE_DIR)
        for file in files:
            if file.endswith(".json"):
                continue

            relDir = file.replace(SITE_DIR + "/", "")
            print(f"Processing {relDir}")
            output = os.path.join(out, relDir)
            if not file.endswith(".md"):
                shell.mkdir(os.path.dirname(output))
                shell.cp(file, out)
                continue

            output = output.replace(".md", ".html")

            print(f"Rendering {file} -> {output}")

            shell.mkdir(os.path.dirname(output))

            mdContent = readFile(path=file)
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
def _() -> None:
    shell.rmrf(SITE_BUILD_DIR)
    shell.mkdir(SITE_BUILD_DIR)
    site = Site.load()
    site.renderAll(SITE_BUILD_DIR)

    print(f"{CAT} Site built at {SITE_BUILD_DIR}")


@cli.command("c", "cat/clean", "Clean the site")
def _():
    shell.rmrf(SITE_BUILD_DIR)

    print(f"{CAT} Site cleaned")


@cli.command("s", "cat/serve", "Serve the site")
def _():
    shell.rmrf(SITE_BUILD_DIR)
    shell.mkdir(SITE_BUILD_DIR)
    site = Site.load()
    site.renderAll(SITE_BUILD_DIR)

    os.chdir(SITE_BUILD_DIR)

    print(f"{CAT} Serving site")
    shell.exec("python3", "-m", "http.server")


@cli.command("e", "cat/init", "Initialize the site")
def _():
    shell.mkdir(SITE_DIR)
    writeFile(
        os.path.join(SITE_DIR, "site.json"),
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
        os.path.join(SITE_DIR, "index.md"),
        """
This is the home page of the site. You can edit this file to change the content of the home page.
""",
    )

    print(f"{CAT} Site initialized at {SITE_DIR}")
