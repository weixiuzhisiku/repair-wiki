#!/data/data/com.termux/files/usr/bin/bash
cd ~/repair-wiki/tiddlers
echo "=== 新建维修案例 ==="
read -p "品牌: " brand
read -p "机型: " model
read -p "故障: " fault
echo "$brand-$model-$fault" > "$brand-$model-$fault.tid"
