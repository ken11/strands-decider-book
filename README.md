# 入門 System Oneモデル - サンプルコード

本リポジトリは、技術書典21で頒布する「[**入門 System Oneモデル ― Strands DeciderとStrands AgentsでつくるAIエージェント**](https://techbookfest.org/product/rJ2tyytq6mvD18LVydkfc5)」のサンプルコードを収録しています。

## 書籍について

Strands Agents で AI メール秘書を作りながら、文章を生成せずに判断だけを返す System One モデルを AI エージェントの中で活用する方法を、ハンズオン形式で解説します。System One モデルには、ローカルで動く Strands Decider を使います。

## 必要な環境

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- Node.js 24（LTS）
- Amazon Bedrock を利用できる AWS アカウント

動作は Apple Silicon 搭載の Mac で確認しています。Strands Decider は、Mac では MLX を使って動かします（`--device mlx`）。MLX を指定しなければ、ほかの環境でも基本的には動くはずです。

## 使い方

```bash
uv sync
uv run python chapter1/hello.py
```

各章のコードは `chapter1/` 〜 の各ディレクトリに格納しています。どの章もリポジトリのルートから実行してください。

### 画面で動かす（第2章から）

第2章からは、メールの画面（`web/`）からAI秘書を動かせます。章ごとのAPIサーバと、画面の開発サーバを、それぞれ別のターミナルで起動します。

```bash
uv run python chapter2/server.py
```

```bash
cd web
npm install
npm run dev
```

ブラウザで http://localhost:5173 を開きます。APIサーバは、起動するたびにデータ（`workspace/`）を初期状態に戻します。第5章からは、`uv run --group mask python chapter5/server.py` のように `--group mask` を付けて起動します。

画面を使わずに、すべてのメールをまとめて処理したいときは、各章の `main.py` を実行します。

第6章は、画面もBedrockも使いません。100通のダミーメールを、手元の Decider と Presidio だけで判定します。

第4章からは、Strands Decider のサーバを別のターミナルで起動しておきます。Decider はサンプルコードとは別の環境で動かします。

```bash
uvx --python 3.13 --from "strands-decider[mlx]==0.2.0" \
  strands-decider serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 \
  --device mlx --port 8099
```

第5章からは、個人情報を伏せ字にするためのパッケージを追加でインストールします。

```bash
uv sync --group mask
```

## ダミーデータについて

`data/` には、ハンズオンで使うダミーのメール・予定・正解ラベルを収録しています。
登場する会社・人物・住所・電話番号・メールアドレスなどは、すべて架空のものです。

## 免責事項

- 本サンプルコードは学習目的で提供しており、本番環境での使用は想定していません
- コードの動作や結果について、著者は一切の責任を負いません
- AWS の認証情報などの機密情報の管理は、ご自身の責任で行ってください
- サンプルコードを実行すると、Amazon Bedrock の利用料金が発生します。AI エージェントは1回の依頼でもモデルを何度も呼び出すため、想定より多くの料金がかかる場合があります。料金は事前に [Amazon Bedrock の料金ページ](https://aws.amazon.com/jp/bedrock/pricing/) で確認し、AWS Budgets などで予算のアラートを設定することをおすすめします
- サンプルコードの不具合や想定外の動作、改変などによって高額な請求が発生した場合でも、著者は一切の責任を負いません。ご自身の責任のもとで実行してください
- 本サンプルコードは書籍執筆時点（2026年10月）の情報に基づいており、ライブラリの仕様変更によって動作しなくなる可能性があります

## ライセンス

[MIT License](LICENSE)
