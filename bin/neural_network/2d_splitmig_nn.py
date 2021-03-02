
"""
model params are in log-scale base 10
between models, must change 
    train_params 
    test_params
    func
    ns
    logs
    pnames
"""

# import sys
import time
import dadi
import numpy as np
import random
import util
import matplotlib.pyplot as plt
import pickle

if __name__ == '__main__': 
    # open a text file to record experiment results
    timestr = time.strftime("%Y%m%d-%H%M%S")
    # sys.stdout = open('results/1d-2epoch-'+ timestr +'.txt', 'w')
    # print header to visually seperate each run
    print('*'*70, '\n')
    # print the date and time of run
    print('EXPERIMENT DATE: ', time.asctime(time.localtime(time.time())))
    # print guide key to intepret the numbers for training and testing cases
    print(
    '''
    Keys for Training/Testing #:
    # 1 : no noise
    # 2 : theta = 100
    # 3 : theta = 1,000 
    # 4 : theta = 10,000
    '''
        )
    
    # generate parameter list for testing
    test_params = []
    # range(#) dictate how many values are in each test sets
    while (len(test_params) < 100):
    # generate random nu and T within the same range as training data range
        nu1 = random.random() * 4 - 2 # log
        nu2 = random.random() * 4 - 2 #log
        T = random.random() * 1.9 + 0.1
        m = random.random() * 9 + 1
        params = (round(nu1, 2), round(nu2, 2), round(T, 2), round(m, 2))
        test_params.append(params)
    # print testing set info 
    print('n_samples testing:', len(test_params))
    print('Range of testing params:', min(test_params), 'to', 
            max(test_params))

    # generate a list of theta values to run scaling and add variance
    theta_list = [1, 1000] # 1000, 10000]
    print('Theta list:', theta_list)

    func = dadi.Demographics2D.split_mig
    ns = [20, 20]
    pts_l = [40, 50, 60]
    logs = [True, True, False, False] # nu1 and nu2 are in log-scale
    pnames = ["nu1", "nu2", "T", "m"] # names for plots

    list_train_dict = pickle.load(open('train_set','rb'))
    list_test_dict = util.generating_data_parallel_log(test_params, 
                        theta_list, func, ns, pts_l, logs)

    
    size = len(theta_list)
    
    fig1, axs1 = plt.subplots(size, size, figsize=(4*size, 4*size))
    fig2, axs2 = plt.subplots(size, size, figsize=(4*size, 4*size))
    fig3, axs3 = plt.subplots(size, size, figsize=(4*size, 4*size))
    fig4, axs4 = plt.subplots(size, size, figsize=(4*size, 4*size))
    train_i = 0

    for train_dict in list_train_dict:
        print("Training with theta = ", theta_list[train_i])
        nn = util.nn_train(train_dict)
        # plot the loss curve after training
        fig, ax = plt.subplots()
        ax.plot(nn.loss_curve_)
        fig.savefig(f'../../results/{timestr}_splitmig_nn_{theta_list[train_i]}_loss.png')
        test_i = 0
    
        for test_dict in list_test_dict:
            y_true, y_predict = util.nn_test(nn, test_dict)
            param_true, param_pred = util.sort_by_param(y_true, y_predict)
            r2_by_param = util.nn_r2_score(y_true, y_predict)[1]

      
            log_nu1_true = param_true[0]
            log_nu1_pred =  param_pred[0]
            util.plot_by_param_log(log_nu1_true, log_nu1_pred, True, axs1[train_i, test_i],
                            r2=r2_by_param[0], case=["nu1", theta_list[test_i]])


            log_nu2_true = param_true[1]
            log_nu2_pred =  param_pred[1]
            util.plot_by_param_log(log_nu2_true, log_nu2_pred, True, axs2[train_i, test_i], 
                            r2=r2_by_param[1], case=["nu2", theta_list[test_i]])

          
            util.plot_by_param_log(param_true[2], param_pred[2], False, axs3[train_i, test_i],
                            r2=r2_by_param[2], case=["T", theta_list[test_i]])
            
       
            util.plot_by_param_log(param_true[3], param_pred[3], False, axs4[train_i, test_i], 
                            r2=r2_by_param[3], case=["m", theta_list[test_i]])
            
                
            test_i += 1
            
        train_i += 1
    fig1.tight_layout(rect=[0, 0, 1, 0.95])    
    fig2.tight_layout(rect=[0, 0, 1, 0.95])
    fig3.tight_layout(rect=[0, 0, 1, 0.95]) 
    fig4.tight_layout(rect=[0, 0, 1, 0.95]) 
    fig1.savefig(f'../../results/{timestr}_splitmig_nn_nu1.png')
    fig2.savefig(f'../../results/{timestr}_splitmig_nn_nu2.png')
    fig3.savefig(f'../../results/{timestr}_splitmig_nn_T.png')
    fig4.savefig(f'../../results/{timestr}_splitmig_nn_m.png')

    print("END")



