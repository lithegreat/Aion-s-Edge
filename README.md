# Aion's Edge

Hands-on projects for the course "Multi-Criteria Optimization and
Decision Analysis." The main experience is Aion's Edge (a Streamlit
strategy game), plus two classic neuroevolution demos.

## ✅ Prerequisites

Before installation, make sure you have:

- Python 3.14+
- `uv` package manager installed
- Optional for demos: native build tools for `pygame`/`gymnasium[box2d]`

If `uv` is not installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

> [!WARNING]
> This project uses Python 3.14 (very new), so some dependencies may not
> have prebuilt wheels yet. The Streamlit game runs with the base
> dependencies, but optional demos may require local compilation:
> `pygame` (Flappy Bird) and `gymnasium[box2d]` (Lunar Lander).
>
> On Fedora 43 (which is the system I use), you can start with the following system packages as a
> reference:
>
> ```bash
> sudo dnf install -y \
>   gcc gcc-c++ make cmake pkgconf-pkg-config swig \
>   SDL2-devel SDL2_image-devel SDL2_mixer-devel SDL2_ttf-devel \
>   portmidi-devel mesa-libGL-devel
> ```
>
> Recommended workflow: run `uv sync` (or `uv pip install ...`) first, then
> install only the missing build tools/libraries reported in the error logs.

## 🎮 Projects

### 1. Aion's Edge (Main Game)
A Streamlit colony-strategy game that teaches Linear Programming,
Multi-Objective Optimization, and Voting Theory/MCDA through three
playable levels.

**Features:**
- Level 1: LP survival planning with random events
- Level 2: Pareto-front exploration and Nadir analysis
- Level 3: Voting systems and coalition outcomes

**Run:**
```bash
uv run streamlit run src/app.py
```

### 2. Flappy Bird Evolution
A pure NumPy neural network learns to play Flappy Bird through a
genetic algorithm.

**Features:**
- Custom neural network (3 inputs → 6 hidden → 1 output)
- Genetic algorithm with elitism and mutation
- Real-time visualization with PyGame
- Fast-forward training mode (press Space)

**Run:**
```bash
uv run other_games/flappy_evolution.py
```

### 3. Lunar Lander (NEAT)
Uses NEAT (NeuroEvolution of Augmenting Topologies) to evolve neural
networks for the Gymnasium Lunar Lander environment.

**Features:**
- NEAT topology evolution (nodes + connections)
- Multi-episode fitness evaluation
- Checkpoint saving every 5 generations
- Automated demo visualization after training

**Run:**
```bash
# Train
uv run other_games/lunar_neat.py

# Or resume from checkpoint
uv run python -c "import neat; p = neat.Checkpointer.restore_checkpoint('checkpoints/neat-checkpoint-50')"
```

## 📦 Installation

```bash
uv sync
```

Or manually install dependencies:
```bash
uv pip install neat-python numpy pyyaml scipy streamlit matplotlib
```

Optional (Flappy Bird only):
```bash
uv pip install pygame
```

Optional (Lunar Lander only):
```bash
uv pip install "gymnasium[box2d]"
```

Install optional extras through project metadata:
```bash
uv sync --extra flappy --extra lunar
```

## 🧬 How It Works

### Aion's Edge Math Engine
The numerical solvers now live in `src/optimization/`:
- `lp.py`: linear programming for survival planning
- `moo.py`: Pareto-front detection and Nadir analysis
- `voting.py`: voting rules for MCDA decisions

The game flow now uses package-based modules under `src/`:
- `src/campaign/`: shared campaign state, events, and turn resolution
- `src/level1/`: Level 1 orchestration, LP logic, and plotting
- `src/level2/`: Level 2 orchestration, policy scoring, and Pareto views
- `src/level3/`: Level 3 orchestration, voting logic, and council views

### Genetic Algorithm (Flappy Bird)
1. **Initialize** population with random neural networks
2. **Evaluate** fitness (survival time)
3. **Select** top performers
4. **Reproduce** via mutation
5. **Repeat** until convergence

### NEAT (Lunar Lander)
- Evolves both **network topology** and **weights**
- Uses **speciation** to protect innovation
- **Crossover** between similar networks
- Solves multi-objective optimization (landing success + fuel efficiency)

## 📊 Project Structure

```
neuroevolution_games/
├── report/
│   ├── main.tex               # Main LaTeX report entry point
│   ├── references.bib        # Bibliography database
│   ├── Makefile              # Report build commands
│   └── sections/             # Report chapters/sections
├── src/
│   ├── app.py                 # Aion's Edge Streamlit entry point
│   ├── optimization/
│   │   ├── __init__.py        # Shared optimization package exports
│   │   ├── lp.py              # Linear-programming solver
│   │   ├── moo.py             # Pareto and Nadir analysis
│   │   └── voting.py          # Voting-rule evaluation
│   ├── campaign/
│   │   ├── __init__.py        # Campaign package exports
│   │   ├── core.py            # Shared state, events, and turn flow
│   │   └── views.py           # Campaign status and resolution UI
│   ├── level1/
│   │   ├── __init__.py        # Level 1 page orchestration
│   │   ├── core.py            # LP gameplay logic
│   │   └── views.py           # Level 1 charts and event UI
│   ├── level2/
│   │   ├── __init__.py        # Level 2 page orchestration
│   │   ├── core.py            # Policy and Pareto logic
│   │   └── views.py           # Level 2 plots and UI helpers
│   └── level3/
│       ├── __init__.py        # Level 3 page orchestration
│       ├── core.py            # Voting and council resolution logic
│       └── views.py           # Voting visualizations and summaries
├── other_games/
│   ├── flappy_evolution.py    # Flappy Bird with custom GA
│   └── lunar_neat.py          # Lunar Lander with NEAT
├── config/
│   └── config-feedforward.yaml  # NEAT configuration
├── checkpoints/              # Training checkpoints (auto-saved)
└── pyproject.toml            # Dependencies
```

## 📄 Report Module

This repository now includes a dedicated LaTeX report module in
`report/` for writing course notes, experiment summaries, and project
reports.

**Build prerequisites:**
- A LaTeX distribution such as TeX Live
- `latexmk`
- `bibtex` (or the TeX Live package that provides it)

**Build the PDF:**
```bash
cd report
make pdf
```

**Clean generated files:**
```bash
cd report
make clean
```

## 🎯 Training Tips

**Flappy Bird:**
- Press **Space** to toggle fast-forward mode
- Typical convergence: 50-200 generations
- Watch diversity in bird colors

**Lunar Lander:**
- Training saves checkpoints every 5 generations in `checkpoints/`
- Success threshold: fitness > 200
- Demo runs automatically after training

## 🔧 Configuration

Edit [config/config-feedforward.yaml](config/config-feedforward.yaml) to tune NEAT parameters:
- `pop_size`: Population size (default: 100)
- `fitness_threshold`: Success criteria (default: 200)
- `conn_add_prob`: Connection mutation rate
- `bias_mutate_rate`: Weight mutation rate

## 📝 License

MIT

## 🤝 Contributing

Feel free to open issues or PRs for improvements!
