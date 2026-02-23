import asyncio
import random
from collections import namedtuple
import time
import matplotlib.pyplot as plt

random.seed(42)

# --- Config ---
NUM_NODES = 5
ELECTION_TIMEOUT_RANGE = (0.12, 0.28)
SIMULATION_TIME = 6.0
HEARTBEAT_INTERVAL = 0.05

# --- RPC types ---
RequestVote = namedtuple("RequestVote", ["term", "candidate_id", "last_log_index", "last_log_term"])
RequestVoteResp = namedtuple("RequestVoteResp", ["term", "vote_granted"])
AppendEntries = namedtuple("AppendEntries", ["term", "leader_id", "prev_log_index", "prev_log_term", "entries", "leader_commit"])
AppendEntriesResp = namedtuple("AppendEntriesResp", ["term", "success", "match_index"])

# --- Network simulator ---
class Network:
    def __init__(self):
        self.queues = {}
        self.message_count = {"RequestVote":0, "RequestVoteResp":0, "AppendEntries":0, "AppendEntriesResp":0}

    def register(self, node_id, queue):
        self.queues[node_id] = queue

    async def send(self, to_id, message):
        msg_type = message[0]
        if msg_type in self.message_count:
            self.message_count[msg_type] += 1
        await asyncio.sleep(random.uniform(0.002, 0.01))
        await self.queues[to_id].put(message)

# --- Raft Node ---
class Node:
    def __init__(self, node_id, peer_ids, network):
        self.id = node_id
        self.peers = peer_ids
        self.network = network

        # Persistent state
        self.current_term = 0
        self.voted_for = None
        self.log = []

        # Volatile state
        self.commit_index = -1
        self.last_applied = -1
        self.state = "follower"
        self.leader_id = None

        # Leader state
        self.next_index = {}
        self.match_index = {}

        # Communication
        self.inbox = asyncio.Queue()
        self.network.register(self.id, self.inbox)

        # Election timer
        self.reset_election_timeout()

        # Runtime control
        self.running = True

        # Metrics
        self.election_start_time = None
        self.election_duration = 0.0
        self.commit_times = {}
        self.commit_history = []  # Track commit index over time
        self.leader_election_ms = None  # Track election time in ms

    def reset_election_timeout(self):
        self.election_timeout = random.uniform(*ELECTION_TIMEOUT_RANGE)
        self.election_deadline = asyncio.get_event_loop().time() + self.election_timeout

    def last_log_index(self):
        return len(self.log) - 1

    def last_log_term(self):
        return self.log[-1][0] if self.log else 0

    # --- RPC Handlers ---
    async def handle_request_vote(self, msg, src):
        if msg.term < self.current_term:
            await self.network.send(src, ("RequestVoteResp", RequestVoteResp(term=self.current_term, vote_granted=False), self.id))
            return
        if msg.term > self.current_term:
            self.current_term = msg.term
            self.voted_for = None
            self.state = "follower"
            self.leader_id = None

        vote_granted = False
        if self.voted_for in (None, msg.candidate_id):
            up_to_date = (msg.last_log_term > self.last_log_term()) or \
                         (msg.last_log_term == self.last_log_term() and msg.last_log_index >= self.last_log_index())
            if up_to_date:
                vote_granted = True
                self.voted_for = msg.candidate_id
                self.reset_election_timeout()

        await self.network.send(src, ("RequestVoteResp", RequestVoteResp(term=self.current_term, vote_granted=vote_granted), self.id))

    async def handle_append_entries(self, msg, src):
        if msg.term < self.current_term:
            await self.network.send(src, ("AppendEntriesResp", AppendEntriesResp(term=self.current_term, success=False, match_index=-1), self.id))
            return

        self.leader_id = msg.leader_id
        self.current_term = msg.term
        self.state = "follower"
        self.reset_election_timeout()

        if msg.prev_log_index >= 0:
            if msg.prev_log_index > self.last_log_index() or \
               (self.log[msg.prev_log_index][0] != msg.prev_log_term):
                await self.network.send(src, ("AppendEntriesResp", AppendEntriesResp(term=self.current_term, success=False, match_index=-1), self.id))
                return

        idx = msg.prev_log_index + 1
        for entry in msg.entries:
            if idx <= self.last_log_index():
                if self.log[idx] != entry:
                    self.log = self.log[:idx]
                    self.log.append(entry)
            else:
                self.log.append(entry)
            idx += 1

        if msg.leader_commit > self.commit_index:
            self.commit_index = min(msg.leader_commit, self.last_log_index())
            value = self.log[self.commit_index][1]
            if value not in self.commit_times:
                self.commit_times[value] = time.time()

        await self.network.send(src, ("AppendEntriesResp", AppendEntriesResp(term=self.current_term, success=True, match_index=idx-1), self.id))

    # --- Node Actions ---
    async def start_election(self):
        self.state = "candidate"
        self.current_term += 1
        self.voted_for = self.id
        self.reset_election_timeout()
        votes = 1
        majority = len(self.peers)//2 + 1
        self.election_start_time = time.time()

        for peer in self.peers:
            rv = RequestVote(term=self.current_term, candidate_id=self.id,
                             last_log_index=self.last_log_index(), last_log_term=self.last_log_term())
            await self.network.send(peer, ("RequestVote", rv, self.id))

        while asyncio.get_event_loop().time() < self.election_deadline:
            try:
                msgtype, payload, src = await asyncio.wait_for(self.inbox.get(), timeout=self.election_deadline - asyncio.get_event_loop().time())
            except asyncio.TimeoutError:
                break

            if msgtype == "RequestVoteResp":
                resp = payload
                if resp.term > self.current_term:
                    self.current_term = resp.term
                    self.state = "follower"
                    self.voted_for = None
                    return False
                if resp.vote_granted:
                    votes += 1
                    if votes >= majority:
                        self.state = "leader"
                        self.leader_id = self.id
                        self.election_duration = time.time() - self.election_start_time
                        self.leader_election_ms = (time.time() - start_time_global) * 1000
                        for p in self.peers:
                            self.next_index[p] = self.last_log_index() + 1
                            self.match_index[p] = -1
                        return True
            elif msgtype == "AppendEntries":
                await self.handle_append_entries(payload, src)

        self.state = "follower"
        return False

    async def run(self):
        while self.running:
            now = asyncio.get_event_loop().time()
            if self.state != "leader" and now >= self.election_deadline:
                became = await self.start_election()
                if became:
                    await self.leader_send_heartbeats()

            try:
                msgtype, payload, src = await asyncio.wait_for(self.inbox.get(), timeout=0.02)
            except asyncio.TimeoutError:
                if self.state == "leader":
                    await self.leader_send_heartbeats()
                continue

            if msgtype == "RequestVote":
                await self.handle_request_vote(payload, src)
            elif msgtype == "AppendEntries":
                await self.handle_append_entries(payload, src)
            elif msgtype == "AppendEntriesResp" and self.state == "leader":
                await self.process_append_entries_resp(payload, src)

    async def process_append_entries_resp(self, resp, src):
        if resp.term > self.current_term:
            self.current_term = resp.term
            self.state = "follower"
            self.voted_for = None
            return

        if resp.success:
            self.match_index[src] = resp.match_index
            self.next_index[src] = resp.match_index + 1
            N = len(self.peers)//2 + 1
            for i in range(self.last_log_index(), self.commit_index, -1):
                match_count = 1 + sum(1 for p in self.peers if self.match_index.get(p, -1) >= i)
                if match_count >= N and self.log[i][0] == self.current_term:
                    self.commit_index = i
                    value = self.log[i][1]
                    if value not in self.commit_times:
                        self.commit_times[value] = time.time()
                    break
        else:
            self.next_index[src] = max(0, self.next_index.get(src, 1) - 1)

    async def leader_send_heartbeats(self):
        for peer in self.peers:
            prev_index = self.next_index.get(peer, 0) - 1
            prev_term = self.log[prev_index][0] if prev_index >= 0 and prev_index <= self.last_log_index() else 0
            entries = []
            if self.next_index.get(peer, 0) <= self.last_log_index():
                entries = self.log[self.next_index[peer]:]
            ae = AppendEntries(term=self.current_term, leader_id=self.id,
                               prev_log_index=prev_index, prev_log_term=prev_term,
                               entries=entries, leader_commit=self.commit_index)
            await self.network.send(peer, ("AppendEntries", ae, self.id))

    async def propose_value(self, value):
        if self.state != "leader":
            return False
        self.log.append((self.current_term, value))
        for p in self.peers:
            self.next_index[p] = self.last_log_index() + 1
        await self.leader_send_heartbeats()
        self.commit_times[value] = time.time()
        return True

    async def apply_committed(self):
        while self.last_applied < self.commit_index:
            self.last_applied += 1

# --- Run Simulation ---
async def run_simulation(proposed_value="X"):
    global start_time_global
    start_time_global = time.time()

    nodes = {}
    network = Network()
    node_ids = list(range(NUM_NODES))
    for nid in node_ids:
        peers = [p for p in node_ids if p != nid]
        nodes[nid] = Node(nid, peers, network)

    tasks = [asyncio.create_task(nodes[n].run()) for n in nodes]

    time_history = []
    commit_history = {nid: [] for nid in node_ids}

    while time.time() - start_time_global < SIMULATION_TIME:
        leaders = [n for n in nodes.values() if n.state == "leader"]
        if leaders:
            leader = leaders[0]
            if leader.last_log_index() == -1:
                await leader.propose_value(proposed_value)
        await asyncio.sleep(0.05)
        current_time_ms = (time.time() - start_time_global) * 1000
        time_history.append(current_time_ms)
        for nid, n in nodes.items():
            await n.apply_committed()
            commit_history[nid].append(n.commit_index)

    for n in nodes.values():
        n.running = False
    await asyncio.gather(*tasks, return_exceptions=True)

    # --- Print results ---
    print("=== Simulation Result ===")
    committed_values = []
    for nid, n in nodes.items():
        await n.apply_committed()
        committed_val = n.log[n.commit_index][1] if n.commit_index >= 0 else None
        committed_values.append(committed_val)
        print(f"Node {nid}: state={n.state}, term={n.current_term}, committed_index={n.commit_index}, committed_value={committed_val}, log={n.log}, election_time={n.election_duration:.4f}s, commit_times={n.commit_times}, leader_election_ms={n.leader_election_ms}")

    print("\nMessage counts:", network.message_count)
    all_equal = all(v == committed_values[0] for v in committed_values if v is not None)
    print("\nConsensus reached across nodes?", all_equal)
    if all_equal:
        print("Final agreed value:", committed_values[0])
    else:
        print("Committed values:", committed_values)

    # --- Plot commit evolution ---
    plt.figure(figsize=(8,5))
    for nid, history in commit_history.items():
        plt.plot(time_history, history, label=f"Node {nid}")
        # Mark final commit with red dot
        commit_index = nodes[nid].commit_index
        if commit_index >= 0:
            for t_ms, idx in zip(time_history, history):
                if idx == commit_index:
                    plt.plot(t_ms, idx, 'ro')
                    break

    # Plot vertical lines for leader election
    for nid, n in nodes.items():
        if n.leader_election_ms:
            plt.axvline(x=n.leader_election_ms, color='k', linestyle='--', alpha=0.5, label=f"Leader Node {nid} elected")

    plt.xlabel("Time (ms)")
    plt.ylabel("Commit Index")
    plt.title("Évolution de l'index de commit par nœud (final commit marked)")
    plt.legend()
    plt.grid(True)
    plt.show()

# Run the simulation
asyncio.run(run_simulation(proposed_value="SUSHI"))
