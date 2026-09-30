# Geyser Cooldown Crossplay Weapons

GeyserCooldownAnimation 専用の統合パック。Blurry FACE の Crossplay Animations 2.0 から剣の横薙ぎ、斧・トライデントの振り、メイス専用の振りと持ち方を取り込みました。剣・斧の各素材（銅を含む）に対応します。

ツルハシ・hoe の attachable と専用スイングを撤去し、通常表示・通常スイングを使います。サーバーから送られるクールダウンによる腕下げも、この2種類には適用しません。shovel の既存表示は維持します。

クールダウンは既存の Geyser パケットで再生します。参考パックのクライアント側クールダウンコントローラーは追加しないため、腕下げの二重再生を避けられます。既存の hand / sword / pickaxe / diamond_axe / iron_axe / stone_axe / mace のIDは通信互換用に保持します。回復時間は順に 0.25 / 0.65 / 0.90 / 1.05 / 1.15 / 1.30 / 1.65 秒です。

生成: python scripts/generate_pack_animations.py
パッケージ化: ./gradlew.bat resourcePack
cooldown.animation.json のみ生成対象です。crossplay_weapons.animation.json は参考元から統合した定義で、再生成しても維持されます。
