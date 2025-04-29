from typing import Annotated

from datastar_py.sse import ServerSentEventGenerator
from fastapi import APIRouter, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, StreamingResponse
from htpy import (
    Element,
    HTMLElement,
    a,
    aside,
    button,
    div,
    fieldset,
    figcaption,
    figure,
    form,
    img,
    input,
    label,
    li,
    main,
    ul,
)

from ..components import event_response, page_layout
from ..store import Product, ProductTable, delete_product

router = APIRouter()


def page_products(req: Request, products: list[Product]) -> HTMLElement:
    product_figures = [
        figure(
            id=f"product-{p.product_id}",
            class_="flex flex-col border-4 border-blue-400 rounded-md transition-colors ease-in-out active:bg-blue-300",
            data_on_click=f"@get('/products/{p.product_id}/editor')",
        )[
            img(
                src=str(req.url_for("static", path=p.filename)),
                alt=p.name,
                class_="mx-auto w-full h-auto aspect-square",
            ),
            figcaption(class_="text-center truncate")[p.name],
            div(class_="text-center")[p.price_str()],
        ]
        for p in products
    ]

    main_elm = main(
        class_="w-4/6 grid grid-cols-4 auto-cols-max auto-rows-min gap-2 py-2 pl-10 pr-6 overflow-y-scroll"
    )[
        *product_figures,
        figure(
            id="product-placeholder",
            class_="flex flex-col border-4 border-blue-400 rounded-md transition-colors ease-in-out active:bg-blue-300",
            data_on_click="@get('/product-editor')",
        )[
            img(
                src=str(req.url_for("static", path="no-image.png")),
                alt="新しい商品を追加",
                class_="mx-auto w-full h-auto aspect-square",
            ),
            figcaption(class_="text-center truncate")["新しい商品を追加する"],
            div(class_="text-center"),
        ],
    ]
    aside_elm = aside(class_="w-2/6 flex flex-col p-4")[
        ul(class_="flex flex-row py-2 justify-around items-center text-xl")[
            li(class_="grow")[
                a(
                    href="/",
                    class_="px-2 py-1 rounded-sm bg-gray-300 hidden lg:inline-block",
                )["ホーム"]
            ]
        ],
        div(id="product-editor", class_="grow flex flex-col justify-center")[
            div(class_="text-center")["編集する商品を選択してください"]
        ],
    ]

    return page_layout(
        req,
        div(class_="h-dvh flex flex-col")[
            div(class_="min-h-0 flex flex-row")[main_elm, aside_elm]
        ],
        title="商品編集 - murchace",
    )


def fragment_editor(req: Request, product: Product) -> Element:
    product_preview = div(id="product-preview", class_="grow")[
        figure(
            class_="w-2/3 mx-auto flex flex-col border-4 border-blue-400 rounded-md transition-colors ease-in-out active:bg-blue-300"
        )[
            img(
                src=str(req.url_for("static", path=product.filename)),
                alt=product.name,
                class_="mx-auto w-full h-auto aspect-square",
            ),
            figcaption(class_="text-center truncate")[product.name],
            div(class_="text-center")[product.price_str()],
        ]
    ]
    editor_form = form(
        data_on_submit=f"@post('/products/{product.product_id}', {{contentType: 'form'}})",
        class_="flex flex-col",
    )[
        fieldset(
            data_signals_product_id=product.product_id,
            data_signals_name=f'"{product.name}"',  # TODO: properly escape quotes
            data_signals_filename=f'"{product.filename}"',  # TODO: properly escape quotes
            data_signals_price=product.price,
            data_signals_no_stock=product.no_stock,
            class_="grid grid-cols-3 auto-rows-min justify-items-end gap-2 py-4 text-lg",
        )[
            label(for_="product-id", class_="w-full text-right")["商品番号:"],
            input(
                data_bind_product_id=True,
                type="number",
                id="product-id",
                name="id",
                class_="col-span-2 w-full",
            ),
            label(for_="product-name", class_="w-full text-right")["商品名:"],
            input(
                data_bind_name=True,
                type="text",
                id="product-name",
                name="name",
                class_="col-span-2 w-full",
            ),
            label(for_="product-filename", class_="w-full text-right")["ファイル名:"],
            input(
                data_bind_filename=True,
                type="text",
                id="product-filename",
                name="filename",
                class_="col-span-2 w-full",
            ),
            label(for_="product-price", class_="w-full text-right")["金額:"],
            input(
                data_bind_price=True,
                type="number",
                id="product-price",
                name="price",
                class_="col-span-2 w-full",
            ),
            label(for_="product-no-stock", class_="w-full text-right truncate")[
                "在庫数（未実装）:"
            ],
            input(
                data_bind_no_stock=True,
                type="text",
                id="product-no-stock",
                name="no-stock",
                class_="col-span-2 w-full",
            ),
        ],
        div(class_="flex flex-row justify-between")[
            button(
                data_on_click=f"confirm(`本当に「${{$name}}（{product.product_id}）」を削除しますか？`) && @delete('/products/{product.product_id}')",
                type="button",
                class_="px-2 py-1 text-white bg-red-500 rounded-lg",
            )["削除"],
            button(
                data_on_click=f"@get('/products/{product.product_id}/editor')",
                type="reset",
                class_="px-2 py-1 border border-black rounded-lg",
            )["リセット"],
            button(type="submit", class_="px-2 py-1 text-white bg-blue-500 rounded-lg")[
                "更新"
            ],
        ],
    ]

    return div(id="product-editor", class_="grow flex flex-col justify-center")[
        div(class_="h-full flex flex-col")[product_preview, editor_form]
    ]


def fragment_empty_editor(req: Request) -> Element:
    product_preview = div(id="product-preview", class_="grow")[
        figure(
            class_="w-2/3 mx-auto flex flex-col border-4 border-blue-400 rounded-md transition-colors ease-in-out active:bg-blue-300"
        )[
            img(
                src=str(req.url_for("static", path="no-image.png")),
                alt="仮画像",
                class_="mx-auto w-full h-auto aspect-square",
            ),
        ]
    ]
    editor_form = form(
        data_on_submit="@post('/products', {contentType: 'form'})",
        class_="flex flex-col",
    )[
        fieldset(
            class_="grid grid-cols-3 auto-rows-min justify-items-end gap-2 py-4 text-lg"
        )[
            label(for_="product-id", class_="w-full text-right")["商品番号:"],
            input(
                type="number",
                id="product-id",
                name="product_id",
                class_="col-span-2 w-full",
            ),
            label(for_="product-name", class_="w-full text-right")["商品名:"],
            input(
                type="text", id="product-name", name="name", class_="col-span-2 w-full"
            ),
            label(for_="product-filename", class_="w-full text-right")["ファイル名:"],
            input(
                type="text",
                id="product-filename",
                name="filename",
                value="no-image.png",
                class_="col-span-2 w-full",
            ),
            label(for_="product-price", class_="w-full text-right")["金額:"],
            input(
                type="number",
                id="product-price",
                name="price",
                value="0",
                class_="col-span-2 w-full",
            ),
            label(for_="product-no-stock", class_="w-full text-right truncate")[
                "在庫数（未実装）:"
            ],
            input(
                type="text",
                id="product-no-stock",
                name="no_stock",
                class_="col-span-2 w-full",
            ),
        ],
        div(class_="flex flex-row justify-between")[
            button(
                data_on_click="@get('/product-editor')",
                type="reset",
                class_="px-2 py-1 border border-black rounded-lg",
            )["リセット"],
            button(type="submit", class_="px-2 py-1 text-white bg-blue-500 rounded-lg")[
                "追加"
            ],
        ],
    ]

    return div(id="product-editor", class_="grow flex flex-col justify-center")[
        div(class_="h-full flex flex-col")[product_preview, editor_form]
    ]


@router.get("/products", response_class=HTMLResponse)
async def get_products(request: Request):
    products = await ProductTable.select_all()
    return HTMLResponse(page_products(request, products))


@router.post("/products", response_class=Response)
async def new_product(
    product_id: Annotated[int, Form()],
    name: Annotated[str, Form(max_length=40)],
    filename: Annotated[str, Form(max_length=100)],
    price: Annotated[int, Form()],
    no_stock: Annotated[int | None, Form()] = None,
):
    new_product = Product(
        product_id=product_id,
        name=name,
        filename=filename,
        price=price,
        no_stock=no_stock,
    )
    maybe_product = await ProductTable.insert(new_product)

    # TODO: report back that the operation has been completed successfully or
    # failed in the process depending on the value of `maybe_product`
    _ = maybe_product
    # if (product := maybe_product) is None:
    #     detail = f"Product {product_id} not updated"
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    #
    # # return event_Response(product_card(product))

    return event_response(ServerSentEventGenerator.execute_script("location.reload()"))


@router.post("/products/{prev_product_id}")
async def update_product(
    prev_product_id: int,
    product_id: Annotated[int, Form()],
    name: Annotated[str, Form(max_length=40)],
    filename: Annotated[str, Form(max_length=100)],
    price: Annotated[int, Form()],
    no_stock: Annotated[int | None, Form()] = None,
):
    new_product = Product(
        product_id=product_id,
        name=name,
        filename=filename,
        price=price,
        no_stock=no_stock,
    )

    maybe_product = await ProductTable.update(prev_product_id, new_product)

    # TODO: report back that the operation has been completed successfully or
    # failed in the process depending on the value of `maybe_product`
    _ = maybe_product
    # if (product := maybe_product) is None:
    #     detail = f"Product {product_id} not updated"
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    #
    # # return event_response(templates.product.card(product))

    return event_response(ServerSentEventGenerator.execute_script("location.reload()"))


@router.delete("/products/{product_id}", response_class=StreamingResponse)
async def delete(product_id: int):
    await delete_product(product_id)
    return event_response(ServerSentEventGenerator.execute_script("location.reload()"))


@router.get("/products/{product_id}/editor", response_class=StreamingResponse)
async def get_product_editor(request: Request, product_id: int):
    maybe_product = await ProductTable.by_product_id(product_id)

    if (product := maybe_product) is None:
        detail = f"Product {product_id} not found"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    fragment = fragment_editor(request, product)
    return event_response(ServerSentEventGenerator.merge_fragments([str(fragment)]))


@router.get("/product-editor")
async def get_empty_product_editor(request: Request):
    fragment = fragment_empty_editor(request)
    return event_response(ServerSentEventGenerator.merge_fragments([str(fragment)]))


# TODO: This path is defined temporally for convenience and should be removed in the future.
@router.put("/products/static/{csv_file}")
async def renew_table_from_products_list_csv(csv_file: str = "product-list.csv"):
    await ProductTable.renew_from_static_csv(f"static/{csv_file}")
