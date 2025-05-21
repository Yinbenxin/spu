from hashlib import sha1
import argparse
import random
import string


def gen_fix_data(total=100):
    f = open("psi_100w.csv", 'w+')
    for i in range(total):
        shax = sha1(str(i).encode()).hexdigest()
        f.write(shax + "\n")


def gen_sender_receiver_data(sender_size, receiver_size=100, intersection_size=500000):
    sender_list = []
    for i in range(sender_size):
        shax = sha1(str(i).encode()).hexdigest()
        sender_list.append(shax)
    print('Done creating sender\'s set')
    intersection_set = sender_list[:intersection_size]
    recv_list = []
    recv_list.extend(intersection_set)
    for i in range(receiver_size - intersection_size):
        shax = sha1((str(i) + "_not_match").encode()).hexdigest()
        recv_list.append(shax)
    print('Done creating receiver\'s set')
    return recv_list, sender_list


def gen_sender_receiver_data1(sender_size, receiver_size=100, intersection_size=500000):
    sender_list = []
    for i in range(sender_size):
        shax = sha1(str(i).encode()).hexdigest()
        sender_list.append(shax)
    print('Done creating sender\'s set')
    intersection_set = sender_list[:intersection_size]
    recv_list = []
    recv_list.extend(intersection_set)
    for i in range(receiver_size - intersection_size):
        shax = sha1((str(i) + "_not_match").encode()).hexdigest()
        recv_list.append(shax)
    print('Done creating receiver\'s set')
    return recv_list, sender_list



if __name__ == '__main__':
    recv_list, sender_list = gen_sender_receiver_data(100)
    print(len(set(recv_list)))
    print(len(set(sender_list)))
    intersection_set = set(recv_list).intersection(set(sender_list))
    print(len(intersection_set))

