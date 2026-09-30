# GeyserCooldownAnimation

**Javaの攻撃クールダウンを、Bedrockプレイヤーの手元の動きで表示するGeyser拡張。**

Paperの攻撃速度に応じて、攻撃したBedrockプレイヤー本人へアニメーションを送信します。
専用の **Geyser Cooldown Animation Resource Pack** を同梱して、配布します。

[導入ガイド](INSTALL.md) · [MIT License](LICENSE)

> 開発段階です。Geyser上のロード・パック登録・受信処理は確認済みですが、Paperの実際の攻撃イベント・Velocity経由の実接続・Bedrock実機の表示は未検証です。

## 機能

- 素手・剣・ツルハシ・斧・メイスの7つの表示プロファイル。
- 攻撃時に手を下げ、クールダウンに合わせて戻す一人称アニメーション。
- 専用パックの自動展開とGeyser経由の配布。
- 同じtickの重複抑制と、プレイヤーの既存接続を使う通信。
- token・endpoint・追加ポート・設定ファイル不要。
- 内部APIの非互換時に表示機能を停止。

## 対応環境

| コンポーネント | 配置先 | 実行環境 |
| --- | --- | --- |
| GeyserCooldownAnimation | Geyserの `extensions/` | Java 21以上、Geyser API 2.11.0以上 |
| GeyserCooldownPaperBridge | Paperの `plugins/` | Java 25以上、Paper 26.3 |
| 専用リソースパック | 拡張JARに同梱 | Bedrockでサーバーパックを適用 |

Geyser-Spigot、Geyser-Velocity、Standaloneから、既存のMinecraft接続でPaperと連携します。
別ホストでも追加のHTTP通信設定は不要です。Velocity専用の追加JARも不要です。
Geyser 2.11.3-b1247の実パケットクラスで受信処理を検証済み。
Velocity経由の実接続とBedrock実機での表示は未検証です。

## 導入

1. GitHub **Releases** から同じバージョンの2つのJAR、または導入用ZIPを取得。
2. Geyserのextensionsへ拡張、Paperのpluginsへ連携JARを配置。
3. 起動し、Bedrockから接続してサーバーパックを適用。

設定ファイルの編集は不要です。Velocity構成では各Paperサーバーへ連携JARを配置します。

詳しいフォルダ例と設定は [INSTALL.md](INSTALL.md) を参照してください。

## 専用パック

自作のmanifest・独自名前空間・数式によるアニメーションで構成した **MIT** のパックです。
外部パックのテクスチャ・モデル・プレイヤー定義・コントローラは含めていません。

動きは、指定されたCooldown Animationの「0.125秒で下げ、その後戻す」という表示に合わせています。
一人称で右腕を20モデル単位下げ、プロファイルに応じて元の位置に戻します。

| プロファイル | 元の位置に戻るまで |
| --- | --- |
| 素手 | 0.25秒 |
| 剣 | 0.65秒 |
| ツルハシ | 0.90秒 |
| ダイヤ・金・ネザライト斧相当 | 1.05秒 |
| 鉄斧相当 | 1.15秒 |
| 木・石斧相当 | 1.30秒 |
| メイス | 1.65秒 |

実効攻撃速度から最も近い標準プロファイルを選びます。
カスタム攻撃速度を連続的に反映する仕組みではありません。
パックのソースと動作仕様は [resource-pack/README.md](resource-pack/README.md) を参照してください。

## 表示の範囲

| 対象 | 動作 |
| --- | --- |
| 攻撃したBedrockプレイヤー本人 | 一人称で手元を下げる |
| Javaプレイヤー | アニメーションを送信しない |
| 第三者のBedrockクライアント | この版では送信しない |
| 三人称視点 | 専用パックの右腕オフセットは0 |
| 採掘の左クリック | 再生要求を送信しない |

## ビルド

JDK 21と25、Python 3を用意します。拡張はJava 21、Paper連携はJava 25をターゲットにします。

```bash
./gradlew clean build
python3 scripts/package_release.py --version 1.1.0
```

Windowsでは `gradlew.bat clean build` と `py scripts/package_release.py --version 1.1.0` を使います。
パックのJSONソースを編集した場合も、Gradleが同梱版と単独版を作成します。

| 配布資産 | 内容 |
| --- | --- |
| `GeyserCooldownAnimation-<version>.jar` | 専用パック入りGeyser拡張 |
| `GeyserCooldownPaperBridge-<version>.jar` | Paper連携 |
| `GeyserCooldownAnimation-pack-<version>.mcpack` | 専用パック単体 |
| `GeyserCooldownAnimation-<version>.zip` | 両JAR、パック、導入手順、ライセンス |
| `SHA256SUMS.txt` | 配布資産のチェックサム |

出力先は `dist/` です。通常の導入ではパック単体の手動配置は不要です。

## GitHub Actions

- ブランチpush・pull request：ビルド、テスト、配布資産の検証、Actions成果物の保存。
- `v1.1.0` のようなタグpush：タグのバージョンでビルドしてGitHub Releaseを自動作成。
- `v1.1.0-rc.1`：プレリリースとして公開。

```bash
git tag v1.1.0
git push origin v1.1.0
```

両JARのファイル名とメタデータをタグに合わせます。
Bedrockのmanifestにはタグの数値部分を3要素のバージョンとして反映します。

## ライセンス

コードと専用パックは **MIT**。Copyright © 2026 gamelist1990 & Koukunn_。
元のExtension TemplateのMIT著作権表示も保持しています。
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) で依存元・参考元を確認できます。
