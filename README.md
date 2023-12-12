# CAESURA: Language Models as Multi-Modal Query Planners

CAESURA is a LLM-driven query planner for multi-modal data systems. This is the implementation described in

> Matthias Urban and Carsten Binnig: "CAESURA: Language Models as Multi-Modal Query Planners", CIDR'2024 [[PDF]](https://www.cidrdb.org/cidr2024/program.html) [[Preprint]](https://arxiv.org/abs/2308.03424).
> 
> ![Image of CAESURA Paper](image.png)

## 1. Setup

1. **Install CAESURA. Tested with python3.11.2 and conda on Ubuntu.**

    ```sh
    git clone git@github.com:DataManagementLab/caesura.git
    conda create -n caesura
    conda activate caesura
    conda install python=3.11 pip
    pip install -r requirements.txt
    pip install -e .
    ```

1. **Install Pytorch: https://pytorch.org/ -- Tested with torch==2.0.0, torchvision==0.15.1**

1. **Get the datasets**

    1. **Generate the Rotowire Dataset.**

        ```sh
        python scripts/rotowire/download.py
        ```

        Manually fix the dataset in datasets/rotowire/players.csv and datasets/rotowire/teams.csv. Look out for [[ and {{. For correct results also check whether heights are all given in feet, and so on.

    1. **Get the artworks/museum dataset.**

        ```sh
        python scripts/artworks/download.py  # Full dataset
        python scripts/artworks/download.py 100 # Only first 100 artworks 
        ```

1. **Test it on your own queries.**

    ```sh
    python caesura/main.py
    ```

1. **Run the experiments.**

    ```sh
    python scripts/run_experiment.py --model=3  # GPT-3
    python scripts/run_experiment.py --model=4  # GPT-4
    ```

    To get the same queries as in the paper, run the above the commands once. Afterwards open scripts/run_experiment.py and uncomment lines 14-39. Then run again.
