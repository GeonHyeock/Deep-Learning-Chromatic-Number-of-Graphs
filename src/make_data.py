import numpy as np
import pandas as pd
import networkx as nx
import random
import argparse
import os, sys, shutil
from itertools import combinations
from collections import defaultdict
from tqdm import tqdm


def random_seed(args):
    random.seed(args.version)
    np.random.seed(args.version)
    os.environ["PYTHONHASHSEED"] = str(args.version)


def create_folder(args):
    if not os.path.exists(args.folder_path):
        os.makedirs(args.folder_path)
    else:
        msg = ""
        while msg not in ["Y", "N"]:
            msg = input(
                f"{args.folder_path}가 존재합니다 \n Y : 기존의 폴더를 삭제 -> 새로 데이터 생성합니다 \n N : 실행 중단 \n"
            )

        if msg == "Y":
            shutil.rmtree(args.folder_path)
            os.makedirs(args.folder_path)
        else:
            sys.exit()


def make_label_graph(args, label, PG, weight_funtion=lambda x: x * (x - 1)):

    if label == "is_PlanarGraph":
        sample_node = []
        while args.min_node > len(sample_node) or len(sample_node) > args.max_node:
            start_node = int(np.random.choice(PG.nodes, 1))
            depth = np.random.choice(range(1, 15), 1)
            sample_node = sum([list(i) for i in nx.dfs_edges(PG, start_node, depth)], [])
        G = PG.subgraph(sample_node)
        G = nx.from_numpy_array(nx.to_numpy_array(G))
        assert nx.is_connected(G), "연결 그래프"
        return G

    elif label == "is_not_PlanarGraph":
        n_range = range(args.min_node, args.max_node + 1)
        is_conected, count = False, 0
        while not is_conected:
            if count // 1000 == 0:
                n = random.choices(n_range, weights=map(weight_funtion, n_range))[0]
                m_range = range(n - 1, (3 * n - 6) + 1)
                m = random.choices(m_range)[0]
            G = nx.gnm_random_graph(n, m)
            is_conected = nx.is_connected(G)
            count += 1

        my_sub = random.choice(["K5", "K3_3", "K5&K3_3"])
        if "K5" in my_sub:
            sample_node = np.random.choice(G.nodes, size=5, replace=False)
            for e in combinations(sample_node, 2):
                G.add_edge(*e)
        if "K3_3" in my_sub:
            sample_node = np.random.choice(G.nodes, size=6, replace=False)
            A, B = np.split(sample_node, 2)
            for a in A:
                for b in B:
                    G.add_edge(a, b)
        return G


def make_graph(args):
    with open(args.PlanarGraph, "r") as f:
        PG = [[int(i) for i in r.rstrip().split()] for r in f][2:]
        PG = np.array(PG)
    PG = nx.from_edgelist(PG)

    df = defaultdict(list)
    for idx in tqdm(range(args.N)):
        label = args.label_name[idx % args.label_size]
        G = make_label_graph(args, label, PG)

        # 그래프 정보 csv 저장
        data_path = os.path.join(args.folder_path, str(idx).zfill(8) + ".adjlist")
        nx.write_adjlist(G, data_path)

        df["data_path"].append(data_path)
        df["label_name"].append(args.labelname2label[label])
        df["node_number"].append(G.number_of_nodes())

    df = pd.DataFrame(df)
    data_type = ["train"] * 8 + ["valid"] * 1 + ["test"] * 1
    data_type = np.random.permutation(np.array(data_type * (len(df) // 10 + 1))[: len(df)])
    df["type"] = data_type
    df.to_csv(os.path.join(args.folder_path, "label.csv"), index=False)


def label_dict(args):
    if args.label_size:
        df = pd.DataFrame({"label_name": args.label_name, "label": list(range(args.label_size))})
        df.to_csv(os.path.join(args.folder_path, "label_dict.csv"), index=False)
        args.labelname2label = {k: v for k, v in zip(df.label_name, df.label)}


def main(args):
    random_seed(args)
    create_folder(args)
    label_dict(args)
    make_graph(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=6, help="data_version")
    parser.add_argument("--min_node", default=10, help="그래프 노드의 최소 개수")
    parser.add_argument("--max_node", default=100, help="그래프 노드의 최대 개수")
    parser.add_argument("--N", default=25000, help="Sample_size")
    parser.add_argument("--label_name", nargs="+", default=["is_not_PlanarGraph", "is_PlanarGraph"], help="데이터 라벨")
    parser.add_argument("--PlanarGraph", default="data/planar_embedding1000000.pg", help="평면그래프")
    args = parser.parse_args()
    args.folder_path = "./data/version_" + str(args.version).zfill(3)
    args.label_size = len(args.label_name)
    main(args)
