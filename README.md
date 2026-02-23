Mini-Project: Simplified Consensus (Mini-Raft)
Project Overview
This project implements a simplified version of the Raft Consensus Protocol. The primary goal is to simulate a distributed system where multiple independent nodes reach an agreement on a single value, 
even in an asynchronous environment with simulated network delays.

This was developed as part of the Advanced Algorithms and Complexity course at Ferhat Abbas University - Setif 1.

Features

Leader Election: Nodes transition from Followers to Candidates to elect a Leader based on a majority vote.
Log Replication: The Leader manages a log and replicates entries across the cluster to ensure consistency.
Asynchronous Simulation: Built using asyncio to handle concurrent message passing between nodes.
Performance Metrics: Real-time tracking of message counts (RequestVote, AppendEntries) and election durations.

Technical Specifications

Language: Python 3.10+.
Core Libraries: asyncio, matplotlib (for visualization), and collections.
Configuration: * Number of Nodes: 5.
Election Timeout: 120ms to 280ms.
Heartbeat Interval: 50ms.

Installation & Execution
Clone the repository:
Bash
git clone https://github.com/salah-cherair/AAC-mini-project.git
cd AAC-mini-project
Install dependencies:

Bash

pip install matplotlib
Run the simulation:

Bash

python raft.py

Results Summary
During the simulation, the system successfully reached a consensus on the value "SUSHI".
Election Speed: A leader was typically elected within ~63ms to 79ms.
Consistency: 100% of nodes reached the same final commit index and applied the same value.
Network Traffic: Observed high volumes of AppendEntries messages, reflecting the heartbeat and replication mechanism of the protocol.

Author : Salaheddine Cherair 
Supervisor: Dr. Hadi Fairouz 
Academic Year: 2025-2026
