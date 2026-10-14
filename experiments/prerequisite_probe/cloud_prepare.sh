#!/usr/bin/env bash
set -euo pipefail

BASE=/root/autodl-tmp/monitor2
mkdir -p "$BASE/experiments/prerequisite_probe/artifacts/model_input" "$BASE/research/sources" "$BASE/logs" /root/autodl-tmp/hf /root/autodl-tmp/pip_cache /root/autodl-tmp/tmp

printf '%s  %s\n' a17e0bb91f649a5ca514c9231cd01aba4fc9331a0bbf75bba598f5603b918c88 /root/autodl-tmp/model_input_only.zip | sha256sum -c -
unzip -oq /root/autodl-tmp/model_input_only.zip -d "$BASE/experiments/prerequisite_probe/artifacts/model_input"

if [ ! -d "$BASE/research/sources/TOPReward/.git" ]; then
    git clone https://github.com/TOPReward/TOPReward.git "$BASE/research/sources/TOPReward"
fi
git -C "$BASE/research/sources/TOPReward" checkout --detach 4877a0ee5098cbec18485125466631b1dcc4a573

if [ ! -d "$BASE/research/sources/robometer/.git" ]; then
    git clone https://github.com/robometer/robometer.git "$BASE/research/sources/robometer"
fi
git -C "$BASE/research/sources/robometer" checkout --detach 352d160389daa964788de1ec933d1925f3a6de4f

git -C "$BASE/research/sources/TOPReward" rev-parse HEAD
git -C "$BASE/research/sources/robometer" rev-parse HEAD
du -sh "$BASE/experiments/prerequisite_probe/artifacts/model_input"
