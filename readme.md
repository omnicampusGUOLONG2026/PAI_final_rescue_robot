# PAI Final Rescue Robot: AI見守り・転倒レスキューロボットシステム

YOLOv8-Pose姿勢推定AIとROS 2 / Gazebo自律走行モジュールを連携させ、病室内での患者の転倒インシデント発生時に自律急行・現場確認および一次救援アラートを実行するフィジカルAIシステムです。

---

## 1. システム概要・社会的背景

超高齢社会の進展に伴い、医療機関や介護療養施設における夜間・少人数帯での転倒・転落防止および早期覚知が強い課題となっています。本システムは、定点カメラによるリアルタイム姿勢推定AIと移動ロボットを疎結合に連携させ、以下のプロセスを全自動で実行します：

1. **転倒判定**: 俯瞰RGBカメラ映像からYOLOv8-Poseを用いて骨格情報を抽出し、幾何学的比率および時間軸フィルタリング（チャタリング防止）により高精度に転倒を確定検知。
2. **自律急行**: 転倒確定イベント（`/fall_event` -> `/navigation_goal_trigger`）を受信後、Nav2スタックを介してベッドサイドへ最速経路で自律移動。
3. **現場確認・待機**: 到達後は患者の方向へ自動で旋回し、現場状況の確認と二次インシデント防止のためのフェイルセーフ動作を実行。

---

## 2. システムアーキテクチャ

```
[病室 RGBカメラ]
       │ (sensor_msgs/msg/Image)
       ▼
[Vision AI Node (YOLOv8-Pose)]
       │ (/fall_event: std_msgs/msg/String)
       ▼
[Fall Logic Node (幾何学・3フレーム時間軸フィルタ)]
       │ (/navigation_goal_trigger: std_msgs/msg/String)
       ▼
[Navigator Node (ROS 2 Nav2 Stack)]
       │ (geometry_msgs/msg/Twist)
       ▼
[Gazebo Simulation (TurtleBot3 / 病室ワールド)]
```

---

## 3. コンポーネントおよび使用技術一覧

| モジュール名 | 使用技術・ライブラリ | 役割および実装内容 |
| :--- | :--- | :--- |
| **Vision AI Node** | YOLOv8-Pose (PyTorch / Ultralytics) | 俯瞰映像から17個の骨格キーポイントをリアルタイム推論 (~30fps) |
| **Fall Logic Node** | ROS 2 (`rclpy` / `std_msgs`) | バウンディングボックス長短比および3フレーム連続検出によるチャタリング防止 |
| **Navigator Node** | ROS 2 (`geometry_msgs` / Nav2) | 目標座標への自律経路生成および旋回・待機動作の制御指令発行 |
| **Simulation** | Gazebo 11 / TurtleBot3 | 病室環境（ベッド・机・患者マネキン）内の物理模擬 |

---

## 4. 主な技術的工夫

* **三段階の誤検知低減ロジック**:
  * アスペクト比判定: 人体バウンディングボックスの $width / height > 1.1$ を検知。
  * チャタリング防止: ノイズによる誤判定を抑制するため、3フレーム連続（約100ms）で条件を満たした場合のみ確定フラグをパブリッシュ。
* **疎結合なROS 2ノード設計**:
  * 推論・論理判定・ナビゲーションを独立したノード群として設計。標準メッセージ通信を用いることで、実機ロボットへの移行時にも最小限のコード修正で対応可能。

---

## 5. ディレクトリ構成

```text
PAI_final_rescue_robot/
├── README.md
├── package.xml
├── setup.py
└── PAI_final_rescue_robot/
    ├── __init__.py
    ├── vision_ai_node.py
    ├── fall_logic_node.py
    └── navigator_node.py
```

---

## 6. セットアップ・実行方法

### 前提条件
* Ubuntu 22.04 LTS
* ROS 2 Humble
* Python 3.10+
* Ultralytics (`pip install ultralytics opencv-python cv-bridge`)

### 起動手順

1. **ワークスペースのビルドと環境読み込み**:
   ```bash
   cd ~/ros2_ws
   colcon build --symlink-install
   source install/setup.bash
   ```

2. **Gazeboシミュレーション環境の起動**:
   ```bash
   ros2 launch my_rescue_bot_gazebo hospital_world.launch.py
   ```

3. **転倒検知・レスキューシステムの起動**:
   ```bash
   ros2 run PAI_final_rescue_robot vision_ai_node
   ros2 run PAI_final_rescue_robot fall_logic_node
   ros2 run PAI_final_rescue_robot navigator_node
   ```

---

## 7. 今後の展望

* **マルチモーダル統合**: 遮蔽物（毛布等）によるキーポイント欠損に対応するため、3D LiDAR点群データとの統合。
* **プライバシー配慮型エッジAI**: 深度マップやサーマルカメラ入力を用いたエッジ推論の導入。