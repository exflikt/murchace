## 一般

### コミットヒストリー

Git のコミット履歴を綺麗に保つことは大事だが、ルールと呼べるもほどのものはない。
可能であれば、プルリクエストのタイトルや説明文はソフトウェアを更新する際によく見る変更履歴 (Changelog) のような形式にする。

**根拠**: 綺麗な履歴は便利かもしれないが、実際にはそれほど読まれない。しかし、多くのユーザはチェンジログを読む。

### リント

Python コードは ruff でリントする。もしリントが不適切であれば、 https://docs.astral.sh/ruff/configuration/ に従って `pyproject.toml` を書き換える。

## コード

### Python の命名規則

[PEP8](https://peps.python.org/pep-0008/#naming-conventions) に従い、変数名や関数名は小文字の単語をアンダースコア `_` で、クラス名は最初の文字を大文字にした単語を繋げる。

- 変数名、関数名 (snake_case): `lower_case_with_underscores`
- クラス名 (CamelCase): `CapitalizedWords`
- グローバル変数 (SCREAMING_SNAKE_CASE): `UPPER_CASE_WITH_UNDERSCORES`
