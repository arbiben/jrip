#!/usr/bin/env python

############################################
#               Ben Arbib                  #
#                  P2                      #
#          JRIP34 - cost_table             #
#    object that handles the cost table    #
#               COMS 4119                  #
############################################

import copy

class cost_table:
    def __init__(self, list_of_neighbors, my_ip):
        # initialize the table
        self.table = {}
        self.nodes = {}
        self.neighbors = []
        self.location = 0
        self.me = my_ip

        self.table["SEQ"] = 0  # not sure if neede?
        self.table["ACK"] = 0
        self.table["Data"] = {}
        self.table["Data"]["Type"] = "JRIP"
        self.table["Data"]["RIPTable"] = []


        for n in list_of_neighbors:
            ip, port, cost = n.split(":")
            nid = ip+":"+port

            new_neighbor = {}
            self.neighbors.append(nid)
            self.nodes[nid] = self.location
            self.location = self.location + 1

            new_neighbor["Dest"] = nid
            new_neighbor["Next"] = nid 
            new_neighbor["Cost"] = cost
            self.table["Data"]["RIPTable"].append(copy.deepcopy(new_neighbor))

    def update_table(self, other_table, from_ip):
        cost_list = other_table["Data"]["RIPTable"]
        change = False
        if from_ip in self.nodes:
            for n in cost_list:
                # neig is the info of the neighbor that sent the JRIP table
                neig = self.table["Data"]["RIPTable"][self.nodes[from_ip]]
                if n["Dest"] != self.me:
                    if n["Dest"] in self.nodes:
                        # temp holds my info about the Node we recive info about
                        temp = self.table["Data"]["RIPTable"][self.nodes[n["Dest"]]]
                        if int(n["Cost"]) + int(neig["Cost"]) < int(int(temp["Cost"])):
                            change = True
                            temp["Next"] = neig["Dest"]
                            temp["Cost"] = int(neig["Cost"]) + int(n["Cost"])

                    else:
                        change = True
                        new_node = {}
                        new_node["Dest"] = n["Dest"]
                        new_node["Next"] = neig["Dest"]
                        new_node["Cost"] = int(neig["Cost"]) + int(n["Cost"])
                        
                        self.nodes[n["Dest"]] = self.location
                        self.location = self.location + 1
                        self.table["Data"]["RIPTable"].append(new_node)

            return change

    def get_all_neighbors(self):
        return self.neighbors

    def get_table(self):
        return self.table

