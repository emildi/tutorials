import time

import matplotlib.pyplot as plt
import numpy as np
import os

import tensorflow as tf
from agent import Agent
from gamewrapper import GameWrapper
from config import (BATCH_SIZE, CLIP_REWARD, DISCOUNT_FACTOR, ENV_NAME,
                    EVAL_LENGTH, FRAMES_BETWEEN_EVAL, INPUT_SHAPE,
                    LEARNING_RATE, LOAD_FROM, MAX_EPISODE_LENGTH,
                    MAX_NOOP_STEPS, MEM_SIZE, MIN_REPLAY_BUFFER_SIZE,
                    SAVE_PATH, TOTAL_FRAMES, UPDATE_FREQ, WRITE_TENSORBOARD)
from dqn import build_q_network
from process_frame import process_frame
from replay_buffer import ReplayBuffer

# My installations require I run this to avoid errors with cuDNN.
# You can remove it if your system doesn't require it.
# (it shouldn't mess anything up if you keep it in)
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)

    except RuntimeError as e:
        print(e)

# Change this to the path of the model you would like to visualize
RESTORE_PATH = 'breakout-saves_redo/save-11379708'

# Create environment
game_wrapper = GameWrapper(ENV_NAME, MAX_NOOP_STEPS)
print("The environment has the following {} actions: {}".format(game_wrapper.env.action_space.n, game_wrapper.env.unwrapped.get_action_meanings()))

# Create agent
MAIN_DQN = build_q_network(game_wrapper.env.action_space.n, LEARNING_RATE, input_shape=INPUT_SHAPE)
TARGET_DQN = build_q_network(game_wrapper.env.action_space.n, input_shape=INPUT_SHAPE)

replay_buffer = ReplayBuffer(size=MEM_SIZE, input_shape=INPUT_SHAPE)
agent = Agent(MAIN_DQN, TARGET_DQN, replay_buffer, game_wrapper.env.action_space.n, input_shape=INPUT_SHAPE, batch_size=BATCH_SIZE)

print('Loading model...')
agent.load(RESTORE_PATH)
print('Loaded')

terminal = True
eval_rewards = []

for frame in range(EVAL_LENGTH):
    if terminal:
        game_wrapper.reset(evaluation=True)
        life_lost = True
        episode_reward_sum = 0
        terminal = False

    # Breakout require a "fire" action (action #1) to start the
    # game each time a life is lost.
    # Otherwise, the agent would sit around doing nothing.
    action = 1 if life_lost else agent.get_action(0, game_wrapper.state, evaluation=True)

    # Step action
    _, reward, terminal, life_lost = game_wrapper.step(action, render_mode='human')

    episode_reward_sum += reward

    # On game-over
    if terminal:
        print(f'Game over, reward: {episode_reward_sum}, frame: {frame}/{EVAL_LENGTH}')
        eval_rewards.append(episode_reward_sum)

print('Average reward:', np.mean(eval_rewards) if len(eval_rewards) > 0 else episode_reward_sum)
