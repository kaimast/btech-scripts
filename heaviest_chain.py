#! /bin/env python3

# pylint: disable=missing-function-docstring, missing-module-docstring, line-too-long

import argparse

parser = argparse.ArgumentParser("heaviest chain attack simulator")
parser.add_argument("strategy", type=str, choices=["honest", "alternate"], help="Defines how the miner will behave")
parser.add_argument("--start-difficulty", type=int, default=3000, help="What is the initial mining difficulty?")
parser.add_argument("--attack-fraction", type=int, default=30, help="What share of the mining power does the attacker have?")
parser.add_argument("--period-length", type=int, default=5, help="After how many blocks is difficulty recalculated?")
parser.add_argument("--block-time", type=int, default=60, help="The expected time between blocks")
parser.add_argument("--num-blocks", type=int, default=50, help="Simulate until the first chain reached this number of blocks")

def calculate_block_interval(difficulty, mining_power):
    return difficulty / mining_power

HONEST=0
ATTACKER=1

def to_name(index):
    if index == HONEST:
        return "HONEST"
    return "ATTACKER"

def main():
    args = parser.parse_args()

    difficulties = [args.start_difficulty, args.start_difficulty]
    block_times = [[], []]
    chain_weights = [0, 0]
    chain_lengths = [0, 0]
    mining_powers = [100 - args.attack_fraction, args.attack_fraction]
    next_block_times = [
        calculate_block_interval(difficulties[HONEST], mining_powers[HONEST]),
        calculate_block_interval(difficulties[ATTACKER], mining_powers[ATTACKER])
    ]

    while chain_lengths[0] < args.num_blocks and chain_lengths[1] < args.num_blocks:
        if next_block_times[0] <= next_block_times[1]:
            idx = 0
        else:
            idx = 1

        time = next_block_times[idx]
        print(f"## {to_name(idx)} created new block at time {time} ##")

        block_times[idx].append(time)
        chain_weights[idx] += difficulties[idx]
        chain_lengths[idx] += 1

        if chain_lengths[idx] % args.period_length == 0:
            assert chain_lengths[idx] > 0

            # We always start measuring from the end of the previous period
            # If there is none, pick 0
            if chain_lengths[idx] == args.period_length:
                start = 0
            else:
                start = block_times[idx][-(args.period_length+1)]

            actual = block_times[idx][-1] - start
            expected = args.period_length * args.block_time
            change = expected / actual

            old = difficulties[idx]
            difficulties[idx] = old * change
            print(f"Changing difficulty for {to_name(idx)} by {change}: {old} -> {difficulties[idx]}")

            if idx == ATTACKER and args.strategy == "alternate":
                if difficulties[ATTACKER] == args.attack_fraction:
                    print("Attacker halved its mining power")
                    difficulties[ATTACKER] = args.attack_fraction / 2
                else:
                    print("Attacker restored its full mining power")
                    difficulties[ATTACKER] = args.attack_fraction

        print(f"Chain lengths are now {to_name(0)}={chain_lengths[0]} {to_name(1)}={chain_lengths[1]}")
        print(f"Chain weights are now {to_name(0)}={chain_weights[0]} {to_name(1)}={chain_weights[1]}")

        if chain_weights[0] >= chain_weights[1]:
            print(f"Heaviest chain is now: {to_name(0)}")
        else:
            print(f"Heaviest chain is now: {to_name(1)}")

        if chain_lengths[0] >= chain_lengths[1]:
            print(f"Longest chain is now: {to_name(0)}")
        else:
            print(f"Longest chain is now: {to_name(1)}")


        next_block_times[idx] = time + calculate_block_interval(difficulties[idx], mining_powers[idx])

if __name__ == "__main__":
    main()
