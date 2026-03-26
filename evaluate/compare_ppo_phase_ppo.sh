#!/bin/bash
echo "Starting Simultaneous Training Process..."
echo "1. Checking Virtual Environment..."
source venv/bin/activate

echo "2. Preparing directories..."
mkdir -p models/ppo_checkpoints models/phase_ppo_checkpoints runs

echo "3. Launching Standard PPO (Background)"
nohup python train_ppo_selfplay_server.py > ppo_training.log 2>&1 &
PPO_PID=$!
echo "   -> PPO PID: $PPO_PID"

echo "4. Launching Phase PPO (Background)"
nohup python train_phase_ppo_selfplay_server.py > phase_ppo_training.log 2>&1 &
PHASE_PPO_PID=$!
echo "   -> Phase PPO PID: $PHASE_PPO_PID"

echo "=========================================="
echo "Training successfully launched in background!"
echo "Check progress by viewing the log files:"
echo "   tail -f ppo_training.log"
echo "   tail -f phase_ppo_training.log"
echo "Or open another terminal and run 'tensorboard --logdir runs/' to view live charts."
echo "=========================================="
