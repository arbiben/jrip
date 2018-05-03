#!/usr/bin/env python

############################################
#               Ben Arbib                  #
#                  P2                      #
#          JRIP34 - cost_table             #
#    object that handles the cost table    #
#               COMS 4119                  #
############################################

import copy, json

class cost_table:
    def __init__(self, list_of_neighbors, my_ip, my_pub_ip):
        # initialize the table
        self.table = {}     # dict of the table itself
        self.nodes = {}     # dict of all nodes and locations
        self.neighbors = [] # list of all neighbors
        self.original_cost = {}
        self.location = 0    
        self.ack_pack = {}
        self.ack_pack["SEQ"] = 0
        self.ack_pack["ACK"] = 1
        self.ack_pack["Data"] = {}
        
        self.me_local = my_ip
        self.me_public = my_pub_ip

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
            self.original_cost[nid] = new_neighbor["Cost"]

    # updates the tables with nodes and costs
    def update_table(self, other_table, from_ip):
        cost_list = other_table["Data"]["RIPTable"]
        change = []
        if from_ip in self.nodes:
            for n in cost_list:
                # neig is the info of the neighbor that sent the JRIP table
                neig = self.table["Data"]["RIPTable"][self.nodes[from_ip]]
                if n["Dest"] != self.me_local and n["Dest"] != self.me_public:
                    if n["Dest"] in self.nodes:
                        # temp holds my info about the Node we recive info about
                        temp = self.table["Data"]["RIPTable"][self.nodes[n["Dest"]]]
                        if int(n["Cost"]) + int(self.original_cost[from_ip]) < int(temp["Cost"]):
                            temp["Next"] = from_ip
                            temp["Cost"] = int(neig["Cost"]) + int(n["Cost"])
                            change.append(neig["Dest"]+" "+str(temp["Cost"]))

                    else:
                        new_node = {}
                        new_node["Dest"] = n["Dest"]
                        new_node["Next"] = neig["Dest"]
                        new_node["Cost"] = int(neig["Cost"]) + int(n["Cost"])
                        
                        self.nodes[n["Dest"]] = self.location
                        self.location = self.location + 1
                        self.table["Data"]["RIPTable"].append(new_node)
                        change.append(new_node["Dest"]+" "+str(new_node["Cost"]))

            return change

    def get_next_hop(self, destination):
        if destination in self.nodes:
            next_hop = self.table["Data"]["RIPTable"][self.nodes[destination]]["Next"]
            return next_hop.split(":")
        
        else:
            return None
    
    def get_ack_pack(self, next_ack):
        self.ack_pack["ACK"] = next_ack
        return self.ack_pack

    def get_all_neighbors(self):
        return self.neighbors

    def get_table(self):
        return self.table

