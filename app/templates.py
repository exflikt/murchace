import os
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Protocol

import jinja2
from fastapi import Request
from fastapi.datastructures import URL
from jinja2.ext import debug as debug_ext

from .env import DEBUG

TEMPLATES_DIR = Path("app/templates")


env = jinja2.Environment(
    extensions=[debug_ext] if DEBUG else [],
    undefined=jinja2.StrictUndefined,
    autoescape=True,
    loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
)
globals: dict[str, Any] = {"DEBUG": DEBUG}


@jinja2.pass_context
def _url_for(context: dict[str, Any], name: str, /, **path_params: Any) -> URL:
    request: Request = context["request"]
    return request.url_for(name, **path_params)


env.globals.setdefault("url_for", _url_for)


def load_macro(template: jinja2.Template, macro_name: str) -> jinja2.runtime.Macro:
    macro = getattr(template.module, macro_name)
    if not isinstance(macro, jinja2.runtime.Macro):
        raise Exception(f"{macro} is not a jinja2.runtime.Macro instance")
    return macro


def hyphen_path_to_underscore_stem(path: str | os.PathLike[str]) -> str:
    return Path(path).stem.replace("-", "_")


class _MacroArgHints[**P](Protocol):
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> None: ...


class _RenderMacroWithRequest[**P](Protocol):
    def __call__(self, request: Request, *args: P.args, **kwargs: P.kwargs) -> str: ...


def macro_template[**P](
    name: str, macro_name: str | None = None
) -> Callable[[_MacroArgHints[P]], _RenderMacroWithRequest[P]]:
    if macro_name is None:
        macro_name = hyphen_path_to_underscore_stem(name)

    def type_signature(fn: _MacroArgHints[P]) -> _RenderMacroWithRequest[P]:
        @wraps(fn)
        def with_request(request: Request, *args: P.args, **kwargs: P.kwargs) -> str:
            template = env.get_template(name, globals={"request": request, **globals})
            return load_macro(template, macro_name)(*args, **kwargs)

        return with_request

    return type_signature


@macro_template("layout.html")
def layout(
    title: str = "murchace", head: str = "", caller: Callable[[], str] = lambda: ""
): ...


@macro_template("hx-post.html")
def hx_post(path: str): ...
