import json
import numpy as np
import pandas as pd
import networkx as nx
from scipy import sparse
from texttable import Texttable
from sklearn.metrics import roc_auc_score, f1_score
from sklearn.decomposition import TruncatedSVD

def read_graph(args):
    """
    Method to read graph and create a target matrix with pooled adjacency matrix powers up to the order.
    :param args: Arguments object.
    :return edges: Edges dictionary.
    """
    dataset = pd.read_csv(args.edge_path).values.tolist()
    edges = {}
    edges["positive_edges"] = [edge[0:2] for edge in dataset if edge[2] == 1]
    edges["negative_edges"] = [edge[0:2] for edge in dataset if edge[2] == -1]
    edges["ecount"] = len(dataset)
    edges["ncount"] = len(set([edge[0] for edge in dataset]+[edge[1] for edge in dataset]))
    return edges

def tab_printer(args):
    """
    Function to print the logs in a nice tabular format.
    :param args: Parameters used for the model.
    """
    args = vars(args)
    keys = sorted(args.keys())
    t = Texttable() 
    t.add_rows([["Parameter", "Value"]] +  [[k.replace("_"," ").capitalize(),args[k]] for k in keys])
    print(t.draw())

def calculate_auc(targets, predictions, edges):
    """
    """
    neg_ratio = len(edges["negative_edges"])/edges["ecount"]
    targets = [0 if target == 1 else 1 for target in targets]
    auc = roc_auc_score(targets, predictions)
    f1 = f1_score(targets, [1 if p > neg_ratio else 0 for p in  predictions])
    return auc, f1

def score_printer(logs):
    """
    :param logs:

    """
    t = Texttable() 
    t.add_rows([per for i, per in enumerate(logs["performance"]) if i % 10 == 0])
    print(t.draw())

def save_logs(args, logs):
    with open(args.log_path,"w") as f:
            json.dump(logs,f)

def setup_features(args, positive_edges, negative_edges, node_count):
    if args.spectral_features:
        X = create_spectral_features(args, positive_edges, negative_edges, node_count)
    else:
        X = create_general_features(args)
    return X

def create_general_features(args):
    features = np.array(pd.read_csv(args.features_path))
    return features 

def create_spectral_features(args, positive_edges, negative_edges, node_count):
    """

    """
    p_edges = positive_edges + [[edge[1],edge[0]] for edge in positive_edges]
    n_edges = negative_edges + [[edge[1],edge[0]] for edge in negative_edges]
    train_edges = p_edges + n_edges
    index_1 = [edge[0] for edge in train_edges]
    index_2 = [edge[1] for edge in train_edges]
    values = [1]*len(p_edges) + [-1]*len(n_edges)
    shaping = (node_count, node_count)
    signed_A = sparse.csr_matrix(sparse.coo_matrix((values,(index_1,index_2)),shape=shaping,dtype=np.float32))
    svd = TruncatedSVD(n_components=args.reduction_dimensions, n_iter=args.reduction_iterations, random_state=args.seed)
    svd.fit(signed_A)
    return svd.components_.T

    

