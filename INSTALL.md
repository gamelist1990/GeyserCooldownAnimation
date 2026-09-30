# 導入ガイド

[READMEへ戻る](README.md)

## 1. 同じバージョンの2つのJARを配置

[GitHub Releases](https://github.com/gamelist1990/GeyserCooldownAnimation/releases)から取得します。

| ファイル | 配置先 |
| --- | --- |
| GeyserCooldownAnimation-<version>.jar | Geyserの extensions/ |
| GeyserCooldownPaperBridge-<version>.jar | 各Paperの plugins/ |

| Geyser環境 | 拡張の配置例 |
| --- | --- |
| Geyser-Spigot | plugins/Geyser-Spigot/extensions/ |
| Geyser-Velocity | plugins/Geyser-Velocity/extensions/ |
| Standalone | 実行ディレクトリの extensions/ |

GeyserはJava 21以上、PaperはJava 25以上・26.3が必要です。
Velocityでは拡張をGeyser-Velocityに置き、連携JARを各Paperに置きます。

## 2. 起動する

**token・endpoint・ポート設定は不要です。**
プレイヤーの既存のMinecraft接続で攻撃情報を運びます。
GeyserとPaperが別ホストでも、この拡張用のネットワーク設定は必要ありません。
通常のGeyser・Velocity・Paperの接続設定は済ませてください。

ログで次を確認します。

```text
Cooldown animation enabled; no token, endpoint or HTTP port required.
Cooldown animation bridge enabled; no configuration required.
```

## 3. Bedrockから接続してパックを適用

専用パックは拡張JARから自動展開され、Geyser経由で配布されます。
単体mcpackを重ねて配置する必要はありません。
サーバーパックを適用し、一人称で剣・斧・メイスの攻撃と空振りを確認してください。

自動展開されたパックを直接編集しても、次回起動時にJARの内容へ更新されます。
Geyserの受信アダプタは実パケットクラスで検証済みですが、Paperの実攻撃イベント・Velocity経由の実接続・Bedrock実機の見た目は未検証です。

## 1.0.0から更新する場合

1. GeyserとPaperを停止。
2. 旧版の両JARを取り除き、同じ新バージョンの両JARを配置。
3. 起動してBedrockから再接続。

旧bridge.propertiesとPaper側config.ymlは使用しません。残っていても構いません。
以前手動配置した同じUUIDのパックがある場合は、停止中に取り除いてください。

## トラブルシューティング

| 症状 | 確認する内容 |
| --- | --- |
| 拡張がロードされない | 配置先、Java 21以上、Geyser対応版 |
| Paper連携がロードされない | Paper側への配置、Java 25以上、Paper 26.3 |
| パック登録に失敗する | 同じUUIDのパックの重複、配布JARの破損 |
| Cooldown message adapter unavailable | Geyser内部APIの対応版。ログを添えて報告 |
| Unsupported Geyser packet API | Geyser対応版へ更新して再起動 |
| サーバー移動後だけ表示されない | 移動先Paperにも同じ版の連携JARがあるか |
| 動かない | サーバーパック適用、一人称視点、他のパックとの競合、専用チャンネルgeyser_cooldown:attackを他プラグインが遮断していないか |

## 削除

GeyserとPaperを停止して両JARと対応するデータフォルダを削除します。
