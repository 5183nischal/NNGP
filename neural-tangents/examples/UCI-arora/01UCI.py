import argparse
import os
import math
import numpy as np
import NTK
import NNGP
import tools

parser = argparse.ArgumentParser()
parser.add_argument('-dir', default = "data", type = str, help = "data directory")
parser.add_argument('-file', default = "resultnngp.log", type = str, help = "Output File")
parser.add_argument('-max_tot', default = 1000, type = int, help = "Maximum number of data samples")
parser.add_argument('-max_dep', default = 5, type = int, help = "Maximum number of depth")


args = parser.parse_args()

MAX_N_TOT = args.max_tot
MAX_DEP = args.max_dep
DEP_LIST = list(range(MAX_DEP))
C_LIST = [10.0 ** i for i in range(-2, 5)]
datadir = args.dir

alg = tools.svm

avg_acc_list_NTK = []
avg_acc_list_NNGP = []
outf = open(args.file, "w")
print ("Dataset\tValidation Acc\tTest Acc", file = outf)
for idx, dataset in enumerate(sorted(os.listdir(datadir))):
    if not os.path.isdir(datadir + "/" + dataset):
        continue
    if not os.path.isfile(datadir + "/" + dataset + "/" + dataset + ".txt"):
        continue
    dic = dict()
    for k, v in map(lambda x : x.split(), open(datadir + "/" + dataset + "/" + dataset + ".txt", "r").readlines()):
        dic[k] = v
    c = int(dic["n_clases="])
    d = int(dic["n_entradas="])
    n_train = int(dic["n_patrons_entrena="])
    n_val = int(dic["n_patrons_valida="])
    n_train_val = int(dic["n_patrons1="])
    n_test = 0
    if "n_patrons2=" in dic:
        n_test = int(dic["n_patrons2="])
    n_tot = n_train_val + n_test
    
    if n_tot > MAX_N_TOT or n_test > 0:
        print (str(dataset) + '\t0\t0', file = outf)
        continue
    
    print (idx, dataset, "\tN:", n_tot, "\td:", d, "\tc:", c)
    
    # load data
    f = open("data/" + dataset + "/" + dic["fich1="], "r").readlines()[1:]
    X = np.asarray(list(map(lambda x: list(map(float, x.split()[1:-1])), f)))
    y = np.asarray(list(map(lambda x: int(x.split()[-1]), f)))
    
    # calculate NTK
    Ks = NTK.kernel_value_batch(X, MAX_DEP)
        
    # load training and validation set
    fold = list(map(lambda x: list(map(int, x.split())), open(datadir + "/" + dataset + "/" + "conxuntos.dat", "r").readlines()))
    train_fold, val_fold = fold[0], fold[1]
    best_acc = 0.0
    best_value = 0
    best_dep = 0
    best_ker = 0
    
    # enumerate kenerls and cost values to find the best hyperparameters
    for dep in DEP_LIST:
        for fix_dep in range(dep + 1):
            K = Ks[dep][fix_dep]
            for value in C_LIST:
                acc = alg(K[train_fold][:, train_fold], K[val_fold][:, train_fold], y[train_fold], y[val_fold], value, c)
                if acc > best_acc:
                    best_acc = acc
                    best_value = value
                    best_dep = dep
                    best_fix = fix_dep

    K = Ks[best_dep][best_fix]    

    print ("best NTK acc:", best_acc)#, "\tC:", best_value, "\tdep:", best_dep, "\tfix:", best_fix)
    avg_acc = 0.0
    fold = list(map(lambda x: list(map(int, x.split())), open("data/" + dataset + "/" + "conxuntos_kfold.dat", "r").readlines()))
    for repeat in range(4):
        train_fold, test_fold = fold[repeat * 2], fold[repeat * 2 + 1]
        acc = alg(K[train_fold][:, train_fold], K[test_fold][:, train_fold], y[train_fold], y[test_fold], best_value, c)
        avg_acc += 0.25 * acc
        
    print ("acc:", avg_acc, "\n")
    print (str(dataset) + '\t' + str(best_acc * 100) + '\t' + str(avg_acc * 100), file = outf)
    avg_acc_list_NTK.append(avg_acc)

    #print(X[train_fold].shape,y[train_fold].shape,X[val_fold].shape,y[val_fold].shape)

    best_acc = 0
    max_l = 0 
    max_w = 0
    best_regul = 0
    b = 0
    for l in range(1,3):
      #print("testing with layers:", l)
      for r in range(1,101):
        for w in range(1,10):
            temp_acc = NNGP.GP(x_train,y[train_fold],x_val,y[val_fold],w*0.1,b,l,r*0.001)
            if temp_acc > best_acc:
                best_acc = temp_acc
                max_l = l
                max_w = w*0.1
                best_regul = r*0.001

    print("best NNGP acc:", best_acc, "with", max_l, "layers, and w_var, b_var, regularizer:", max_w,",", b, ",", best_regul)
    print("#######################################")

    avg_acc = 0.0
    fold = list(map(lambda x: list(map(int, x.split())), open("data/" + dataset + "/" + "conxuntos_kfold.dat", "r").readlines()))
    for repeat in range(4):
        train_fold, test_fold = fold[repeat * 2], fold[repeat * 2 + 1]
        acc = NNGP.GP(X[train_fold],y[train_fold],X[test_fold],y[test_fold],max_w*0.1,b,max_l)
        avg_acc += 0.25 * acc
        
    print ("acc:", avg_acc, "\n")
    print (str(dataset) + '\t' + str(best_acc * 100) + '\t' + str(avg_acc * 100), file = outf)
    avg_acc_list_NNGP.append(avg_acc)
    
outf.close()

    
    